#!/bin/bash

#############################################
# Quick Droplet Creation with doctl
#############################################
# This script creates a Digital Ocean Droplet
# and runs the setup script automatically
#############################################

set -e

echo "=========================================="
echo "Create Digital Ocean Droplet"
echo "=========================================="
echo ""

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "❌ doctl is not installed"
    echo ""
    echo "Install it with:"
    echo "  macOS: brew install doctl"
    echo "  Linux: snap install doctl"
    echo "  Manual: https://docs.digitalocean.com/reference/doctl/how-to/install/"
    echo ""
    exit 1
fi

# Check if authenticated
if ! doctl account get &> /dev/null; then
    echo "❌ Not authenticated with Digital Ocean"
    echo ""
    echo "Run: doctl auth init"
    echo "Then enter your API token from: https://cloud.digitalocean.com/account/api/tokens"
    echo ""
    exit 1
fi

echo "✅ doctl is installed and authenticated"
echo ""

# Configuration
echo "📝 Droplet Configuration:"
echo ""

# Get available regions
echo "Available regions (closest to you):"
doctl compute region list --format Slug,Name,Available | grep true | head -5
echo ""

read -p "Enter region (default: nyc1): " REGION
REGION=${REGION:-nyc1}

# Droplet size
echo ""
echo "Available sizes:"
echo "  s-1vcpu-512mb-10gb  - $4/month  - 512MB RAM, 1 vCPU, 10GB SSD"
echo "  s-1vcpu-1gb         - $6/month  - 1GB RAM, 1 vCPU, 25GB SSD (recommended)"
echo "  s-1vcpu-2gb         - $12/month - 2GB RAM, 1 vCPU, 50GB SSD"
echo "  s-2vcpu-2gb         - $18/month - 2GB RAM, 2 vCPU, 60GB SSD"
echo ""

read -p "Enter size (default: s-1vcpu-1gb): " SIZE
SIZE=${SIZE:-s-1vcpu-1gb}

# Droplet name
read -p "Enter droplet name (default: ai-cruel-backend): " NAME
NAME=${NAME:-ai-cruel-backend}

# SSH key
echo ""
echo "Available SSH keys:"
doctl compute ssh-key list --format ID,Name
echo ""
read -p "Enter SSH key ID (or press Enter to create without key): " SSH_KEY_ID

# Confirm
echo ""
echo "=========================================="
echo "Creating Droplet with:"
echo "  Name: $NAME"
echo "  Region: $REGION"
echo "  Size: $SIZE"
echo "  OS: Ubuntu 22.04 LTS"
if [ -n "$SSH_KEY_ID" ]; then
    echo "  SSH Key: $SSH_KEY_ID"
fi
echo "=========================================="
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 1
fi

# Create droplet
echo ""
echo "Creating droplet..."

if [ -n "$SSH_KEY_ID" ]; then
    DROPLET_ID=$(doctl compute droplet create "$NAME" \
        --region "$REGION" \
        --size "$SIZE" \
        --image ubuntu-22-04-x64 \
        --ssh-keys "$SSH_KEY_ID" \
        --wait \
        --format ID \
        --no-header)
else
    DROPLET_ID=$(doctl compute droplet create "$NAME" \
        --region "$REGION" \
        --size "$SIZE" \
        --image ubuntu-22-04-x64 \
        --wait \
        --format ID \
        --no-header)
fi

echo "✅ Droplet created with ID: $DROPLET_ID"

# Get droplet IP
sleep 5
DROPLET_IP=$(doctl compute droplet get "$DROPLET_ID" --format PublicIPv4 --no-header)

echo "✅ Droplet IP: $DROPLET_IP"
echo ""

# Wait for SSH to be ready
echo "Waiting for SSH to be ready..."
for i in {1..30}; do
    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@$DROPLET_IP "echo 'SSH ready'" &> /dev/null; then
        echo "✅ SSH is ready"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 10
done

# Upload setup script
echo ""
echo "Uploading setup script..."
scp -o StrictHostKeyChecking=no deploy/setup-droplet.sh root@$DROPLET_IP:/root/

# Run setup script
echo ""
echo "Running setup script..."
echo "This may take 5-10 minutes..."
echo ""

ssh -o StrictHostKeyChecking=no root@$DROPLET_IP "bash /root/setup-droplet.sh"

# Print success message
echo ""
echo "=========================================="
echo "✅ Droplet Setup Complete!"
echo "=========================================="
echo ""
echo "🌐 Your Droplet:"
echo "   IP Address: $DROPLET_IP"
echo "   SSH: ssh root@$DROPLET_IP"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. SSH into your droplet:"
echo "   ssh root@$DROPLET_IP"
echo ""
echo "2. Edit environment variables:"
echo "   nano /var/www/ai-cruel-backend/.env"
echo ""
echo "3. Deploy the application:"
echo "   cd /var/www/ai-cruel-backend"
echo "   ./deploy.sh"
echo ""
echo "4. Access your API:"
echo "   http://$DROPLET_IP"
echo "   http://$DROPLET_IP/docs"
echo "   http://$DROPLET_IP/health"
echo ""
echo "5. (Optional) Set up domain and SSL:"
echo "   - Point your domain A record to: $DROPLET_IP"
echo "   - Run: certbot --nginx -d yourdomain.com"
echo ""
echo "=========================================="
echo "📚 Documentation: ./backend/DIGITAL_OCEAN_DEPLOYMENT.md"
echo "=========================================="
