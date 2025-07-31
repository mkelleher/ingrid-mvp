# Railway Deployment Fix

## Issue Resolved
Railway's Nixpacks was unable to generate a build plan because the required configuration files were in the `deployment/` directory instead of the root directory.

## Files Moved to Root Directory
- ✅ `Dockerfile` - Container configuration for Python backend
- ✅ `railway.json` - Railway-specific deployment configuration

## Deployment Instructions

### Option 1: Deploy from Current Repository
1. Connect your Railway project to this repository
2. Railway will now detect the `Dockerfile` and `railway.json` in the root directory
3. The build should proceed automatically

### Option 2: Manual Deployment (if needed)
1. Ensure these environment variables are set in Railway:
   - `MONGO_URL` - MongoDB connection string
   - `DB_NAME` - Database name
   - `USDA_FDC_API_KEY` - USDA FoodData Central API key
   - `USDA_ORGANIC_API_KEY` - USDA Organic Integrity API key

2. The Dockerfile will:
   - Use Python 3.11 slim image
   - Install system dependencies (tesseract-ocr, OpenCV dependencies)
   - Install Python packages from requirements.txt
   - Expose port 8001
   - Start the FastAPI server with Uvicorn

## Verification
After deployment, verify the API is working by checking:
- `https://your-railway-url.up.railway.app/api/` - Should return API status message
- Health check endpoints should respond correctly

## Current Status
- ✅ Dockerfile configured for Railway deployment  
- ✅ All dependencies included in requirements.txt
- ✅ System dependencies for OCR/image processing included
- ✅ Port 8001 properly exposed
- ✅ Environment variables configured for MongoDB and APIs