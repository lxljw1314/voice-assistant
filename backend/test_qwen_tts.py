#!/usr/bin/env python3
"""
测试 qwen3-tts 语音合成
"""
import asyncio
from qwen_tts_service import QwenTTSService

async def test_tts():
    print("🎤 测试 qwen3-tts 语音合成...")
    
    tts = QwenTTSService()
    
    # 测试文本
    text = "你好呀！我是你的语音助手，有什么可以帮你的吗？"
    
    print(f"📝 合成文本: {text}")
    print("🎵 开始合成...")
    
    # 调用合成
    audio_data = await tts.synthesize(text, voice="Cherry")
    
    if audio_data:
        print(f"✅ 合成成功！音频大小: {len(audio_data)} bytes")
        
        # 保存音频文件
        output_file = "/tmp/test_qwen_tts.wav"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        
        print(f"💾 音频已保存到: {output_file}")
        print(f"▶️  可以用以下命令播放:")
        print(f"   afplay {output_file}")
    else:
        print("❌ 合成失败")

if __name__ == "__main__":
    asyncio.run(test_tts())
