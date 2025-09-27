#!/bin/bash

# IRCTC Tatkal Automation Bot - AWS Deployment Script
# This script deploys the bot to AWS EC2 Mumbai region for optimal performance

set -e

echo "🚀 IRCTC Tatkal Bot - AWS Deployment Script"
echo "==========================================="

# Configuration
AWS_REGION="ap-south-1"  # Mumbai region for lowest latency to IRCTC
INSTANCE_TYPE="t3.medium"  # Good balance of CPU and memory
KEY_NAME="irctc-bot-key"
SECURITY_GROUP_NAME="irctc-bot-sg"
AMI_ID="ami-0f58b397bc5c1f2e8"  # Ubuntu 22.04 LTS in Mumbai region

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install AWS CLI first."
        echo "Installation instructions: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check if we're in the project directory
    if [ ! -f "run.py" ] || [ ! -f "requirements.txt" ]; then
        print_error "Please run this script from the project root directory."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Create EC2 key pair
create_key_pair() {
    print_status "Creating EC2 key pair..."
    
    if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$AWS_REGION" &> /dev/null; then
        print_warning "Key pair '$KEY_NAME' already exists. Skipping creation."
    else
        aws ec2 create-key-pair \
            --key-name "$KEY_NAME" \
            --region "$AWS_REGION" \
            --query 'KeyMaterial' \
            --output text > "${KEY_NAME}.pem"
        
        chmod 400 "${KEY_NAME}.pem"
        print_success "Key pair created and saved as ${KEY_NAME}.pem"
    fi
}

# Create security group
create_security_group() {
    print_status "Creating security group..."
    
    # Check if security group exists
    if aws ec2 describe-security-groups --group-names "$SECURITY_GROUP_NAME" --region "$AWS_REGION" &> /dev/null; then
        print_warning "Security group '$SECURITY_GROUP_NAME' already exists. Skipping creation."
        return
    fi
    
    # Create security group
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
        --group-name "$SECURITY_GROUP_NAME" \
        --description "Security group for IRCTC Tatkal Bot" \
        --region "$AWS_REGION" \
        --query 'GroupId' \
        --output text)
    
    # Add rules
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region "$AWS_REGION"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region "$AWS_REGION"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --region "$AWS_REGION"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 5000 \
        --cidr 0.0.0.0/0 \
        --region "$AWS_REGION"
    
    print_success "Security group created: $SECURITY_GROUP_ID"
}

# Launch EC2 instance
launch_instance() {
    print_status "Launching EC2 instance..."
    
    # Create user data script
    cat > user-data.sh << 'EOF'
#!/bin/bash
set -e

# Update system
apt-get update -y
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install other tools
apt-get install -y git nginx certbot python3-certbot-nginx htop curl wget unzip

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Install Node.js (for frontend build tools if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Create application directory
mkdir -p /opt/irctc-bot
chown ubuntu:ubuntu /opt/irctc-bot

# Set timezone to IST
timedatectl set-timezone Asia/Kolkata

# Install NTP for accurate time synchronization
apt-get install -y ntp
systemctl enable ntp
systemctl start ntp

# Configure firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp
ufw --force enable

echo "EC2 instance setup completed" > /var/log/setup-complete.log
EOF

    # Launch instance
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id "$AMI_ID" \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --security-groups "$SECURITY_GROUP_NAME" \
        --user-data file://user-data.sh \
        --region "$AWS_REGION" \
        --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=IRCTC-Tatkal-Bot}]' \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    print_success "Instance launched: $INSTANCE_ID"
    
    # Wait for instance to be running
    print_status "Waiting for instance to be running..."
    aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"
    
    # Get instance public IP
    PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --region "$AWS_REGION" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    print_success "Instance is running. Public IP: $PUBLIC_IP"
    
    # Save instance details
    cat > instance-details.txt << EOF
Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP
Region: $AWS_REGION
Key File: ${KEY_NAME}.pem

SSH Command:
ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP

Application URL (after deployment):
http://$PUBLIC_IP:5000
EOF
    
    echo "$INSTANCE_ID" > instance-id.txt
    echo "$PUBLIC_IP" > public-ip.txt
    
    # Clean up
    rm -f user-data.sh
}

