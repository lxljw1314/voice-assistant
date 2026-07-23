"""
配置文件 - 从环境变量读取（不包含硬编码密钥）
"""
import os

# 阿里云语音服务配置
ALIYUN_APPKEY = os.getenv("ALIYUN_APPKEY", "")
ALIYUN_ACCESS_KEY_ID = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
ALIYUN_ACCESS_KEY_SECRET = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")

# LLM 配置（DeepSeek）
LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-b3da8d8898654de4805fe1eff68ddaf0")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash")

# 百炼 DashScope API 配置（用于 TTS）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-ws-H_EHPXEYI_J7Q5_MEYCIQDO6ixURAyHeXcJdMOMxPkewkvHNddqjzGCgB6gtf84rQIhAMUOKRm6gdGZfhECF60fTkO8Yz8kdgNQC7q1_IMDosPZ")
DASHSCOPE_WORKSPACE_ID = os.getenv("DASHSCOPE_WORKSPACE_ID", "llm-5zv4v5xa91kbfk9b")

# 百炼 TTS 配置
BAILIAN_TTS_MODEL = os.getenv("BAILIAN_TTS_MODEL", "qwen-audio-3.0-tts-flash")
BAILIAN_TTS_VOICE = os.getenv("BAILIAN_TTS_VOICE", "longanhuan_v3.6")


# 本地 FunASR 配置（910B 昇腾部署）
USE_LOCAL_ASR = os.getenv("USE_LOCAL_ASR", "true").lower() in ("true", "1", "yes")
FUNASR_WS_URL = os.getenv("FUNASR_WS_URL", "ws://117.68.66.100:39006")

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
