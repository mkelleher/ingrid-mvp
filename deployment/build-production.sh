#!/bin/bash
# Production Build Script for Ingrid MVP

echo "🚀 Building Ingrid MVP for Production Deployment..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
cd /app
rm -rf deployment/build
rm -rf frontend/build

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
yarn install --production

# Build frontend for production
echo "🏗️ Building frontend..."
export REACT_APP_BACKEND_URL="https://ingrid-backend-production.railway.app"
yarn build

# Copy build to deployment folder
echo "📁 Copying build files..."
cp -r build ../deployment/
cp -r public/sw.js ../deployment/build/
cp -r public/manifest.json ../deployment/build/

# Copy configuration files
cd ../deployment
cp netlify.toml build/

echo "✅ Frontend build completed!"
echo "📦 Build files ready in /app/deployment/build/"

# Prepare backend for Railway
echo "🖥️ Preparing backend for Railway..."
cd /app
cp -r backend deployment/backend
cp deployment/Dockerfile deployment/
cp deployment/railway.json deployment/

echo "✅ Backend files prepared!"

# Generate deployment package
echo "📦 Creating deployment package..."
cd deployment
tar -czf ingrid-deployment.tar.gz build/ backend/ Dockerfile railway.json netlify.toml .env.production

echo "🎉 Deployment package created: ingrid-deployment.tar.gz"
echo ""
echo "Next steps:"
echo "1. Deploy backend to Railway using Dockerfile"
echo "2. Deploy frontend build/ folder to Netlify"  
echo "3. Configure custom domain www.useingrid.com"
echo "4. Set up MongoDB Atlas connection"
echo ""
echo "🚀 Ready for production deployment!"