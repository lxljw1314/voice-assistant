"""启动脚本 - 从项目根目录运行"""
import sys
import os

# 将 backend 目录加入 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.main import app

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
