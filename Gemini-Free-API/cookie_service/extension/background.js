// 默认配置 - 从订阅列表动态获取
const CHECK_INTERVAL = 1; // 分钟
const API_BASE = 'http://localhost:3898';

// 获取需要监控的域名列表
async function getMonitoredDomains() {
  try {
    const response = await fetch(`${API_BASE}/subscriptions`);
    if (!response.ok) return [];
    
    const data = await response.json();
    return data.domains || [];
  } catch (e) {
    console.error('Failed to get subscriptions:', e);
    return [];
  }
}

// 获取并发送 cookies 到服务器
async function updateCookies(force = false) {
  try {
    const domains = await getMonitoredDomains();
    
    if (domains.length === 0) {
      console.log('No subscriptions found');
      return;
    }
    
    for (const domain of domains) {
      const cookies = await chrome.cookies.getAll({ domain });
      
      if (cookies.length === 0) {
        console.log(`No cookies found for ${domain}`);
        continue;
      }
      
      const result = {};
      for (const cookie of cookies) {
        result[cookie.name] = cookie.value;
      }
      
      // 如果不是强制更新，先比较
      if (!force) {
        try {
          const serverResponse = await fetch(`${API_BASE}/cookies/${encodeURIComponent(domain)}`);
          if (serverResponse.ok) {
            const serverCookies = await serverResponse.json();
            
            let changed = false;
            for (const [name, value] of Object.entries(result)) {
              if (serverCookies[name] !== value) {
                changed = true;
                break;
              }
            }
            
            if (!changed) {
              console.log(`Cookies unchanged for ${domain}`);
              continue;
            }
          }
        } catch (e) {
          // 服务器可能还没启动，继续更新
        }
      }
      
      // 更新到服务器
      const response = await fetch(`${API_BASE}/cookies/${encodeURIComponent(domain)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cookies: result })
      });
      
      const data = await response.json();
      console.log(`Cookies updated for ${domain}:`, data);
    }
  } catch (e) {
    console.error('Failed to update cookies:', e);
  }
}

// 扩展安装时
chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed, force updating cookies...');
  updateCookies(true);
  
  chrome.alarms.create('updateCookies', {
    periodInMinutes: CHECK_INTERVAL
  });
});

// 扩展启动时
chrome.runtime.onStartup.addListener(() => {
  console.log('Extension started, force updating cookies...');
  updateCookies(true);
});

// 定时器触发
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'updateCookies') {
    console.log('Alarm triggered, checking cookies...');
    updateCookies(false);
  }
});

// 监听来自 popup 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'updateNow') {
    updateCookies(true).then(() => {
      sendResponse({ success: true });
    }).catch(e => {
      sendResponse({ success: false, error: e.message });
    });
    return true;
  }
  
  if (request.action === 'getStatus') {
    fetch(`${API_BASE}/`)
      .then(r => r.json())
      .then(data => sendResponse({ success: true, data }))
      .catch(e => sendResponse({ success: false, error: e.message }));
    return true;
  }
});
