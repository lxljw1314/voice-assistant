# 部署指南

## 📦 项目结构

```
voice-assistant/
├── backend/          # Python FastAPI 后端
├── frontend/         # 静态前端页面
├── Procfile          # Railway 启动配置
├── runtime.txt       # Python 版本
└── .env.example      # 环境变量示例
```

## 🚀 部署步骤

### 第一步：部署后端到 Railway

1. **登录 Railway**
   - 访问 https://railway.app/
   - 使用 GitHub 登录

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的 `voice-assistant` 仓库

3. **配置环境变量**
   在 Railway 项目设置中，添加以下环境变量：
   ```
   ALIYUN_APPKEY=你的AppKey
   ALIYUN_ACCESS_KEY_ID=你的AccessKeyID
   ALIYUN_ACCESS_KEY_SECRET=你的AccessKeySecret
   LLM_API_KEY=你的DeepSeek API Key
   DASHSCOPE_API_KEY=你的DashScope API Key
   DASHSCOPE_WORKSPACE_ID=你的Workspace ID
   ```

4. **获取后端地址**
   - 部署完成后，在 Settings -> Domains 中获取后端 URL
   - 格式类似：`https://your-app-name.up.railway.app`

5. **测试后端**
   访问 `https://your-backend.up.railway.app/` 应该能看到前端页面（但目前先不管）

### 第二步：部署前端到 Cloudflare Pages

1. **登录 Cloudflare**
   - 访问 https://dash.cloudflare.com/
   - 登录或注册账号

2. **创建 Pages 项目**
   - 进入 "Workers & Pages"
   - 点击 "Create application"
   - 选择 "Pages" -> "Connect to Git"

3. **配置部署**
   - 选择你的 GitHub 仓库
   - 配置构建设置：
     - **Build command**: 留空（不需要构建）
     - **Build output directory**: `frontend`

4. **修改前端配置**
   
   在部署前，编辑 `frontend/config.js`：
   ```javascript
   window.API_BASE = 'https://your-backend.up.railway.app';
   window.WS_BASE = 'wss://your-backend.up.railway.app';
   ```
   
   将 `your-backend.up.railway.app` 替换为你的 Railway 后端地址

5. **部署**
   - 点击 "Save and Deploy"
   - 等待部署完成

6. **获取前端地址**
   - 部署完成后，会分配一个域名
   - 格式类似：`https://your-project.pages.dev`

### 第三步：验证部署

1. 访问 Cloudflare Pages 分配的前端地址
2. 测试语音功能是否正常
3. 打开浏览器开发者工具，检查是否有错误

## 🔧 常见问题

### WebSocket 连接失败
- 检查 `frontend/config.js` 中的 `WS_BASE` 是否正确
- 确保使用 `wss://` 而不是 `ws://`（HTTPS 需要 WSS）

### API 调用失败
- 检查 `frontend/config.js` 中的 `API_BASE` 是否正确
- 检查 Railway 后端的环境变量是否配置正确
- 查看 Railway 日志排查错误

### CORS 错误
- 后端已经配置了 CORS 允许所有来源
- 如果需要限制，修改 `backend/main.py` 中的 `allow_origins`

## 📝 更新代码

当代码更新后：
- **后端**：Railway 会自动检测 GitHub 更新并重新部署
- **前端**：Cloudflare Pages 也会自动检测并重新部署

## 💰 成本说明

- **Railway**: 免费套餐每月 $5 额度，小型应用通常够用
- **Cloudflare Pages**: 完全免费（有请求限制）
- **阿里云 ASR**: ¥3.5/小时
- **阿里云 TTS**: ¥0.01/千字符
- **DeepSeek**: 按 token 计费

## 🔒 安全建议

1. 不要将 API 密钥提交到 Git
2. 使用 Railway 的环境变量管理密钥
3. 定期检查和轮换密钥
4. 考虑在 Railway 中启用访问日志监控
