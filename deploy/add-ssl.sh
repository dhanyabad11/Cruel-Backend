#!/bin/bash

# Add SSL to Digital Ocean Backend
echo "Installing Certbot..."
apt-get update
apt-get install -y certbot python3-certbot-nginx

echo "Please enter your domain name (e.g., api.yourdomain.com):"
read DOMAIN

echo "Please enter your email for SSL certificate notifications:"
read EMAIL

# Get SSL certificate
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL

# Update nginx config to use SSL
cat > /etc/nginx/sites-available/ai-cruel << NGINX_EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri\;
}

server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location / {
        proxy_pass http://localhost:8000\;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX_EOF

nginx -t && systemctl reload nginx

echo "SSL certificate installed successfully!"
echo "Update your frontend NEXT_PUBLIC_API_URL to: https://$DOMAIN"
