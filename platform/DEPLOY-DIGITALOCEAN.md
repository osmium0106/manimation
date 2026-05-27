# Deploy Manimations Studio on DigitalOcean

Step-by-step guide to run **frontend + backend + Manim rendering** on a single DigitalOcean Droplet.

This app is **local-first by design** (projects saved as JSON on disk, no database). One VPS is the simplest and most reliable setup because Manim needs FFmpeg, Cairo, and enough CPU/RAM to render video.

---

## What you are deploying

| Component | Tech | Production role |
|-----------|------|-----------------|
| Frontend | React + Vite | Static files served by Nginx |
| Backend | FastAPI + Uvicorn | API on port 8000 (internal) |
| Renderer | Manim CE | Subprocess from backend |
| Storage | Filesystem | `~/manimations-studio/projects/` |
| AI | OpenAI API | Beat chat + icon resolution |

**URLs (example):**

- `https://studio.yourdomain.com` → frontend
- `https://studio.yourdomain.com/api/...` → proxied to backend

---

## Recommended Droplet

| Setting | Recommendation |
|---------|----------------|
| **Plan** | Basic Droplet (Dedicated CPU preferred for renders) |
| **Size** | **4 GB RAM / 2 vCPU** minimum (8 GB if you export 1080p60 often) |
| **OS** | **Ubuntu 24.04 LTS** |
| **Region** | Closest to your users |
| **Storage** | 50 GB+ SSD (projects + Manim cache + media) |

Manim renders are CPU-heavy. Preview (`-ql`) is lighter; export (`-qh` 1080p60) needs more headroom.

---

## Overview (7 phases)

1. Create Droplet + SSH in  
2. Install system dependencies (FFmpeg, Cairo, Node, Python)  
3. Clone repo + Python/Manim venv  
4. Configure environment (`.env`, CORS, data dir)  
5. Build frontend + configure Nginx  
6. Run backend with systemd  
7. HTTPS + firewall + smoke test  

---

## Phase 1 — Create the Droplet

1. Log in to [DigitalOcean](https://cloud.digitalocean.com/).
2. **Create → Droplets**
3. Choose **Ubuntu 24.04 LTS**
4. Choose **4 GB RAM / 2 vCPU** (or larger)
5. Add your **SSH key** (recommended) or use a password
6. Create the Droplet
7. Point a domain (optional but recommended):
   - DigitalOcean → **Networking → Domains** → add `yourdomain.com`
   - Create an **A record**: `studio` → your Droplet IP

SSH in:

```bash
ssh root@YOUR_DROPLET_IP
```

Create a deploy user (do not run the app as root):

```bash
adduser manim
usermod -aG sudo manim
rsync --archive --chown=manim:manim ~/.ssh /home/manim
```

Log in as that user:

```bash
ssh manim@YOUR_DROPLET_IP
```

---

## Phase 2 — System dependencies

Manim and the studio need OS packages beyond pip/npm.

```bash
sudo apt update && sudo apt upgrade -y

# Build tools + Manim multimedia stack
sudo apt install -y \
  git curl nginx certbot python3-certbot-nginx \
  python3 python3-venv python3-pip \
  ffmpeg \
  libcairo2-dev libpango1.0-dev \
  pkg-config \
  build-essential

# Node.js 20 LTS (for building the frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

node -v   # v20.x
python3 --version
ffmpeg -version
```

Optional (only if scenes use LaTeX / MathTex):

```bash
sudo apt install -y texlive-latex-extra texlive-fonts-extra dvisvgm
```

---

## Phase 3 — Clone repo and install Python

### 3.1 Clone

```bash
cd ~
git clone https://github.com/eskeon/manim-renderer.git manimations
cd manimations
```

(Or use your own fork URL.)

### 3.2 Root venv — Manim (used by the renderer)

The backend calls `manim render` using the repo root `.venv`:

```bash
cd ~/manimations
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# If pyproject.toml requires Python 3.14 and apt only has 3.12, either:
#   - install a newer Python via deadsnakes/uv, OR
#   - temporarily set requires-python = ">=3.11" in pyproject.toml
pip install -e .
manim --version
deactivate
```

### 3.3 Backend venv — FastAPI

```bash
cd ~/manimations/platform/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

### 3.4 Smoke-test Manim render (optional)

```bash
cd ~/manimations
source .venv/bin/activate
manim -ql platform/backend/app/../../Episode1/beats/beat1/welcome_to_python.py WelcomeToPython 2>/dev/null || \
  echo "Use any small scene in the repo to verify Manim works"
deactivate
```

---

## Phase 4 — Environment and production tweaks

### 4.1 OpenAI key

```bash
cp ~/manimations/platform/.env.example ~/manimations/platform/.env
nano ~/manimations/platform/.env
```

Set:

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

Lock permissions:

```bash
chmod 600 ~/manimations/platform/.env
```

### 4.2 CORS — allow your production domain

Edit `platform/backend/app/main.py` and add your site to `allow_origins`:

```python
allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://studio.yourdomain.com",   # ← your real URL
],
```

Or set origins from an env var (recommended for multiple environments).

### 4.3 Data directory

Projects are stored under the **deploy user's home**:

```
/home/manim/manimations-studio/projects/
```

No database setup required. Back up this folder regularly.

### 4.4 Background path

Generated scenes reference `background/orange_theme_BG.png` under the repo. Keep the full repo checkout intact (do not deploy only `platform/`).

---

## Phase 5 — Build frontend

```bash
cd ~/manimations/platform/frontend
npm ci
npm run build
```

Output: `platform/frontend/dist/` (static HTML/JS/CSS)

The frontend calls `/api/...` relative to the same host, so Nginx must proxy `/api` to the backend (next phase).

---

## Phase 6 — Nginx + systemd

### 6.1 Nginx site config

Copy the example and edit your domain:

```bash
sudo cp ~/manimations/platform/deploy/nginx.conf.example \
  /etc/nginx/sites-available/manimations-studio
