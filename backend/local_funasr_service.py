"""
本地 FunASR 实时语音识别服务（910B 昇腾部署）
协议：客户端发送 WAV 二进制块，服务端返回 JSON {"text": "..."}
模型：SenseVoiceSmall (iic/SenseVoiceSmall)
"""
import websocket
import json
import struct
import threading
import time
import re
from config import FUNASR_WS_URL


# FunASR 返回的文本中可能包含事件/情绪标签，需要剥离
_TAG_PATTERN = re.compile(r'<\|[^|]*\|>')


def _strip_tags(text: str) -> str:
    """去除 SenseVoice 返回的 <|zh|><|NEUTRAL|> 等标签"""
    return _TAG_PATTERN.sub('', text).strip()


def _build_wav_header(pcm_data: bytes, sample_rate: int = 16000,
                      channels: int = 1, bits_per_sample: int = 16) -> bytes:
    """为 PCM 数据构建 44 字节 WAV 头"""
    data_size = len(pcm_data)
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8

    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + data_size,       # ChunkSize
        b'WAVE',
        b'fmt ',
        16,                   # Subchunk1Size (PCM)
        1,                    # AudioFormat (1 = PCM)
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b'data',
        data_size
    )
    return header + pcm_data


class LocalFunASRService:
    """
    本地 FunASR WebSocket 适配器
    910B 服务端 VAD 可能返回短片段，需要累积成完整句子
    """

    # 每累积约 1 秒音频就发送一次（16kHz * 2bytes * 1s = 32000）
    CHUNK_THRESHOLD = 32000
    
    # 句子结束标点
    SENTENCE_END_PUNCTS = '。！？!?.，,;；:：'
    
    # 累积超时（秒）：超过这个时间没有新结果，认为说话结束
    ACCUMULATE_TIMEOUT = 1.5
    
    # 短片段阈值：小于这个长度的片段需要累积
    SHORT_FRAGMENT_THRESHOLD = 5

    def __init__(self):
        self.ws_url = FUNASR_WS_URL
        self.ws = None
        self.ws_thread = None
        self.is_running = False

        self.result_callback = None
        self.final_text = ''
        self.current_text = ''
        self._connected = False

        # PCM 缓冲区
        self._pcm_buffer = bytearray()
        self._lock = threading.Lock()
        
        # 结果累积缓冲区
        self._accumulate_buffer = ''
        self._accumulate_timer = None

    # ---- 公共接口 ----

    def start(self, result_callback=None):
        """启动实时 ASR"""
        if self.is_running:
            print('⚠️ 本地 FunASR 已在运行中')
            return False

        self.result_callback = result_callback
        self.current_text = ''
        self.final_text = ''
        self._pcm_buffer = bytearray()
        self._accumulate_buffer = ''
        self._accumulate_timer = None
        self.is_running = True

        print('🚀 正在启动本地 FunASR...')
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open,
            )
            print('📦 WebSocketApp 创建成功')
            self.ws_thread = threading.Thread(target=self._run_ws, daemon=True)
            self.ws_thread.start()
            print('🧵 线程已启动')
            time.sleep(0.5)
            if not self._connected:
                print('⚠️ 等待连接...')
            print(f'✅ 本地 FunASR 已启动 ({self.ws_url})')
            return True
        except Exception as e:
            print(f'❌ 启动本地 FunASR 失败: {e}')
            self.is_running = False
            return False

    def send_audio(self, audio_data: bytes):
        """
        接收前端发来的 PCM 16-bit 数据，缓冲后打包成 WAV 发送
        """
        if not self.is_running or not self.ws:
            return

        pcm_chunk = None
        with self._lock:
            self._pcm_buffer.extend(audio_data)

            if len(self._pcm_buffer) >= self.CHUNK_THRESHOLD:
                pcm_chunk = bytes(self._pcm_buffer)
                self._pcm_buffer = bytearray()

        # 在锁外发送，避免阻塞
        if pcm_chunk:
            wav_data = _build_wav_header(pcm_chunk)
            try:
                self.ws.send(wav_data, opcode=websocket.ABNF.OPCODE_BINARY)
            except Exception as e:
                print(f'❌ 发送音频到 FunASR 失败: {e}')

    def stop(self):
        """停止实时 ASR"""
        if not self.is_running:
            return self.final_text

        print('⏹️ 停止本地 FunASR...')

        # 取消累积定时器
        if self._accumulate_timer:
            self._accumulate_timer.cancel()
            self._accumulate_timer = None

        # 清空缓冲区
        with self._lock:
            self._pcm_buffer = bytearray()

        self.is_running = False
        if self.ws:
            self.ws.close()

        return self.final_text

    def get_result(self):
        return self.current_text or self.final_text

    # ---- 内部方法 ----

    def _run_ws(self):
        print(' 运行 WebSocket 事件循环...')
        try:
            self.ws.run_forever(ping_interval=10, ping_timeout=5)
        except Exception as e:
            print(f'❌ WebSocket 事件循环异常: {e}')
            import traceback
            traceback.print_exc()

    def _on_open(self, ws):
        self._connected = True
        print(f'✅ FunASR WebSocket 已连接: {self.ws_url}')

    def _on_message(self, ws, message):
        """
        910B 服务端可能返回短片段，需要累积成完整句子
        """
        try:
            data = json.loads(message)
            raw_text = data.get('text', '')
            clean_text = _strip_tags(raw_text)

            if clean_text:
                print(f'📝 FunASR 识别：{clean_text}', flush=True)
                
                # 累积到缓冲区
                self._accumulate_buffer += clean_text
                self.current_text = self._accumulate_buffer
                
                # 检查是否有句子结束标点
                has_end_punct = any(p in clean_text for p in self.SENTENCE_END_PUNCTS)
                
                # 检查是否是长片段（可能是完整句子）
                is_long_fragment = len(clean_text) >= self.SHORT_FRAGMENT_THRESHOLD
                
                if has_end_punct or is_long_fragment:
                    # 有结束标点或长片段，立即触发
                    self._flush_accumulated()
                else:
                    # 短片段，启动/重置累积定时器
                    self._reset_accumulate_timer()
        except Exception as e:
            print(f'❌ 解析 FunASR 响应失败：{e}', flush=True)

    def _flush_accumulated(self):
        """触发累积的文本"""
        if self._accumulate_timer:
            self._accumulate_timer.cancel()
            self._accumulate_timer = None
        
        if self._accumulate_buffer and self.result_callback:
            print(f'✅ 触发累积结果：{self._accumulate_buffer}', flush=True)
            self.final_text = self._accumulate_buffer
            self.result_callback(self._accumulate_buffer, True)
            self._accumulate_buffer = ''

    def _reset_accumulate_timer(self):
        """重置累积定时器"""
        if self._accumulate_timer:
            self._accumulate_timer.cancel()
        self._accumulate_timer = threading.Timer(
            self.ACCUMULATE_TIMEOUT, 
            self._on_accumulate_timeout
        )
        self._accumulate_timer.daemon = True
        self._accumulate_timer.start()

    def _on_accumulate_timeout(self):
        """累积超时回调"""
        print(f' 累积超时，触发：{self._accumulate_buffer}', flush=True)
        self._flush_accumulated()

    def _on_error(self, ws, error):
        print(f'❌ FunASR WebSocket 错误：{error}')
        self.is_running = False

    def _on_close(self, ws, close_status_code, close_msg):
        print(f'🔒 FunASR WebSocket 关闭：{close_status_code} - {close_msg}')
        self.is_running = False


if __name__ == '__main__':
    def callback(text, is_final):
        print(f'📝 [{("最终" if is_final else "中间")}] {text}')

    asr = LocalFunASRService()
    if asr.start(callback):
        print('按 Ctrl+C 停止...')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            final = asr.stop()
            print(f'\n最终结果：{final}')
