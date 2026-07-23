"""
百炼 TTS 服务 - WebSocket 协议
支持模型: qwen-audio-3.0-tts-flash, cosyvoice-v1 等
"""
import websocket
import json
import uuid
import time
import os
import threading
from config import DASHSCOPE_API_KEY, DASHSCOPE_WORKSPACE_ID, BAILIAN_TTS_MODEL, BAILIAN_TTS_VOICE


class QwenTTSService:
    def __init__(self, model=None, voice=None):
        self.model = model or BAILIAN_TTS_MODEL
        self.voice = voice or BAILIAN_TTS_VOICE
        self.workspace_id = DASHSCOPE_WORKSPACE_ID
        self.api_key = DASHSCOPE_API_KEY
        self.ws_url = f'wss://{self.workspace_id}.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference'
    
    def synthesize(self, text, output_path=None):
        """
        合成语音并保存到文件
        :param text: 待合成文本
        :param output_path: 输出文件路径，默认自动生成
        :return: 输出文件路径
        """
        if not output_path:
            output_path = f'/tmp/tts_{uuid.uuid4().hex[:8]}.mp3'
        
        if os.path.exists(output_path):
            os.remove(output_path)
        
        task_id = str(uuid.uuid4())
        audio_data = []
        result = {'status': 'unknown', 'error': None}
        
        def on_message(ws, message):
            if isinstance(message, bytes):
                audio_data.append(message)
            else:
                data = json.loads(message)
                event = data.get('header', {}).get('event', '')
                
                if event == 'task-started':
                    # 发送文本
                    ws.send(json.dumps({
                        'header': {'action': 'continue-task', 'task_id': task_id, 'streaming': 'duplex'},
                        'payload': {'input': {'text': text}}
                    }))
                    time.sleep(0.3)
                    # 发送结束
                    ws.send(json.dumps({
                        'header': {'action': 'finish-task', 'task_id': task_id, 'streaming': 'duplex'},
                        'payload': {'input': {}}
                    }))
                elif event == 'task-finished':
                    result['status'] = 'done'
                    ws.close()
                elif event == 'task-failed':
                    result['status'] = 'failed'
                    result['error'] = data.get('header', {}).get('error_message', 'Unknown error')
                    ws.close()
        
        def on_open(ws):
            ws.send(json.dumps({
                'header': {'action': 'run-task', 'task_id': task_id, 'streaming': 'duplex'},
                'payload': {
                    'task_group': 'audio',
                    'task': 'tts',
                    'function': 'SpeechSynthesizer',
                    'model': self.model,
                    'parameters': {
                        'text_type': 'PlainText',
                        'voice': self.voice,
                        'format': 'mp3',
                        'sample_rate': 22050
                    },
                    'input': {}
                }
            }))
        
        def on_error(ws, error):
            result['status'] = 'error'
            result['error'] = str(error)
        
        ws = websocket.WebSocketApp(
            self.ws_url,
            header={'Authorization': f'Bearer {self.api_key}'},
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=lambda ws, *a: None
        )
        
        # 设置超时
        timer = threading.Timer(30, lambda: ws.close())
        timer.start()
        ws.run_forever()
        timer.cancel()
        
        if result['status'] == 'done' and audio_data:
            with open(output_path, 'wb') as f:
                for chunk in audio_data:
                    f.write(chunk)
            return output_path
        else:
            error_msg = result.get('error', 'Unknown error')
            raise Exception(f'TTS 合成失败: {error_msg}')
    
    def list_voices(self):
        """返回常用音色列表"""
        return {
            'longanhuan_v3.6': '龙安欢 (默认)',
            'longxiaochun': '龙小淳 (女声)',
            'longxiaoxia': '龙小夏 (女声)',
            'longxiaochen': '龙小晨 (男声)',
        }


if __name__ == '__main__':
    # 测试
    tts = QwenTTSService()
    print('正在合成语音...')
    output = tts.synthesize('你好，我是语音助手，有什么可以帮你的吗？')
    print(f'✅ 已保存到: {output}')
