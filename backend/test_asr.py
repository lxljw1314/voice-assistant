"""
测试阿里云 ASR 服务连接
"""
import asyncio
from asr_service import ASRService

async def test_asr():
    print("🔍 正在测试阿里云 ASR 服务...")
    
    asr = ASRService()
    
    # 测试获取 Token
    print("\n1️⃣  获取 Token...")
    try:
        token = asr._get_token()
        if token:
            print(f"✅ Token 获取成功: {token[:20]}...")
        else:
            print("❌ Token 获取失败")
            return
    except Exception as e:
        print(f"❌ 获取 Token 异常: {e}")
        return
    
    # 测试识别（用空音频测试）
    print("\n2️⃣  测试识别接口...")
    try:
        # 创建一个空的 PCM 音频数据（1秒，16kHz，16bit）
        import struct
        sample_rate = 16000
        duration = 1
        num_samples = sample_rate * duration
        audio_data = struct.pack(f'<{num_samples}h', *([0] * num_samples))
        
        result = await asr.recognize(audio_data)
        print(f"✅ 识别接口调用成功")
        print(f"📝 识别结果: '{result}'")
    except Exception as e:
        print(f"❌ 识别接口异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_asr())
