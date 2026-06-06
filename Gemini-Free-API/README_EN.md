# Gemini-Free-API

Async Python wrapper for Google Gemini Web API with OpenAI-compatible interface.

> 💡 **Free Access to Gemini 3.0 Pro Thinking**  
> No paid subscription required. Use the latest Gemini 3.0 Pro Thinking model for free with just a Google account. Supports deep thinking, image generation, and more. Pro accounts have higher daily usage limits.

[中文文档](README.md) | English

## Features

- ⭐ **Free Gemini 3.0 Pro Thinking** - No payment required, supports deep thinking and image generation
- ✅ **OpenAI Compatible** - Drop-in replacement for OpenAI SDK
- ✅ **Sync with Web** - Share conversation history with Gemini web version, no data loss
- ✅ **Auto Watermark Removal** - Automatically remove Gemini watermarks using reverse alpha blending
- ✅ **Multimodal Support** - Text, image upload, and image generation
- ✅ **Auto Cookie Refresh** - Browser extension automatically updates cookies
- ✅ **Session Management** - Smart session caching with multi-turn conversations
- ✅ **Async Design** - Efficient concurrent request handling with asyncio

## Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

### 2. Get Gemini Cookies

- Visit https://gemini.google.com and login
- Press F12 → Application → Cookies
- Copy `__Secure-1PSID` and `__Secure-1PSIDTS`

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in the cookies
```

### 4. Start Server

```bash
python openai_server.py
# Or use startup script
start.bat  # Windows
# ./start.sh  # Linux/Mac
```

Server: `http://localhost:3897`  
API Docs: `http://localhost:3897/docs`

## Usage Examples

### Basic Chat

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

### Image Upload

```python
# Supports URL, base64, and local files
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
    }]
)
```

### Image Generation (Auto Watermark Removal)

```python
response = client.images.generate(
    model="gemini-3-pro-image",  # Models with 'image' auto-remove watermarks
    prompt="A beautiful sunset over mountains",
    n=1,
    size="1024x1024"
)
print(response.data[0].url)
```

### Streaming

```python
stream = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /v1/models` | List available models |
| `POST /v1/chat/completions` | Chat completion (streaming, image upload) |
| `POST /v1/images/generations` | Image generation (auto watermark removal) |
| `GET /v1/images/proxy` | Image proxy (supports `?remove_watermark=true/false`) |

## Model Mapping

| OpenAI Model | Gemini Model |
|--------------|--------------|
| gpt-3.5-turbo | gemini-2.5-flash |
| gpt-4 | gemini-2.5-pro |
| gpt-4-turbo | gemini-2.5-pro |
| gemini-3-pro-image | gemini-3.0-pro (auto watermark removal) |

## Auto Cookie Refresh

### Browser Extension (Recommended)

1. Load extension: `cookie_service/extension/`
2. Visit https://gemini.google.com and login
3. Extension monitors cookie changes and pushes to server

### How It Works

- Extension checks cookies every 1 minute
- Updates server and `.env` only when changed
- Server passively receives updates, no active refresh
- Avoids loops and reduces Google security triggers

## Watermark Removal

### Algorithm

Reverse alpha blending:

```
original = (watermarked - α × 255) / (1 - α)
```

### Watermark Positions

- **Small (48×48)**: Width or height ≤ 1024px, 32px from bottom-right
- **Large (96×96)**: Both width and height > 1024px, 64px from bottom-right

### Control

```python
# Method 1: Model name (contains 'image' = auto remove)
response = client.images.generate(model="gemini-3-pro-image", ...)

# Method 2: Proxy URL parameter
url = "http://localhost:3897/v1/images/proxy?url=...&remove_watermark=true"
```

## Project Structure

```
Gemini-Free-API/
├── src/gemini_webapi/          # Core library
│   ├── client.py               # GeminiClient and ChatSession
│   ├── constants.py            # Models and endpoints
│   ├── exceptions.py           # Custom exceptions
│   ├── components/             # Mixin components
│   ├── types/                  # Data types
│   └── utils/                  # Utilities
├── cookie_service/             # Cookie service
│   ├── extension/              # Browser extension
│   └── server.py               # Standalone service
├── assets/                     # Watermark alpha channels
│   ├── bg_48.png
│   └── bg_96.png
├── openai_server.py            # OpenAI-compatible server
├── pyproject.toml              # Project config
└── requirements.txt            # Dependencies
```

## Optional: TTS

Vertex AI Gemini TTS integration code is included (commented out). To enable:

1. Create GCP service account (Vertex AI User role)
2. Download JSON key file
3. Configure environment:
   ```bash
   VERTEX_PROJECT_ID=your_project_id
   VERTEX_LOCATION=us-central1
   VERTEX_SERVICE_ACCOUNT_KEY=path/to/key.json
   ```
4. Uncomment TTS code in `openai_server.py`

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.10+ |
| HTTP | httpx (async) |
| Validation | Pydantic |
| JSON | orjson |
| Logging | loguru |
| Server | FastAPI + Uvicorn |
| Image | Pillow + NumPy |

## Notes

### Cookie Management

- ⚠️ Don't commit `.env` to version control
- ⚠️ Use browser extension for auto management
- ⚠️ Manual refresh may trigger Google security

### Image Generation

- Feature availability varies by region/account
- Activate Gemini extensions on web first
- Not available for users under 18

### Performance

- Server auto-refresh disabled by default (uses extension)
- Session cache: max 500, 30-day expiry
- Streaming support for reduced latency

## Troubleshooting

### Cookie Expired

- Check if browser extension is running
- Click extension icon to force update
- Check server logs: `logs/server.log`

### Init Failed

- Verify valid cookies in `.env`
- Check network and proxy settings
- Check error logs: `logs/error.log`

### Frequent Logouts

- Disable server-side auto refresh
- Use browser extension for cookie management
- Reduce request frequency

## License

See `LICENSE` file.

## Credits

- [gemini-webapi](https://pypi.org/project/gemini-webapi/) - Original project
- [journey-ad/gemini-watermark-remover](https://github.com/journey-ad/gemini-watermark-remover) - Watermark removal algorithm
- [allenk/GeminiWatermarkTool](https://github.com/allenk/GeminiWatermarkTool) - Watermark removal tool
