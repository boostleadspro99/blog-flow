// ── DOM refs ──
const apiUrlInput = document.getElementById('apiUrl');
const tokenInput = document.getElementById('token');
const extractBtn = document.getElementById('extractBtn');
const statusDiv = document.getElementById('status');
const cookieInfo = document.getElementById('cookieInfo');

// ── Load saved settings ──
chrome.storage.local.get(['apiUrl', 'token'], (data) => {
  if (data.apiUrl) apiUrlInput.value = data.apiUrl;
  if (data.token) tokenInput.value = data.token;
});

// ── Status helpers ──
function showStatus(type, message) {
  statusDiv.className = `status show ${type}`;
  statusDiv.textContent = message;
}

function hideStatus() {
  statusDiv.className = 'status';
}

// ── Main extraction ──
extractBtn.addEventListener('click', async () => {
  const apiUrl = apiUrlInput.value.trim();
  const token = tokenInput.value.trim();

  if (!apiUrl) { showStatus('error', 'Please enter your API Backend URL.'); return; }
  if (!token) { showStatus('error', 'Please paste your JWT token from the Settings page.'); return; }

  // Save settings
  chrome.storage.local.set({ apiUrl, token });

  // Disable button
  extractBtn.disabled = true;
  extractBtn.textContent = '⏳ Extracting...';
  showStatus('loading', 'Reading cookies from .google.com...');

  try {
    // Get cookies for .google.com domain (covers gemini.google.com, accounts.google.com, etc.)
    const cookies = await chrome.cookies.getAll({ domain: '.google.com' });

    if (cookies.length === 0) {
      showStatus('error', 'No .google.com cookies found. Make sure you are logged in at gemini.google.com');
      extractBtn.disabled = false;
      extractBtn.textContent = '🔍 Extract & Send Cookies';
      return;
    }

    // Find the Gemini session cookies
    const psidCookie = cookies.find(c => c.name === '__Secure-1PSID');
    const psidtsCookie = cookies.find(c => c.name === '__Secure-1PSIDTS');

    if (!psidCookie) {
      showStatus('error', '__Secure-1PSID cookie not found. Are you logged in to gemini.google.com?');
      extractBtn.disabled = false;
      extractBtn.textContent = '🔍 Extract & Send Cookies';
      return;
    }

    cookieInfo.innerHTML = `
      Found ${cookies.length} cookies on .google.com<br>
      <span style="color:#6ee7b7;">__Secure-1PSID ✓</span> (${psidCookie.value.length} chars)<br>
      ${psidtsCookie ? '<span style="color:#6ee7b7;">__Secure-1PSIDTS ✓</span> (' + psidtsCookie.value.length + ' chars)' : '<span style="color:#fca5a5;">__Secure-1PSIDTS ✗ not found</span>'}
    `;

    // Send to backend
    showStatus('loading', 'Sending cookies to server...');

    const response = await fetch(`${apiUrl}/user/cookies`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        secure_1psid: psidCookie.value,
        secure_1psidts: psidtsCookie ? psidtsCookie.value : '',
      }),
    });

    const data = await response.json();

    if (response.ok && data.is_valid) {
      showStatus('success', '✅ Cookies validated! Your Gemini client is ready. You can now generate images.');
    } else if (response.ok && !data.is_valid) {
      showStatus('error', `⚠️ Cookies saved but validation failed: ${data.error_message || 'Unknown error'}`);
    } else if (response.status === 401) {
      showStatus('error', '❌ Invalid token. Please copy a fresh JWT token from Settings.');
    } else {
      showStatus('error', `❌ Server error (${response.status}): ${data.detail || 'Unknown'}`);
    }
  } catch (err) {
    if (err.message.includes('cookies')) {
      showStatus('error', '❌ Cannot access cookies. Make sure the extension has cookie permissions.');
    } else {
      showStatus('error', `❌ Connection failed: ${err.message}. Check your API URL.`);
    }
  }

  extractBtn.disabled = false;
  extractBtn.textContent = '🔍 Extract & Send Cookies';
});
