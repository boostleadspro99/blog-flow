# Gemini-Free-API

基于 Google Gemini Web API 的异步 Python 封装库，提供 OpenAI 兼容的 API 服务。

> 💡 **免费使用 Gemini 3.0 Pro Thinking**  
> 无需付费订阅，只需 Google 账号即可免费使用最新的 Gemini 3.0 Pro Thinking 模型，支持深度思考、图片生成等高级功能。Pro账号每日使用额度更高。

中文文档 | [English](README_EN.md)

## 特性

- ⭐ **免费使用 Gemini 3.0 pro Thinking** - 无需付费，支持深度思考和图片生成
- ✅ **OpenAI 兼容** - 完全兼容 OpenAI SDK，可作为替代品使用
- ✅ **同步网页对话** - 与 Gemini 网页版共享对话历史，记录不丢失
- ✅ **自动去水印** - 图片生成自动去除 Gemini 水印（反向 Alpha 混合算法）
- ✅ **多模态支持** - 文本、图片上传、图片生成
- ✅ **Cookie 自动刷新** - 浏览器扩展自动更新 Cookie，无需手动维护
- ✅ **会话管理** - 智能会话缓存，支持多轮对话
- ✅ **异步设计** - 基于 asyncio 高效处理并发请求

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv（推荐）
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### 2. 获取 Gemini Cookies

- 访问 https://gemini.google.com 并登录
- 按 F12 打开开发者工具 → Application → Cookies
- 复制 `__Secure-1PSID` 和 `__Secure-1PSIDTS`

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入上面复制的 cookies
```

### 4. 启动服务

```bash
python openai_server.py
# 或使用启动脚本
start.bat
```

服务地址：`http://localhost:3897`  
API 文档：`http://localhost:3897/docs`

## 使用示例

### 基础对话

```python
from openai import OpenAI

client = OpenAI(
    api_key="dummy",
    base_url="http://localhost:3897/v1"
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### 图片上传

```python
# 支持 URL、base64、本地文件
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "这张图片里有什么？"},
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
    }]
)
```

### 图片生成（自动去水印）

```python
response = client.images.generate(
    model="gemini-3-pro-image",  # 模型名包含 'image' 则自动去水印
    prompt="A beautiful sunset over mountains",
    n=1,
    size="1024x1024"
)
print(response.data[0].url)
```

### 流式响应

```python
stream = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "讲个故事"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## API 端点

| 端点 | 说明 |
|------|------|
| `GET /v1/models` | 列出可用模型 |
| `POST /v1/chat/completions` | 聊天补全（支持流式、图片上传） |
| `POST /v1/images/generations` | 图片生成（自动去水印） |
| `GET /v1/images/proxy` | 图片代理（支持 `?remove_watermark=true/false`） |

## 模型映射

| OpenAI 模型 | Gemini 模型 |
|------------|-------------|
| gpt-3.5-turbo | gemini-2.5-flash |
| gpt-4 | gemini-2.5-pro |
| gpt-4-turbo | gemini-2.5-pro |
| gemini-3-pro-image（原图自动去水印） | gemini-3.0-pro （缩略图带水印）|

## Cookie 自动刷新

### 使用浏览器扩展（推荐）

1. 加载扩展：`cookie_service/extension/`
2. 访问 https://gemini.google.com 并登录
3. 扩展会自动监视 Cookie 变化并推送到服务器

### 工作原理

- 扩展每 1 分钟检查 Cookie 变化
- 仅在变化时更新服务器和 `.env` 文件
- 服务器被动接收更新，不主动刷新
- 避免恶性循环，减少触发 Google 安全机制

### 独立 Cookie 服务

```bash
cd cookie_service
python server.py
```

## 去水印功能

### 原理

基于固定位置的反向 Alpha 混合算法：

```
original = (watermarked - α × 255) / (1 - α)
```

### 水印位置

- **小水印（48×48）**：图片宽度或高度 ≤ 1024px，距右下角 32px
- **大水印（96×96）**：图片宽度和高度都 > 1024px，距右下角 64px

### 控制去水印

```python
# 方式1：通过模型名（包含 'image' 则自动去水印）
response = client.images.generate(model="gemini-3-pro-image", ...)

# 方式2：通过代理 URL 参数
url = "http://localhost:3897/v1/images/proxy?url=...&remove_watermark=true"
```

## 项目结构

```
Gemini-Free-API/
├── src/gemini_webapi/          # 核心库
│   ├── client.py               # GeminiClient 和 ChatSession
│   ├── constants.py            # 模型、端点常量
│   ├── exceptions.py           # 自定义异常
│   ├── components/             # 混入组件
│   ├── types/                  # 数据类型
│   └── utils/                  # 工具函数
├── cookie_service/             # Cookie 服务
│   ├── extension/              # 浏览器扩展
│   └── server.py               # 独立服务
├── assets/                     # 水印 Alpha 通道
│   ├── bg_48.png
│   └── bg_96.png
├── openai_server.py            # OpenAI 兼容服务器
├── pyproject.toml              # 项目配置
└── requirements.txt            # 服务器依赖
```

## 可选功能：TTS

项目包含 Vertex AI Gemini TTS 集成代码（已注释），需要时可启用：

1. 创建 GCP 服务账号（Vertex AI User 角色）
2. 下载 JSON 密钥文件
3. 配置环境变量：
   ```bash
   VERTEX_PROJECT_ID=your_project_id
   VERTEX_LOCATION=us-central1
   VERTEX_SERVICE_ACCOUNT_KEY=path/to/key.json
   ```
4. 取消注释 `openai_server.py` 中的 TTS 代码

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| HTTP | httpx (异步) |
| 验证 | Pydantic |
| JSON | orjson |
| 日志 | loguru |
| 服务器 | FastAPI + Uvicorn |
| 图像处理 | Pillow + NumPy |

## 注意事项

### Cookie 管理

- ⚠️ 不要提交 `.env` 文件到版本控制
- ⚠️ 建议使用浏览器扩展自动管理 Cookie
- ⚠️ 手动刷新可能触发 Google 安全机制

### 图片生成

- 功能受地区/账户限制
- 需在网页端激活 Gemini 扩展
- 18 岁以下用户不可用

### 性能优化

- 服务器默认禁用自动刷新（依赖扩展）
- 会话缓存最多 500 个，30 天过期
- 支持流式响应减少延迟

## 故障排查

### Cookie 过期

- 检查浏览器扩展是否运行
- 手动点击扩展图标强制更新
- 查看服务器日志：`logs/server.log`

### 初始化失败

- 确认 `.env` 中有有效 Cookie
- 检查网络连接和代理设置
- 查看错误日志：`logs/error.log`

### 账号频繁退出

- 禁用服务器端自动刷新
- 使用浏览器扩展管理 Cookie
- 降低请求频率

## 许可证

详见 `LICENSE` 文件。

## 致谢

- [gemini-webapi](https://pypi.org/project/gemini-webapi/) - 原始项目
- [journey-ad/gemini-watermark-remover](https://github.com/journey-ad/gemini-watermark-remover) - 去水印算法
- [allenk/GeminiWatermarkTool](https://github.com/allenk/GeminiWatermarkTool) - 去水印工具
