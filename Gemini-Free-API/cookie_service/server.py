"""
通用 Cookie 服务 - 订阅模式
- 仅内存缓存
- 支持订阅推送
- 第三方应用注册 webhook
"""
import time
import asyncio
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

app = FastAPI(title="Cookie Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存缓存: {domain: {cookie_name: {value, updated_at}}}
cookies_cache: Dict[str, Dict[str, dict]] = defaultdict(dict)

# 订阅列表: {domain: [{webhook_url, cookie_names}]}
subscriptions: Dict[str, List[dict]] = defaultdict(list)


class CookieUpdate(BaseModel):
    cookies: Dict[str, str]


class Subscription(BaseModel):
    domain: str
    webhook_url: str
    cookie_names: Optional[List[str]] = None  # 可选，不提供则监控所有
    app_name: Optional[str] = None  # 应用名称，用于显示


async def notify_subscribers(domain: str, cookies: Dict[str, str]):
    """异步通知所有订阅者"""
    if domain not in subscriptions:
        return
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for sub in subscriptions[domain]:
            webhook_url = sub.get('webhook_url')
            if not webhook_url:
                continue
            
            # 过滤 cookie
            filtered_cookies = cookies
            if sub.get('cookie_names'):
                filtered_cookies = {k: v for k, v in cookies.items() if k in sub['cookie_names']}
            
            if not filtered_cookies:
                continue
            
            try:
                await client.post(
                    webhook_url,
                    json={'domain': domain, 'cookies': filtered_cookies, 'timestamp': time.time()},
                    timeout=5.0
                )
                sub['last_notified'] = time.time()
                sub['notify_count'] = sub.get('notify_count', 0) + 1
                print(f"Notified {sub.get('app_name', webhook_url)} for {domain}")
            except Exception as e:
                print(f"Failed to notify {webhook_url}: {e}")
                sub['last_error'] = str(e)


@app.get("/")
async def root():
    return {
        "service": "Cookie Service",
        "version": "2.0.0",
        "mode": "subscription",
        "domains": list(cookies_cache.keys()),
        "subscriptions": sum(len(v) for v in subscriptions.values())
    }


@app.post("/subscribe")
async def subscribe(sub: Subscription):
    """注册订阅"""
    sub_data = {
        'webhook_url': sub.webhook_url,
        'cookie_names': sub.cookie_names,
        'app_name': sub.app_name or sub.webhook_url,
        'created_at': time.time(),
        'last_notified': None,
        'notify_count': 0
    }
    
    # 避免重复订阅
    for existing in subscriptions[sub.domain]:
        if existing.get('webhook_url') == sub.webhook_url:
            existing.update(sub_data)
            return {"status": "updated", "domain": sub.domain}
    
    subscriptions[sub.domain].append(sub_data)
    return {"status": "subscribed", "domain": sub.domain, "total": len(subscriptions[sub.domain])}


@app.delete("/subscribe")
async def unsubscribe(domain: str, webhook_url: str):
    """取消订阅"""
    if domain not in subscriptions:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    subscriptions[domain] = [s for s in subscriptions[domain] if s.get('webhook_url') != webhook_url]
    
    if not subscriptions[domain]:
        del subscriptions[domain]
    
    return {"status": "unsubscribed", "domain": domain}


@app.get("/subscriptions")
async def list_subscriptions():
    """列出所有已订阅的域名（仅域名，不含敏感信息）"""
    return {
        "domains": list(subscriptions.keys())
    }


@app.get("/subscriptions/my")
async def get_my_subscriptions(webhook_url: str):
    """查看自己的订阅详情（需要提供 webhook_url）"""
    my_subs = {}
    for domain, subs in subscriptions.items():
        for s in subs:
            if s.get('webhook_url') == webhook_url:
                my_subs[domain] = {
                    "app_name": s.get('app_name'),
                    "cookie_names": s.get('cookie_names'),
                    "created_at": s.get('created_at'),
                    "last_notified": s.get('last_notified'),
                    "notify_count": s.get('notify_count', 0),
                    "last_error": s.get('last_error')
                }
                break
    
    if not my_subs:
        raise HTTPException(status_code=404, detail="No subscriptions found for this webhook")
    
    return my_subs


@app.get("/cookies")
async def get_all_cookies():
    """获取所有域名的 cookies"""
    return {
        domain: {name: data["value"] for name, data in cookies.items()}
        for domain, cookies in cookies_cache.items()
    }


@app.get("/cookies/{domain}")
async def get_cookies(domain: str):
    """获取指定域名的所有 cookies"""
    if domain not in cookies_cache:
        raise HTTPException(status_code=404, detail=f"Domain {domain} not found")
    
    return {name: data["value"] for name, data in cookies_cache[domain].items()}


@app.get("/cookies/{domain}/{name}")
async def get_cookie(domain: str, name: str):
    """获取指定域名的指定 cookie"""
    if domain not in cookies_cache:
        raise HTTPException(status_code=404, detail=f"Domain {domain} not found")
    
    if name not in cookies_cache[domain]:
        raise HTTPException(status_code=404, detail=f"Cookie {name} not found")
    
    return {
        "name": name,
        "value": cookies_cache[domain][name]["value"],
        "updated_at": cookies_cache[domain][name]["updated_at"]
    }


@app.post("/cookies/{domain}")
async def update_cookies(domain: str, data: CookieUpdate, background_tasks: BackgroundTasks):
    """更新指定域名的 cookies（扩展调用）"""
    current_time = time.time()
    
    for name, value in data.cookies.items():
        cookies_cache[domain][name] = {
            "value": value,
            "updated_at": current_time
        }
    
    # 异步通知订阅者
    background_tasks.add_task(notify_subscribers, domain, data.cookies)
    
    return {
        "status": "ok",
        "domain": domain,
        "updated": len(data.cookies),
        "timestamp": current_time,
        "notified": len(subscriptions.get(domain, []))
    }


@app.get("/domains")
async def list_domains():
    """列出所有已缓存的域名"""
    return {
        "domains": [
            {
                "domain": domain,
                "cookies_count": len(cookies),
                "subscribers": len(subscriptions.get(domain, [])),
                "last_updated": max((c["updated_at"] for c in cookies.values()), default=0)
            }
            for domain, cookies in cookies_cache.items()
        ]
    }


@app.delete("/cookies/{domain}")
async def delete_domain(domain: str):
    """删除指定域名的所有 cookies"""
    if domain not in cookies_cache:
        raise HTTPException(status_code=404, detail=f"Domain {domain} not found")
    
    del cookies_cache[domain]
    return {"status": "ok", "message": f"Deleted all cookies for {domain}"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy", "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn
    import os
    import subprocess
    import sys
    
    # 确保工作目录正确
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    sys.path.insert(0, script_dir)
    
    port = int(os.getenv("COOKIE_SERVICE_PORT", 3898))
    host = os.getenv("COOKIE_SERVICE_HOST", "0.0.0.0")  # 宝塔需要 0.0.0.0
    
    # 启动时自动释放端口（仅 Windows）
    if os.name == 'nt':
        try:
            result = subprocess.run(f'netstat -ano | findstr :{port} | findstr LISTENING', 
                                  shell=True, capture_output=True, text=True)
            if result.stdout.strip():
                pids = set()
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 5 and parts[-1].isdigit() and parts[-1] != '0':
                        pids.add(parts[-1])
                
                if pids:
                    print(f"Killing processes on port {port}: {pids}")
                    for pid in pids:
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(2)
        except Exception as e:
            print(f"Port check error: {e}")
    
    print(f"Cookie Service starting on {host}:{port}")
    print(f"Working directory: {os.getcwd()}")
    
    # 使用 app 对象而不是字符串
    uvicorn.run(app, host=host, port=port)