# Deploy application
deploy_application() {
    local PUBLIC_IP=$(cat public-ip.txt)
    
    print_status "Waiting for instance to be fully ready..."
    sleep 60  # Give the instance time to complete user-data script
    
    print_status "Deploying application to $PUBLIC_IP..."
    
    # Wait for SSH to be ready
    print_status "Waiting for SSH access..."
    for i in {1..30}; do
        if ssh -i "${KEY_NAME}.pem" -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@"$PUBLIC_IP" exit &> /dev/null; then
            break
        fi
        print_status "SSH not ready yet, waiting... ($i/30)"
        sleep 10
    done
    
    # Create deployment package
    print_status "Creating deployment package..."
    tar -czf irctc-bot-deploy.tar.gz \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='logs' \
        --exclude='temp' \
        --exclude='*.pem' \
        --exclude='instance-*.txt' \
        --exclude='irctc-bot-deploy.tar.gz' \
        .
    
    # Upload files
    print_status "Uploading application files..."
    scp -i "${KEY_NAME}.pem" -o StrictHostKeyChecking=no \
        irctc-bot-deploy.tar.gz ubuntu@"$PUBLIC_IP":/opt/irctc-bot/
    
    # Deploy on server
    print_status "Setting up application on server..."
    ssh -i "${KEY_NAME}.pem" -o StrictHostKeyChecking=no ubuntu@"$PUBLIC_IP" << 'EOF'
set -e

cd /opt/irctc-bot

# Extract application
tar -xzf irctc-bot-deploy.tar.gz
rm irctc-bot-deploy.tar.gz

# Create environment file
cp .env.example .env

# Generate secure keys
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Update .env file
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
sed -i "s/DEBUG=.*/DEBUG=False/" .env
sed -i "s/ENVIRONMENT=.*/ENVIRONMENT=production/" .env

# Create required directories
mkdir -p logs temp config

# Start the application with Docker Compose
docker-compose up -d

# Wait for application to start
sleep 30

# Check if application is running
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ Application is running successfully!"
else
    echo "❌ Application failed to start. Checking logs..."
    docker-compose logs --tail=50
fi

EOF
    
    # Clean up
    rm -f irctc-bot-deploy.tar.gz
    
    print_success "Application deployed successfully!"
}

# Setup SSL certificate (optional)
setup_ssl() {
    local PUBLIC_IP=$(cat public-ip.txt)
    local DOMAIN=$1
    
    if [ -z "$DOMAIN" ]; then
        print_warning "No domain provided, skipping SSL setup"
        return
    fi
    
    print_status "Setting up SSL certificate for $DOMAIN..."
    
    ssh -i "${KEY_NAME}.pem" -o StrictHostKeyChecking=no ubuntu@"$PUBLIC_IP" << EOF
# Setup Nginx reverse proxy
cat > /etc/nginx/sites-available/irctc-bot << 'NGINX_CONFIG'
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINX_CONFIG

# Enable site
ln -sf /etc/nginx/sites-available/irctc-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Setup SSL with Let's Encrypt
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN --redirect

EOF
    
    print_success "SSL certificate setup completed for $DOMAIN"
}

# Main deployment function
main() {
    print_status "Starting AWS deployment for IRCTC Tatkal Bot"
    echo "Region: $AWS_REGION"
    echo "Instance Type: $INSTANCE_TYPE"
    echo ""
    
    # Run deployment steps
    check_prerequisites
    create_key_pair
    create_security_group
    launch_instance
    deploy_application
    
    # Get final details
    local PUBLIC_IP=$(cat public-ip.txt)
    local INSTANCE_ID=$(cat instance-id.txt)
    
    # Print success message
    print_success "Deployment completed successfully!"
    echo ""
    echo "📋 Deployment Details:"
    echo "====================="
    echo "Instance ID: $INSTANCE_ID"
    echo "Public IP: $PUBLIC_IP"
    echo "Region: $AWS_REGION"
    echo "SSH Key: ${KEY_NAME}.pem"
    echo ""
    echo "🌐 Access URLs:"
    echo "=============="
    echo "Application: http://$PUBLIC_IP:5000"
    echo "Health Check: http://$PUBLIC_IP:5000/api/health"
    echo ""
    echo "🔐 SSH Access:"
    echo "============="
    echo "ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
    echo ""
    echo "📝 Next Steps:"
    echo "============="
    echo "1. Wait 2-3 minutes for the application to fully start"
    echo "2. Access the web interface at http://$PUBLIC_IP:5000"
    echo "3. Configure your booking preferences"
    echo "4. (Optional) Setup a domain and SSL certificate"
    echo ""
    echo "🛠️ Management Commands:"
    echo "======================"
    echo "View logs: ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP 'cd /opt/irctc-bot && docker-compose logs'"
    echo "Restart app: ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP 'cd /opt/irctc-bot && docker-compose restart'"
    echo "Stop app: ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP 'cd /opt/irctc-bot && docker-compose down'"
    echo ""
    
    # Ask about SSL setup
    echo "💡 Optional: Setup domain and SSL certificate"
    read -p "Do you have a domain name to setup SSL? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your domain name (e.g., bot.yourdomain.com): " DOMAIN
        if [ ! -z "$DOMAIN" ]; then
            echo "⚠️  Make sure your domain '$DOMAIN' points to IP: $PUBLIC_IP"
            read -p "Press Enter when DNS is ready, or Ctrl+C to skip..."
            setup_ssl "$DOMAIN"
        fi
    fi
    
    print_success "🎉 IRCTC Tatkal Bot is now deployed and ready to use!"
    echo ""
    echo "⚠️  Important Security Notes:"
    echo "- Keep your ${KEY_NAME}.pem file secure"
    echo "- The application is accessible from the internet"
    echo "- Monitor your AWS usage and costs"
    echo "- Regularly update the system and application"
}

# Handle script interruption
trap 'print_error "Deployment interrupted. Cleaning up..."; exit 1' INT TERM

# Run main function
main "$@"