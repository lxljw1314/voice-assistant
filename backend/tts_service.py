"""
Edge TTS 语音合成服务（微软免费，音色好）
"""
import edge_tts
import asyncio


class TTSService:
    def __init__(self):
        # 默认音色：活泼女声
        self.default_voice = "zh-CN-XiaoxiaoNeural"
        # 语速 +30%（比默认快）
        self.default_rate = "+30%"
        
        # 可用音色列表
        self.voices = {
            "xiaoxiao": "zh-CN-XiaoxiaoNeural",  # 活泼女声（默认）
            "xiaoyi": "zh-CN-XiaoyiNeural",      # 甜美女声
            "yunxi": "zh-CN-YunxiNeural",         # 阳光男声
            "yunyang": "zh-CN-YunyangNeural",     # 新闻男声
            "xiaohan": "zh-CN-XiaohanNeural",     # 温柔女声
        }
    
    async def synthesize(self, text: str, voice: str = "xiaoxiao", rate: str = "+30%") -> bytes:
        """
        语音合成
        :param text: 要合成的文本
        :param voice: 音色名称（xiaoxiao/xiaoyi/yunxi/yunyang/xiaohan）
        :param rate: 语速（+30% 表示比默认快 30%）
        :return: 音频数据（bytes）
        """
        try:
            voice_name = self.voices.get(voice, self.default_voice)
            
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_name,
                rate=rate,
                pitch="+0Hz"
            )
            
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            print(f"✅ Edge TTS 合成成功，音色: {voice_name}, 语速: {rate}, 大小: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            print(f"❌ Edge TTS 合成错误: {e}")
            import traceback
            traceback.print_exc()
            return b""
