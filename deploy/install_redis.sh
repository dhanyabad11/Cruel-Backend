#!/bin/bash
# Install and configure Redis on your Digital Ocean droplet
# Run this on your droplet: ssh root@198.211.106.97 < install_redis.sh

set -e

echo "🚀 Installing Redis on your Digital Ocean droplet..."
echo "=================================================="

# Update system
echo "📦 Updating system packages..."
apt-get update -qq

# Install Redis
echo "📦 Installing Redis Server..."
apt-get install -y redis-server

# Configure Redis for production
echo "⚙️  Configuring Redis..."

# Backup original config
cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# Set password
REDIS_PASSWORD=$(openssl rand -base64 32)
echo "requirepass $REDIS_PASSWORD" >> /etc/redis/redis.conf

# Allow connections from localhost only (secure)
sed -i 's/bind 127.0.0.1 ::1/bind 127.0.0.1/' /etc/redis/redis.conf

# Enable as system service
echo "🔧 Enabling Redis service..."
systemctl enable redis-server
systemctl restart redis-server

# Check if Redis is running
if systemctl is-active --quiet redis-server; then
    echo "✅ Redis is running!"
else
    echo "❌ Redis failed to start"
    exit 1
fi

# Test Redis connection
redis-cli -a "$REDIS_PASSWORD" ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Redis connection test successful!"
else
    echo "❌ Redis connection test failed"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ Redis Installation Complete!"
echo "=================================================="
echo ""
echo "📋 Your Redis Connection Details:"
echo "   REDIS_URL=redis://:$REDIS_PASSWORD@127.0.0.1:6379/0"
echo ""
echo "📝 Next Steps:"
echo "1. Copy the REDIS_URL above"
echo "2. Update your .env file on the droplet:"
echo "   nano /root/ai-cruel-backend/.env"
echo "   Update the REDIS_URL line"
echo "3. Restart your services:"
echo "   pm2 restart all"
echo "   # OR"
echo "   systemctl restart ai-cruel-backend"
echo ""
echo "💾 Password saved to: /root/redis_password.txt"
echo "$REDIS_PASSWORD" > /root/redis_password.txt

echo ""
echo "🎉 Done! Your Redis is now running locally on your droplet (FREE!)"