sudo nano /etc/nginx/sites-available/manimations-studio
```

Replace `studio.yourdomain.com` with your domain (or use `_` / IP-only for testing).

Enable the site:

```bash
sudo ln -sf /etc/nginx/sites-available/manimations-studio \
  /etc/nginx/sites-enabled/manimations-studio
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### 6.2 Backend systemd service

```bash
sudo cp ~/manimations/platform/deploy/manimations-backend.service.example \
  /etc/systemd/system/manimations-backend.service
sudo nano /etc/systemd/system/manimations-backend.service
```

Ensure `User=manim` and paths match your clone location (`/home/manim/manimations`).

Start and enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable manimations-backend
sudo systemctl start manimations-backend
sudo systemctl status manimations-backend
```

Logs:

```bash
journalctl -u manimations-backend -f
```

---

## Phase 7 — HTTPS, firewall, verify

### 7.1 Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### 7.2 TLS (Let's Encrypt)

```bash
sudo certbot --nginx -d studio.yourdomain.com
```

Certbot updates Nginx for HTTPS and auto-renewal.

### 7.3 Smoke test

```bash
curl -s http://127.0.0.1:8000/api/health
curl -sI https://studio.yourdomain.com/
curl -s https://studio.yourdomain.com/api/health
```

In the browser:

1. Open `https://studio.yourdomain.com`
2. Create a project
3. Generate a 1-beat script and **Render preview**
4. Confirm MP4 plays

If render fails, check:

```bash
journalctl -u manimations-backend -n 100 --no-pager
ls -la ~/manimations/media/videos/
```

Common fixes:

- Manim not in root venv → re-run Phase 3.2  
- FFmpeg missing → `sudo apt install ffmpeg`  
- Out of memory → upgrade Droplet or render preview only  

---

## Updating after git push

```bash
ssh manim@YOUR_DROPLET_IP
cd ~/manimations
git pull

# Backend deps (if requirements changed)
cd platform/backend && source .venv/bin/activate && pip install -r requirements.txt && deactivate

# Manim deps (if pyproject changed)
cd ~/manimations && source .venv/bin/activate && pip install -e . && deactivate

# Frontend
cd ~/manimations/platform/frontend && npm ci && npm run build

sudo systemctl restart manimations-backend
sudo systemctl reload nginx
```

---

## Architecture diagram

```
Internet
   │
   ▼
┌──────────────────────────────────────┐
│  Nginx (:443)                        │
│  ├─ /        → frontend/dist (static)│
│  └─ /api/*   → proxy → Uvicorn :8000 │
└──────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  FastAPI (systemd)                   │
│  ├─ OpenAI API                       │
│  ├─ ~/manimations-studio/projects/   │
│  └─ subprocess: manim render         │
│       uses ~/manimations/.venv       │
└──────────────────────────────────────┘
```

---

## Alternative: DigitalOcean App Platform

**Not recommended** for this project unless you use a **custom Dockerfile** that includes Manim, FFmpeg, and Cairo. App Platform is great for stateless APIs; Manim rendering is heavy, slow, and writes large files to disk.

If you still want App Platform:

- Use a **Dockerfile** based on `ubuntu:24.04` with all Phase 2 packages
- Mount a **DigitalOcean Volume** for `manimations-studio` data
- Split frontend (static site) and backend (service) — but renders will still need the same system deps

For most teams, **one Droplet + Nginx + systemd** (this guide) is simpler and cheaper.

---

## Security checklist

- [ ] SSH keys only (disable password login)
- [ ] `ufw` enabled (22 + 80/443 only)
- [ ] HTTPS via Certbot
- [ ] `platform/.env` mode `600`, never committed
- [ ] Restrict studio URL (Basic Auth in Nginx, VPN, or DO firewall to your IP) if not public
- [ ] Rotate `OPENAI_API_KEY` if leaked
- [ ] Regular backups of `~/manimations-studio/`

---

## Optional: Basic Auth (private studio)

Add inside your Nginx `server` block:

```nginx
auth_basic "Manimations Studio";
auth_basic_user_file /etc/nginx/.htpasswd;
```

Create password file:

```bash
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd yourusername
sudo systemctl reload nginx
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| UI loads, API 502 | Backend down | `systemctl status manimations-backend` |
| CORS error in browser | Origin not in allow list | Update `main.py` CORS |
| Render timeout | Droplet too small | Upgrade RAM/CPU |
| `Manim render failed` | Missing venv/deps | Phase 3.2 + FFmpeg |
| Icons missing | No outbound HTTPS | Allow egress; Iconify API |
| OpenAI 503 | Missing API key | Check `platform/.env` |

---

## Quick reference paths (on server)

| Path | Purpose |
|------|---------|
| `~/manimations/` | Git repo |
| `~/manimations/.venv/` | Manim Python |
| `~/manimations/platform/backend/.venv/` | FastAPI Python |
| `~/manimations/platform/frontend/dist/` | Built UI |
| `~/manimations-studio/projects/` | User projects + renders |
| `/etc/nginx/sites-available/manimations-studio` | Nginx config |
| `/etc/systemd/system/manimations-backend.service` | Backend service |

---

## Related files in this repo

- `platform/deploy/nginx.conf.example` — Nginx template  
- `platform/deploy/manimations-backend.service.example` — systemd unit  
- `platform/README.md` — local development  
- `platform/.env.example` — environment variables  
