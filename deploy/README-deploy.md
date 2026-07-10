# Deploying PAIGE on Ubuntu EC2 (Nginx + systemd)

PAIGE consists of two pieces:

- **Backend** — FastAPI + Pydantic AI served by `uvicorn` (managed by systemd).
- **Frontend** — a React (Vite/TypeScript/Tailwind) SPA built to static files and
  served by Nginx, which also reverse-proxies `/api` to the backend.

The instructions below assume the repository is checked out to `/opt/highlight`.

## 1. System packages

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx
# Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

## 2. Backend

```bash
cd /opt/highlight
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .           # installs the highlight package + FastAPI/Pydantic AI deps

# Provide credentials. Copy the repo .env into the backend directory so the
# systemd EnvironmentFile can load it.
cp .env backend/.env
```

`backend/.env` must contain (moved off Azure — a base URL is now required):

```dotenv
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-5.5-project"
OPENAI_EMBEDDING_MODEL="text-embedding-3-large-project"
OPENAI_BASE_URL="https://ai-incubator-api.pnnl.gov"
IM3_ACCESS="phase3"
```

Install and start the service:

```bash
sudo cp deploy/paige-backend.service /etc/systemd/system/paige-backend.service
sudo systemctl daemon-reload
sudo systemctl enable --now paige-backend
sudo systemctl status paige-backend
```

The API is now available on `127.0.0.1:8000` (health check: `GET /api/health`).

## 3. Frontend

```bash
cd /opt/highlight/frontend
npm install
npm run build          # outputs to frontend/dist

sudo mkdir -p /var/www/paige
sudo cp -r dist/* /var/www/paige/
```

## 4. Nginx

```bash
sudo cp deploy/nginx-paige.conf /etc/nginx/sites-available/paige
sudo ln -s /etc/nginx/sites-available/paige /etc/nginx/sites-enabled/paige
sudo rm -f /etc/nginx/sites-enabled/default   # optional
sudo nginx -t && sudo systemctl reload nginx
```

Visit `http://<ec2-public-dns>/`. Because the SPA uses same-origin relative
`/api` URLs, no CORS configuration is required in production.

## 5. HTTPS (recommended)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d paige.example.com
```

## 6. Updating a deployment

```bash
cd /opt/highlight
git pull
source .venv/bin/activate && pip install .   # if backend deps changed
sudo systemctl restart paige-backend

cd frontend && npm install && npm run build
sudo cp -r dist/* /var/www/paige/
```

## Notes

- The backend keeps sessions and uploaded document content **in memory**, which
  is appropriate for a single-instance deployment. For horizontal scaling,
  replace `backend/app/session.py` with a shared store (e.g. Redis).
- Users can authenticate with the shared `IM3_ACCESS` password or by supplying
  their own OpenAI-compatible API key and base URL in the sign-in screen.
