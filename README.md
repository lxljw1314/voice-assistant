# 语音全链路产品 - 最小可用版本

## 📦 功能
- 实时语音识别（阿里云 ASR）
- 智能对话（DeepSeek/Qwen）
- 语音合成（阿里云 TTS）
- Web 界面交互

## 🚀 快速开始

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置阿里云服务
1. 登录阿里云控制台
2. 开通「智能语音交互」服务
3. 创建项目，获取 AppKey
4. 获取 AccessKey ID 和 Secret

编辑 `backend/config.py`：
```python
ALIYUN_APPKEY = "你的AppKey"
ALIYUN_ACCESS_KEY_ID = "你的AccessKeyID"
ALIYUN_ACCESS_KEY_SECRET = "你的AccessKeySecret"
```

### 3. 配置 LLM
编辑 `backend/config.py`：
```python
LLM_API_KEY = "你的DeepSeek API Key"
LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL = "deepseek-chat"
```

### 4. 启动服务
```bash
# 启动后端
cd backend
python main.py

# 后端运行在 http://localhost:8000
```

### 5. 打开前端
直接用浏览器打开 `frontend/index.html`

## 📋 使用说明
1. 点击「开始录音」按钮
2. 说话后点击「停止录音」
3. 等待 AI 回复（会显示文字 + 播放语音）

## 💰 成本
- ASR：¥3.5/小时
- TTS：¥0.01/千字符
- LLM：按 token 计费

## 🔧 技术栈
- 后端：Python + FastAPI
- ASR：阿里云实时语音识别
- TTS：阿里云语音合成
- LLM：DeepSeek / Qwen
- 前端：原生 HTML + JavaScript
