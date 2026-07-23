"""
阿里云实时语音识别服务（流式 WebSocket）
"""
import json
import uuid
import websocket
import threading
from config import ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, ALIYUN_APPKEY
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest


class RealtimeASRService:
    def __init__(self):
        self.appkey = ALIYUN_APPKEY
        self.access_key_id = ALIYUN_ACCESS_KEY_ID
        self.access_key_secret = ALIYUN_ACCESS_KEY_SECRET
        self.token = None
        self.ws = None
        self.task_id = str(uuid.uuid4()).replace('-', '')
        self.result_text = ""  # 最终结果
        self.current_text = ""  # 当前中间结果
        self.is_started = False
        self.is_finished = False
        
    def _get_token(self):
        """获取阿里云 Token"""
        try:
            client = AcsClient(self.access_key_id, self.access_key_secret, "cn-shanghai")
            request = CommonRequest()
            request.set_method('POST')
            request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
            request.set_version('2019-02-28')
            request.set_action_name('CreateToken')
            
            response = client.do_action_with_exception(request)
            result = json.loads(response)
            
            if 'Token' in result and 'Id' in result['Token']:
                self.token = result['Token']['Id']
                print(f"✅ 实时 ASR Token 获取成功")
                return self.token
            else:
                print(f"❌ 实时 ASR Token 获取失败: {result}")
                return ""
        except Exception as e:
            print(f"❌ 获取 Token 异常: {e}")
            return ""
    
    def _on_message(self, ws, message):
        """接收阿里云返回的消息"""
        try:
            msg = json.loads(message)
            header = msg.get('header', {})
            name = header.get('name', '')
            
            if name == 'TranscriptionStarted':
                print("✅ 实时 ASR 已启动")
                self.is_started = True
            elif name == 'TranscriptionResultChanged':
                # 中间结果（临时）
                payload = msg.get('payload', {})
                result = payload.get('result', '')
                self.current_text = result
                print(f"🔄 中间结果: {result}")
            elif name == 'SentenceEnd':
                # 一句话结束（最终结果）
                payload = msg.get('payload', {})
                result = payload.get('result', '')
                self.result_text += result
                self.current_text = self.result_text  # 中间结果也更新为最终
                print(f"✅ 一句话结束: {result}")
            elif name == 'TranscriptionCompleted':
                print("✅ 实时 ASR 完成")
                self.is_finished = True
            elif name == 'TaskFailed':
                status = header.get('status', 0)
                status_text = header.get('status_text', '')
                print(f"❌ ASR 任务失败: {status} - {status_text}")
                self.is_finished = True
                
        except Exception as e:
            print(f"❌ 解析消息错误: {e}")
    
    def _on_error(self, ws, error):
        print(f"❌ WebSocket 错误: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        print(f"🔒 WebSocket 关闭: {close_status_code} - {close_msg}")
    
    def _on_open(self, ws):
        print("✅ WebSocket 连接已建立")
        
        # 发送 StartTranscription 指令
        start_msg = {
            "header": {
                "message_id": str(uuid.uuid4()).replace('-', ''),
                "task_id": self.task_id,
                "namespace": "SpeechTranscriber",
                "name": "StartTranscription",
                "appkey": self.appkey
            },
            "payload": {
                "format": "pcm",
                "sample_rate": 16000,
                "enable_intermediate_result": True,
                "enable_punctuation_prediction": True,
                "enable_inverse_text_normalization": True
            }
        }
        
        ws.send(json.dumps(start_msg))
        print("📤 已发送 StartTranscription 指令")
    
    def start(self):
        """启动实时识别"""
        if not self.token:
            self.token = self._get_token()
            if not self.token:
                return False
        
        url = f"wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1?token={self.token}"
        
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        # 在后台线程运行 WebSocket
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        return True
    
    def send_audio(self, audio_data: bytes):
        """发送音频数据"""
        if self.ws and self.is_started and not self.is_finished:
            self.ws.send(audio_data, opcode=websocket.ABNF.OPCODE_BINARY)
    
    def stop(self):
        """停止识别"""
        if self.ws and self.is_started and not self.is_finished:
            # 发送 StopTranscription 指令
            stop_msg = {
                "header": {
                    "message_id": str(uuid.uuid4()).replace('-', ''),
                    "task_id": self.task_id,
                    "namespace": "SpeechTranscriber",
                    "name": "StopTranscription",
                    "appkey": self.appkey
                }
            }
            
            self.ws.send(json.dumps(stop_msg))
            print("📤 已发送 StopTranscription 指令")
            
            # 等待完成
            import time
            for _ in range(50):  # 最多等 5 秒
                if self.is_finished:
                    break
                time.sleep(0.1)
            
            # 关闭 WebSocket
            if self.ws:
                self.ws.close()
        
        return self.result_text
    
    def get_result(self):
        """获取当前识别结果（优先返回中间结果，实现实时显示）"""
        if self.current_text:
            return self.current_text
        return self.result_text
