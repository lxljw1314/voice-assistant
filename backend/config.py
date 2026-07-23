"""
配置文件 - 从环境变量读取（不包含硬编码密钥）
"""
import os

# 阿里云语音服务配置
ALIYUN_APPKEY = os.getenv("ALIYUN_APPKEY", "")
ALIYUN_ACCESS_KEY_ID = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
ALIYUN_ACCESS_KEY_SECRET = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")

# LLM 配置（DeepSeek）
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash")

# 百炼 DashScope API 配置（用于 TTS）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_WORKSPACE_ID = os.getenv("DASHSCOPE_WORKSPACE_ID", "")

# 百炼 TTS 配置
BAILIAN_TTS_MODEL = os.getenv("BAILIAN_TTS_MODEL", "qwen-audio-3.0-tts-flash")
BAILIAN_TTS_VOICE = os.getenv("BAILIAN_TTS_VOICE", "longanhuan_v3.6")

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
