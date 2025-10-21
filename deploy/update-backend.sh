#!/bin/bash

# Update Backend on Digital Ocean Droplet
# Usage: ./update-backend.sh

set -e

DROPLET_IP="198.211.106.97"
APP_DIR="/var/www/ai-cruel-backend"

echo "🚀 Updating AI Cruel Backend on Digital Ocean..."
echo ""

# SSH into droplet and update
ssh root@${DROPLET_IP} << 'ENDSSH'
    cd /var/www/ai-cruel-backend
    
    echo "📥 Pulling latest code from GitHub..."
    git pull origin main
    
    echo "🛑 Stopping containers..."
    docker-compose down
    
    echo "🔨 Building new images..."
    docker-compose build
    
    echo "🚀 Starting containers..."
    docker-compose up -d
    
    echo "✅ Deployment complete!"
    echo ""
    echo "📊 Container status:"
    docker-compose ps
    
    echo ""
    echo "📋 Recent logs:"
    docker-compose logs --tail=20
ENDSSH

echo ""
echo "✨ Backend updated successfully!"
echo "🌐 Backend URL: http://${DROPLET_IP}"
echo ""
echo "To check logs: ssh root@${DROPLET_IP} 'cd ${APP_DIR} && docker-compose logs -f'"
