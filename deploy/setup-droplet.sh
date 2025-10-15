#!/bin/bash

#############################################
# AI Cruel Backend - Droplet Setup Script
#############################################
# This script sets up a fresh Ubuntu droplet with:
# - Docker & Docker Compose
# - Nginx reverse proxy with SSL
# - Backend deployment automation
#############################################

set -e  # Exit on any error

echo "=========================================="
echo "AI Cruel Backend - Droplet Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use: sudo bash setup-droplet.sh)"
   exit 1
fi

log_info "Starting droplet setup..."

# Update system
log_info "Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
log_info "Installing essential packages..."
apt install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    ufw \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Install Docker
log_info "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    log_info "Docker installed successfully"
else
    log_warn "Docker already installed"
fi

# Install Docker Compose
log_info "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log_info "Docker Compose installed successfully"
else
    log_warn "Docker Compose already installed"
fi

# Install Nginx
log_info "Installing Nginx..."
if ! command -v nginx &> /dev/null; then
    apt install -y nginx
    systemctl enable nginx
    systemctl start nginx
    log_info "Nginx installed successfully"
else
    log_warn "Nginx already installed"
fi

# Configure firewall
log_info "Configuring firewall..."
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # Backend (optional, for direct access)
log_info "Firewall configured"

# Create application directory
log_info "Creating application directory..."
mkdir -p /var/www/ai-cruel-backend
cd /var/www/ai-cruel-backend

# Clone repository
log_info "Enter your GitHub repository URL (or press Enter to skip):"
read -p "Repository URL: " REPO_URL

if [ -n "$REPO_URL" ]; then
    log_info "Cloning repository..."
    if [ -d ".git" ]; then
        log_warn "Repository already exists, pulling latest changes..."
        git pull
    else
        git clone "$REPO_URL" .
    fi
else
    log_warn "Skipping repository clone. You'll need to upload your code manually."
fi

# Create .env file template
log_info "Creating .env file..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Application Settings
HOST=0.0.0.0
PORT=8000
DEBUG=False
ENVIRONMENT=production

# CORS (Update with your frontend URL)
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key

# Database
DATABASE_URL=postgresql://postgres:password@db.supabase.co:5432/postgres

# Redis (Upstash or local)
REDIS_URL=redis://localhost:6379

# Twilio
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=AI Cruel Deadline Manager

# Security
SECRET_KEY=change-this-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
EOF
    log_warn "Please edit /var/www/ai-cruel-backend/.env with your credentials"
    log_warn "Run: nano /var/www/ai-cruel-backend/.env"
else
    log_info ".env file already exists"
fi

# Create docker-compose.yml if not exists
log_info "Creating docker-compose.yml..."
if [ ! -f "docker-compose.yml" ]; then
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    build: .
    container_name: ai-cruel-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    networks:
      - ai-cruel-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Local Redis (if not using Upstash)
  # redis:
  #   image: redis:7-alpine
  #   container_name: ai-cruel-redis
  #   restart: unless-stopped
  #   ports:
  #     - "6379:6379"
  #   volumes:
  #     - redis-data:/data
  #   networks:
  #     - ai-cruel-network

networks:
  ai-cruel-network:
    driver: bridge

volumes:
  redis-data:
EOF
    log_info "docker-compose.yml created"
fi

# Configure Nginx reverse proxy
log_info "Configuring Nginx..."
cat > /etc/nginx/sites-available/ai-cruel << 'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/ai-cruel-access.log;
    error_log /var/log/nginx/ai-cruel-error.log;

    # Backend proxy
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if any)
    location /static/ {
        alias /var/www/ai-cruel-backend/static/;
        expires 30d;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/ai-cruel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t
systemctl reload nginx

log_info "Nginx configured successfully"

# Create deployment script
log_info "Creating deployment script..."
cat > /var/www/ai-cruel-backend/deploy.sh << 'EOF'
#!/bin/bash

echo "Deploying AI Cruel Backend..."

# Navigate to project directory
cd /var/www/ai-cruel-backend

# Pull latest code (if using git)
if [ -d ".git" ]; then
    echo "Pulling latest code..."
    git pull origin main
fi

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down

# Rebuild images
echo "Building Docker images..."
docker-compose build --no-cache

# Start containers
echo "Starting containers..."
docker-compose up -d

# Show logs
echo "Deployment complete! Checking logs..."
sleep 5
docker-compose logs --tail=50

echo ""
echo "Backend is running at http://$(hostname -I | awk '{print $1}'):8000"
echo "View logs: docker-compose logs -f"
echo "Check status: docker-compose ps"
EOF

chmod +x /var/www/ai-cruel-backend/deploy.sh

# Create systemd service for auto-start
log_info "Creating systemd service..."
cat > /etc/systemd/system/ai-cruel-backend.service << EOF
[Unit]
Description=AI Cruel Backend Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/var/www/ai-cruel-backend
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-cruel-backend.service

# Create update script
cat > /root/update-backend.sh << 'EOF'
#!/bin/bash
cd /var/www/ai-cruel-backend
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo "Backend updated successfully!"
EOF

chmod +x /root/update-backend.sh

# Print summary
echo ""
echo "=========================================="
log_info "Droplet Setup Complete! ✅"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Edit environment variables:"
echo "   nano /var/www/ai-cruel-backend/.env"
echo ""
echo "2. Deploy the application:"
echo "   cd /var/www/ai-cruel-backend"
echo "   ./deploy.sh"
echo ""
echo "3. (Optional) Set up SSL with Let's Encrypt:"
echo "   apt install certbot python3-certbot-nginx -y"
echo "   certbot --nginx -d your-domain.com"
echo ""
echo "4. View application logs:"
echo "   docker-compose logs -f"
echo ""
echo "5. Check running containers:"
echo "   docker-compose ps"
echo ""
echo "📍 Your backend will be available at:"
echo "   http://$(hostname -I | awk '{print $1}')"
echo ""
echo "🔧 Useful Commands:"
echo "   - Update backend: /root/update-backend.sh"
echo "   - Restart: cd /var/www/ai-cruel-backend && docker-compose restart"
echo "   - Stop: docker-compose down"
echo "   - View logs: docker-compose logs -f"
echo ""
echo "🔒 Security Recommendations:"
echo "   - Change SSH port: nano /etc/ssh/sshd_config"
echo "   - Set up fail2ban: apt install fail2ban -y"
echo "   - Enable automatic updates: apt install unattended-upgrades -y"
echo ""
echo "=========================================="
log_info "Happy deploying! 🚀"
echo "=========================================="
