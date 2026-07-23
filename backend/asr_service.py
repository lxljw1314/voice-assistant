"""
阿里云语音识别服务（一句话识别）
"""
import json
import uuid
import requests
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from config import ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, ALIYUN_APPKEY


class ASRService:
    def __init__(self):
        self.appkey = ALIYUN_APPKEY
        self.access_key_id = ALIYUN_ACCESS_KEY_ID
        self.access_key_secret = ALIYUN_ACCESS_KEY_SECRET
        self.token = None
        
        # 初始化 AcsClient
        self.acs_client = AcsClient(
            self.access_key_id,
            self.access_key_secret,
            "cn-shanghai"
        )
        
    def _get_token(self):
        """获取阿里云 Token（有效期 24 小时）"""
        try:
            # 创建 CommonRequest
            request = CommonRequest()
            request.set_method('POST')
            request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
            request.set_version('2019-02-28')
            request.set_action_name('CreateToken')
            
            # 发送请求
            response = self.acs_client.do_action_with_exception(request)
            result = json.loads(response)
            
            print(f"Token 响应: {result}")
            
            if 'Token' in result and 'Id' in result['Token']:
                self.token = result['Token']['Id']
                print(f"✅ Token 获取成功: {self.token[:20]}...")
                return self.token
            else:
                print(f"❌ Token 获取失败: {result}")
                return ""
                
        except Exception as e:
            print(f"❌ 获取 Token 异常: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    async def recognize(self, audio_data: bytes, format: str = "wav", sample_rate: int = 16000) -> str:
        """
        一句话识别
        :param audio_data: 音频数据（bytes）
        :param format: 音频格式（wav/pcm/opu）
        :param sample_rate: 采样率（16000/8000）
        :return: 识别的文本
        """
        try:
            # 确保有 token
            if not self.token:
                self.token = self._get_token()
                if not self.token:
                    print("❌ 无法获取 Token，识别失败")
                    return ""
            
            # 一句话识别 API
            url = "https://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/asr"
            params = {
                "appkey": self.appkey,
                "format": format,
                "sample_rate": sample_rate,
                "enable_punctuation_prediction": "true",
                "enable_inverse_text_normalization": "true"
            }
            headers = {
                "X-NLS-Token": self.token,
                "Content-Type": "application/octet-stream"
            }
            
            print(f"📤 发送 ASR 请求，音频大小: {len(audio_data)} bytes")
            response = requests.post(url, params=params, headers=headers, data=audio_data)
            
            print(f"📥 ASR 响应状态码: {response.status_code}")
            print(f"📥 ASR 响应头: {dict(response.headers)}")
            
            # 检查响应内容类型
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                result = response.json()
                print(f"📥 ASR 响应 JSON: {result}")
                
                if result.get("status") == 20000000:
                    text = result.get("result", "")
                    print(f"✅ 识别成功: {text}")
                    return text
                else:
                    print(f"❌ ASR 识别失败: {result}")
                    return ""
            else:
                # 可能是音频数据或其他格式
                print(f"❌ 意外的响应类型: {content_type}")
                print(f"响应内容前 200 字符: {response.text[:200]}")
                return ""
                
        except Exception as e:
            print(f"❌ ASR 识别错误: {e}")
            import traceback
            traceback.print_exc()
            return ""
