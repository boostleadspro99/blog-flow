# Cookie 服务 - 订阅模式

通用 Cookie 提取和推送服务，支持多应用订阅。

## 架构

```
浏览器扩展 → 实时提取 cookies
    ↓
Cookie 服务 (内存缓存 + 订阅管理)
    ↓
Webhook 推送 → 第三方应用
```

## 快速开始

### 1. 启动 Cookie 服务

```bash
cd cookie_service
pip install -r requirements.txt
python server.py
```

服务默认运行在 `http://localhost:3898`

### 2. 安装浏览器扩展

1. 打开 Chrome/Edge 浏览器
2. 访问 `chrome://extensions/`
3. 开启"开发者模式"
4. 点击"加载已解压的扩展程序"
5. 选择 `cookie_service/extension` 目录

### 3. 第三方应用订阅

```python
import requests

# 订阅 Google cookies
requests.post("http://localhost:3898/subscribe", json={
    "domain": ".google.com",
    "webhook_url": "http://your-app:5000/webhook",
    "cookie_names": ["__Secure-1PSID", "__Secure-1PSIDTS"],
    "app_name": "My App"
})
```

### 4. 接收推送

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/webhook")
async def receive_cookies(data: dict):
    domain = data["domain"]
    cookies = data["cookies"]
    # 处理 cookie 更新
    return {"status": "ok"}
```

## API 文档

### 订阅管理

**注册订阅**
```http
POST /subscribe
Content-Type: application/json

{
  "domain": ".google.com",
  "webhook_url": "http://localhost:5000/webhook",
  "cookie_names": ["__Secure-1PSID"],  // 可选，不提供则推送所有
  "app_name": "My App"  // 可选，用于显示
}
```

**取消订阅**
```http
DELETE /subscribe?domain=.google.com&webhook_url=http://localhost:5000/webhook
```

**查看订阅列表**
```http
GET /subscriptions
```

### Cookie 查询

**获取所有 cookies**
```http
GET /cookies
```

**获取指定域名 cookies**
```http
GET /cookies/.google.com
```

**获取指定 cookie**
```http
GET /cookies/.google.com/__Secure-1PSID
```

### 健康检查

```http
GET /health
```

## 工作流程

1. **第三方应用启动** → 调用 `/subscribe` 注册订阅
2. **浏览器扩展** → 每分钟检查 cookies 变化
3. **Cookie 变化** → 扩展推送到服务
4. **服务推送** → 异步通知所有订阅者的 webhook
5. **应用接收** → 处理 cookie 更新

## 特性

- ✅ 零配置 - 扩展自动从订阅列表获取域名
- ✅ 实时推送 - Cookie 变化立即通知
- ✅ 多应用支持 - 一个服务支持多个应用订阅
- ✅ 选择性订阅 - 可指定需要的 cookie 字段
- ✅ 内存缓存 - 无持久化，重启即清空
- ✅ 异步推送 - 不阻塞主流程

## 示例

查看 `example_subscriber.py` 了解完整的订阅示例。

## 环境变量

```bash
COOKIE_SERVICE_PORT=3898  # 服务端口
COOKIE_SERVICE_HOST=127.0.0.1  # 服务地址
```
