# PuterImage Studio — Cookie Extractor

Chrome/Edge extension that automatically extracts Gemini cookies from your browser.

## Install

1. Open `chrome://extensions/` (or `edge://extensions/`)
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select this `extension/` folder
5. The extension icon appears in your toolbar

## Usage

1. Log in at [gemini.google.com](https://gemini.google.com)
2. Log in to PuterImage Studio and copy your JWT token from Settings
3. Click the extension icon → paste the token → **Extract & Send**

## Permissions

- `cookies` — to read `__Secure-1PSID` and `__Secure-1PSIDTS` from `.google.com`
- `storage` — to save your token locally
- `host_permissions: *.google.com` — to read Google cookies

No data leaves your browser except the cookies sent to your configured API backend.
