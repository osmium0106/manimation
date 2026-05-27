#!/bin/bash

set -e

echo "Starting backend..."

cd /app/platform/backend

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 &

echo "Starting nginx..."

cat >/etc/nginx/sites-enabled/default <<EOF
server {
    listen 80;

    client_max_body_size 500M;

    location / {
        root /app/platform/frontend/dist;
        index index.html;
        try_files \$uri /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;

        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

nginx -g "daemon off;"
