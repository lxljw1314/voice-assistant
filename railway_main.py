"""
 Railway 部署入口文件
 将 backend 目录添加到 Python 路径，然后启动 FastAPI 应用
"""
import sys
import os

# 将 backend 目录添加到 Python 路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# 导入并运行 FastAPI 应用
from main import app
import uvicorn

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)
