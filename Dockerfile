FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码到根目录（让模块导入正常工作）
COPY backend/ .

# 暴露端口
EXPOSE $PORT

# 启动命令
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
