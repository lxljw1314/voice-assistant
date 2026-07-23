"""
百炼 Qwen-ASR Realtime 服务 - OpenAI Realtime 风格 WebSocket 协议
模型: qwen3-asr-flash-realtime
文档: https://help.aliyun.com/zh/model-studio/qwen-asr-realtime-client-events
"""
import websocket
import json
import uuid
import base64
import threading
import time
from config import DASHSCOPE_API_KEY, DASHSCOPE_WORKSPACE_ID


class BailianRealtimeASRService:
    def __init__(self):
        self.api_key = DASHSCOPE_API_KEY
        self.workspace_id = DASHSCOPE_WORKSPACE_ID
        self.model = 'qwen3-asr-flash-realtime'
        self.ws_url = f'wss://{self.workspace_id}.cn-beijing.maas.aliyuncs.com/api-ws/v1/realtime?model={self.model}'
        
        self.ws = None
        self.ws_thread = None
        self.is_running = False
        
        # 识别结果
        self.current_text = ''
        self.final_text = ''
        self.result_callback = None
        
    def start(self, result_callback=None):
        """
        启动实时 ASR
        :param result_callback: 回调函数，接收 (text, is_final) 参数
        """
        if self.is_running:
            print('⚠️ ASR 已在运行中')
            return False
        
        self.result_callback = result_callback
        self.current_text = ''
        self.final_text = ''
        self.is_running = True
        
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                header={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            self.ws_thread = threading.Thread(target=self._run_ws)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            print('✅ 百炼实时 ASR 已启动')
            return True
            
        except Exception as e:
            print(f'❌ 启动百炼实时 ASR 失败: {e}')
            self.is_running = False
            return False
    
    def _run_ws(self):
        """WebSocket 运行循环"""
        self.ws.run_forever()
    
    def _on_open(self, ws):
        """WebSocket 连接建立"""
        print('✅ 百炼 ASR WebSocket 已连接')
        
        # 发送 session.update 配置会话
        session_update = {
            'event_id': str(uuid.uuid4()),
            'type': 'session.update',
            'session': {
                'model': self.model,  # 添加模型参数
                'modalities': ['text', 'audio'],
                'input_audio_format': 'pcm',
                'input_audio_transformation': {
                    'sample_rate': 16000
                },
                'input_audio_transcription': {
                    'language': 'zh',
                    'model': 'qwen3-asr-flash-realtime'
                },
                'turn_detection': {
                    'type': 'server_vad',
                    'threshold': 0.1,
                    'prefix_padding_ms': 200,
                    'silence_duration_ms': 300,
                    'silence_duration_to_trigger_speech_event_if_asr_has_result_ms': 600
                }
            }
        }
        ws.send(json.dumps(session_update))
        print(f'📤 已发送 session.update: {json.dumps(session_update, ensure_ascii=False)[:200]}...')
    
    def _on_message(self, ws, message):
        """处理服务端消息"""
        try:
            data = json.loads(message)
            event_type = data.get('type', '')
            print(f'📨 ASR 服务端消息: {json.dumps(data, ensure_ascii=False)[:300]}')
            
            if event_type == 'session.created':
                print(f'✅ 会话已创建: {data.get("session", {}).get("id", "")}')
            
            elif event_type == 'session.updated':
                print('✅ 会话配置已更新')
            
            elif event_type == 'conversation.item.input_audio_transcription.completed':
                # 最终识别结果
                transcript = data.get('transcript', '')
                self.final_text = transcript
                print(f'✅ 最终识别: {transcript}')
                if self.result_callback:
                    self.result_callback(transcript, True)
            
            elif event_type == 'conversation.item.input_audio_transcription.delta':
                # 中间识别结果（流式增量）
                delta = data.get('delta', '')
                self.current_text = delta
                if self.result_callback:
                    self.result_callback(delta, False)
            
            elif event_type == 'conversation.item.input_audio_transcription.text':
                # 中间识别结果（另一种格式）
                text = data.get('text', '')
                stash = data.get('stash', '')
                self.current_text = text + stash
                if self.result_callback:
                    self.result_callback(text + stash, False)
            
            elif event_type == 'input_audio_buffer.speech_started':
                print('🎤 检测到语音开始')
            
            elif event_type == 'input_audio_buffer.speech_stopped':
                print('🔇 检测到语音结束')
            
            elif event_type == 'session.finished':
                print('✅ 会话已结束')
                self.is_running = False
                ws.close()
            
            elif event_type == 'error':
                error_msg = data.get('error', {}).get('message', 'Unknown error')
                print(f'❌ 错误: {error_msg}')
                self.is_running = False
            
        except Exception as e:
            print(f'❌ 处理消息失败: {e}')
    
    def _on_error(self, ws, error):
        """WebSocket 错误"""
        print(f'❌ WebSocket 错误: {error}')
        self.is_running = False
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket 关闭"""
        print(f'🔒 WebSocket 关闭: {close_status_code} - {close_msg}')
        self.is_running = False
    
    def send_audio(self, audio_data):
        """
        发送音频数据
        :param audio_data: PCM 16-bit 音频数据 (bytes)
        """
        if not self.is_running or not self.ws:
            return
        
        # Base64 编码
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        # 发送 input_audio_buffer.append
        message = {
            'event_id': str(uuid.uuid4()),
            'type': 'input_audio_buffer.append',
            'audio': audio_b64
        }
        
        try:
            self.ws.send(json.dumps(message))
        except Exception as e:
            print(f'❌ 发送音频失败: {e}')
    
    def stop(self):
        """停止实时 ASR"""
        if not self.is_running:
            return self.final_text
        
        print('⏹️ 停止百炼实时 ASR...')
        
        # 发送 session.finish
        if self.ws:
            try:
                finish_msg = {
                    'event_id': str(uuid.uuid4()),
                    'type': 'session.finish'
                }
                self.ws.send(json.dumps(finish_msg))
                print('📤 已发送 session.finish')
                
                # 等待一小段时间让服务端处理
                time.sleep(0.5)
            except Exception as e:
                print(f'⚠️ 发送 finish 失败: {e}')
        
        self.is_running = False
        
        if self.ws:
            self.ws.close()
        
        return self.final_text
    
    def get_result(self):
        """获取当前识别结果"""
        return self.current_text or self.final_text


if __name__ == '__main__':
    # 测试
    def callback(text, is_final):
        print(f'📝 [{("最终" if is_final else "中间")}] {text}')
    
    asr = BailianRealtimeASRService()
    if asr.start(callback):
        print('按 Ctrl+C 停止...')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            final = asr.stop()
            print(f'\n最终结果: {final}')
