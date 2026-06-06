"""
第三方应用订阅 Cookie 服务示例
"""
import requests
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# Cookie 服务地址
COOKIE_SERVICE = "http://localhost:3898"

# Webhook 接收地址（本应用）
WEBHOOK_URL = "http://localhost:5000/webhook"


@app.on_event("startup")
async def subscribe_cookies():
    """应用启动时订阅 cookies"""
    try:
        response = requests.post(
            f"{COOKIE_SERVICE}/subscribe",
            json={
                "domain": ".google.com",
                "webhook_url": WEBHOOK_URL,
                "cookie_names": ["__Secure-1PSID", "__Secure-1PSIDTS"],
                "app_name": "Gemini API"
            }
        )
        print(f"订阅结果: {response.json()}")
    except Exception as e:
        print(f"订阅失败: {e}")


@app.post("/webhook")
async def receive_cookies(data: dict):
    """接收 Cookie 更新推送"""
    domain = data.get("domain")
    cookies = data.get("cookies")
    timestamp = data.get("timestamp")
    
    print(f"\n收到 Cookie 更新:")
    print(f"  域名: {domain}")
    print(f"  Cookies: {cookies}")
    print(f"  时间: {timestamp}\n")
    
    # 这里处理 cookie 更新逻辑
    # 例如：更新 .env 文件、重新初始化客户端等
    
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"app": "Cookie Subscriber Example", "webhook": WEBHOOK_URL}


if __name__ == "__main__":
    uvicorn.run("example_subscriber:app", host="0.0.0.0", port=5000, reload=False)
