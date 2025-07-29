# 🚀 Ingrid MVP - Food Scanning App

Clean eating made simple. Scan food products and get ingredient analysis with traffic light ratings.

## 🌟 Features

- 📱 **Mobile-First Design** - PWA with offline support
- 📷 **Barcode Scanning** - Camera + manual entry
- 🖼️ **Photo OCR** - Extract ingredients from photos  
- 🚦 **Traffic Light Rating** - Green/Amber/Red health ratings
- 💾 **Bookmarking** - Save favorite products
- 📊 **USDA Integration** - Authoritative food data
- 🔒 **Privacy-First** - Anonymous session tracking

## 🚀 Quick Deploy

### Backend (Railway)
1. Connect this repo to Railway
2. Add environment variables (see `.env.example`)
3. Deploy with included Dockerfile

### Frontend (Netlify)  
1. Deploy `frontend/build` folder to Netlify
2. Use included `netlify.toml` configuration
3. Add custom domain

## 🔧 Environment Variables

Copy `.env.example` to `.env` and update:

```
MONGO_URL=your_mongodb_connection_string
USDA_FDC_API_KEY=your_usda_fdc_key
USDA_ORGANIC_API_KEY=your_usda_organic_key
```

## 🎯 Tech Stack

- **Frontend:** React 19, Tailwind CSS, PWA
- **Backend:** FastAPI, Python 3.11
- **Database:** MongoDB Atlas
- **Deployment:** Railway + Netlify
- **APIs:** USDA FoodData Central, USDA Organic, OpenFoodFacts

## 📱 Mobile App

- Progressive Web App (PWA) ready
- Install on mobile home screen
- Offline functionality with service worker
- Camera access for barcode scanning

## 🏃‍♂️ Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --reload

# Frontend  
cd frontend
yarn install
yarn start
```

## 📄 License

MIT License - Built for clean eating and healthier food choices!

---

🌟 **Help people make better food choices with Ingrid!**