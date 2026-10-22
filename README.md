# opencode2api-python

Python-based OpenAI/OpenCode compatible proxy for rapid testing in Colab, with a Cloudflare tunnel.

This repository is a lightweight test/proxy version intended for experimentation and external access from Colab. It exposes a small compatible API surface and forwards requests to an upstream OpenCode/OpenAI compatible service.

## Features
- FastAPI app
- `/v1/models`
- `/v1/chat/completions`
- `/v1/responses`
- `/v1/messages`
- local API key validation
- optional upstream bearer or x-api-key forwarding
- Cloudflare Tunnel instructions for Colab

## Quick start in Colab

1. Create a new notebook in Google Colab.
2. Install dependencies:

```bash
!pip install -q fastapi uvicorn httpx python-multipart
```

3. Upload or paste `app.py` into the notebook.
4. Run:

```python
!nohup python app.py >/tmp/opencode_proxy.log 2>&1 &
```

5. Install Cloudflared:

```bash
!curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
!chmod +x /usr/local/bin/cloudflared
```

6. Start the tunnel:

```bash
!nohup /usr/local/bin/cloudflared tunnel --url http://127.0.0.1:8000 --loglevel info >/tmp/cloudflare_tunnel.log 2>&1 &
```

7. Read the generated URL:

```python
import re
log = open('/tmp/cloudflare_tunnel.log', 'r', errors='ignore').read()
url = re.findall(r'https://[a-z0-9-]+\\.trycloudflare\\.com', log)
print(url[-1] if url else 'URL not ready yet. Wait a few seconds and retry.')
```

## Environment variables

Set before running the app:

```bash
export SERVER_KEY="change-me-local-key"
export UPSTREAM_BASE="https://opencode.ai/zen"
export UPSTREAM_API_KEY="your-upstream-key"
export UPSTREAM_MODEL="gpt-4o-mini"
```

If `UPSTREAM_API_KEY` is empty, the app will forward the client token if it is present.

## Example request

```bash
curl -X POST "https://<your-cloudflare-url>/v1/chat/completions" \
  -H "Authorization: Bearer change-me-local-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello from Colab"}],
    "temperature": 0.7
  }'
```

## Notes

This is a lightweight Python-compatible testing proxy, not a direct code port of the Go project in the upstream repository. It is designed for quick validation, local experiments, and public testing via a Cloudflare tunnel.

## License

MIT
