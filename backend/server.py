from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import httpx
import json
import re
import base64
from PIL import Image
import io
import easyocr

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Ingrid MVP API", description="Food scanning and ingredient analysis API")

# Create API router
api_router = APIRouter(prefix="/api")

# Initialize OCR reader
ocr_reader = easyocr.Reader(['en'])

# Pydantic Models
class ProductInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    barcode: Optional[str] = None
    name: str
    brand: Optional[str] = None
    ingredients: List[str]
    ingredient_count: int
    rating: str  # "green", "amber", "red"
    certifications: List[str] = []
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ScanRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    product_id: str
    scan_type: str  # "barcode" or "ocr"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BookmarkRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    product_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BarcodeRequest(BaseModel):
    barcode: str
    session_id: str

class OCRRequest(BaseModel):
    session_id: str

class AnalysisResult(BaseModel):
    product: ProductInfo
    is_bookmarked: bool = False

# Helper Functions
def calculate_rating(ingredient_count: int) -> str:
    """Calculate traffic light rating based on ingredient count"""
    if ingredient_count <= 4:
        return "green"
    elif ingredient_count <= 9:
        return "amber"
    else:
        return "red"

def extract_ingredients_from_text(text: str) -> List[str]:
    """Extract ingredients from OCR text"""
    # Common patterns for ingredient lists
    text = text.lower()
    
    # Look for ingredients section
    patterns = [
        r'ingredients?[:\s]+(.*?)(?=\n|$|allergen|nutrition|contains)',
        r'ingredientes?[:\s]+(.*?)(?=\n|$|alérgeno|nutrición|contiene)',
        r'ingrédients?[:\s]+(.*?)(?=\n|$|allergène|nutrition|contient)'
    ]
    
    ingredients_text = ""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            ingredients_text = match.group(1)
            break
    
    if not ingredients_text:
        # Fallback: assume the longest line contains ingredients
        lines = text.split('\n')
        ingredients_text = max(lines, key=len) if lines else ""
    
    # Clean and split ingredients
    ingredients_text = re.sub(r'[()[\]{}]', '', ingredients_text)
    ingredients = [ing.strip() for ing in re.split(r'[,;]', ingredients_text) if ing.strip()]
    
    # Count sub-ingredients (those in parentheses in original text)
    sub_ingredients_pattern = r'\(([^)]+)\)'
    sub_matches = re.findall(sub_ingredients_pattern, text)
    for sub_match in sub_matches:
        sub_ingredients = [ing.strip() for ing in re.split(r'[,;]', sub_match) if ing.strip()]
        ingredients.extend(sub_ingredients)
    
    return ingredients[:50]  # Limit to reasonable number

def detect_certifications(text: str) -> List[str]:
    """Detect organic and non-GMO certifications"""
    text = text.lower()
    certifications = []
    
    organic_patterns = ['organic', 'bio', 'orgánico', 'biologique', 'usda organic']
    non_gmo_patterns = ['non-gmo', 'non gmo', 'without gmo', 'gmo free', 'sin ogm']
    
    for pattern in organic_patterns:
        if pattern in text:
            certifications.append("Organic")
            break
    
    for pattern in non_gmo_patterns:
        if pattern in text:
            certifications.append("Non-GMO")
            break
    
    return certifications

async def enhanced_certification_detection(product_name: str, brand: str = None, text: str = "") -> List[str]:
    """Enhanced certification detection using USDA API and text analysis"""
    certifications = []
    
    # First, check USDA Organic Integrity Database
    try:
        usda_certs = await lookup_usda_organic_certification(product_name, brand)
        certifications.extend(usda_certs)
    except Exception as e:
        logger.warning(f"USDA API check failed: {e}")
    
    # Then, check text-based certifications
    text_certs = detect_certifications(text)
    
    # Merge certifications, avoiding duplicates
    for cert in text_certs:
        if cert not in certifications:
            # If USDA API found "USDA Organic", don't add generic "Organic"
            if cert == "Organic" and "USDA Organic" in certifications:
                continue
            certifications.append(cert)
    
    return certifications

async def lookup_usda_organic_certification(product_name: str, brand: str = None) -> List[str]:
    """Check USDA Organic Integrity Database for organic certification"""
    try:
        usda_api_key = os.environ.get('USDA_ORGANIC_API_KEY')
        if not usda_api_key:
            return []
        
        # USDA Organic Integrity Database API endpoint
        base_url = "https://organic.ams.usda.gov/integrity/api/search"
        
        # Search parameters
        search_terms = [product_name]
        if brand:
            search_terms.append(brand)
        
        certifications = []
        
        for term in search_terms:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        base_url,
                        params={
                            "q": term,
                            "api_key": usda_api_key,
                            "limit": 10
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Check if any results indicate organic certification
                        if "results" in data and data["results"]:
                            for result in data["results"]:
                                # Look for organic certification indicators
                                if any(keyword in str(result).lower() for keyword in 
                                      ['organic', 'certified organic', 'usda organic']):
                                    if "USDA Organic" not in certifications:
                                        certifications.append("USDA Organic")
                                    break
                    
            except Exception as e:
                logger.warning(f"USDA API request failed for term '{term}': {e}")
                continue
        
        return certifications
        
    except Exception as e:
        logger.error(f"Error checking USDA organic certification: {e}")
        return []

async def lookup_product_by_barcode(barcode: str) -> Optional[Dict[str, Any]]:
    """Lookup product information by barcode using external API"""
    # Try OpenFoodFacts first (free API)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:
                    product = data.get("product", {})
                    ingredients_text = product.get("ingredients_text", "")
                    
                    # Parse ingredients
                    ingredients = []
                    if ingredients_text:
                        ingredients = [ing.strip() for ing in re.split(r'[,;]', ingredients_text) if ing.strip()]
                    
                    return {
                        "name": product.get("product_name", "Unknown Product"),
                        "brand": product.get("brands", "").split(",")[0] if product.get("brands") else None,
                        "ingredients": ingredients,
                        "image_url": product.get("image_url"),
                        "ingredients_text": ingredients_text,
                        "labels": product.get("labels", "")
                    }
    except Exception as e:
        logger.error(f"Error looking up barcode {barcode}: {e}")
    
    return None

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Ingrid MVP API - Ready to scan!"}

@api_router.post("/scan/barcode", response_model=AnalysisResult)
async def scan_barcode(request: BarcodeRequest):
    """Scan product by barcode"""
    try:
        # Lookup product info
        product_info = await lookup_product_by_barcode(request.barcode)
        
        if not product_info:
            # Create basic product info if lookup fails
            product_info = {
                "name": f"Product {request.barcode}",
                "brand": None,
                "ingredients": [],
                "image_url": None,
                "ingredients_text": "",
                "labels": ""
            }
        
        # Enhanced certification detection using USDA API
        certifications = await enhanced_certification_detection(
            product_name=product_info["name"],
            brand=product_info["brand"],
            text=product_info.get("ingredients_text", "") + " " + product_info.get("labels", "")
        )
        
        # Create product record
        ingredient_count = len(product_info["ingredients"])
        rating = calculate_rating(ingredient_count)
        
        product = ProductInfo(
            barcode=request.barcode,
            name=product_info["name"],
            brand=product_info["brand"],
            ingredients=product_info["ingredients"],
            ingredient_count=ingredient_count,
            rating=rating,
            certifications=product_info["certifications"],
            image_url=product_info["image_url"]
        )
        
        # Save product to database
        await db.products.insert_one(product.dict())
        
        # Record scan
        scan_record = ScanRecord(
            session_id=request.session_id,
            product_id=product.id,
            scan_type="barcode"
        )
        await db.scans.insert_one(scan_record.dict())
        
        # Check if bookmarked
        bookmark = await db.bookmarks.find_one({
            "session_id": request.session_id,
            "product_id": product.id
        })
        
        return AnalysisResult(
            product=product,
            is_bookmarked=bookmark is not None
        )
        
    except Exception as e:
        logger.error(f"Error scanning barcode: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan barcode")

@api_router.post("/scan/ocr", response_model=AnalysisResult)
async def scan_ocr(session_id: str = Form(...), image: UploadFile = File(...)):
    """Scan product by OCR from image"""
    try:
        # Read and process image
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Perform OCR
        results = ocr_reader.readtext(image_data)
        text = " ".join([result[1] for result in results])
        
        # Extract ingredients and certifications
        ingredients = extract_ingredients_from_text(text)
        certifications = detect_certifications(text)
        
        # Create product record
        ingredient_count = len(ingredients)
        rating = calculate_rating(ingredient_count)
        
        product = ProductInfo(
            name="OCR Scanned Product",
            ingredients=ingredients,
            ingredient_count=ingredient_count,
            rating=rating,
            certifications=certifications
        )
        
        # Save product to database
        await db.products.insert_one(product.dict())
        
        # Record scan
        scan_record = ScanRecord(
            session_id=session_id,
            product_id=product.id,
            scan_type="ocr"
        )
        await db.scans.insert_one(scan_record.dict())
        
        # Check if bookmarked
        bookmark = await db.bookmarks.find_one({
            "session_id": session_id,
            "product_id": product.id
        })
        
        return AnalysisResult(
            product=product,
            is_bookmarked=bookmark is not None
        )
        
    except Exception as e:
        logger.error(f"Error processing OCR: {e}")
        raise HTTPException(status_code=500, detail="Failed to process image")

@api_router.post("/bookmarks/toggle")
async def toggle_bookmark(session_id: str, product_id: str):
    """Toggle bookmark status for a product"""
    try:
        # Check if already bookmarked
        existing = await db.bookmarks.find_one({
            "session_id": session_id,
            "product_id": product_id
        })
        
        if existing:
            # Remove bookmark
            await db.bookmarks.delete_one({"id": existing["id"]})
            return {"bookmarked": False, "message": "Bookmark removed"}
        else:
            # Add bookmark
            bookmark = BookmarkRecord(
                session_id=session_id,
                product_id=product_id
            )
            await db.bookmarks.insert_one(bookmark.dict())
            return {"bookmarked": True, "message": "Bookmark added"}
            
    except Exception as e:
        logger.error(f"Error toggling bookmark: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle bookmark")

@api_router.get("/history/{session_id}", response_model=List[AnalysisResult])
async def get_scan_history(session_id: str):
    """Get scan history for a session"""
    try:
        # Get scan records
        scans = await db.scans.find({"session_id": session_id}).sort("timestamp", -1).to_list(100)
        
        results = []
        for scan in scans:
            # Get product info
            product = await db.products.find_one({"id": scan["product_id"]})
            if product:
                # Check if bookmarked
                bookmark = await db.bookmarks.find_one({
                    "session_id": session_id,
                    "product_id": scan["product_id"]
                })
                
                results.append(AnalysisResult(
                    product=ProductInfo(**product),
                    is_bookmarked=bookmark is not None
                ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get history")

@api_router.get("/bookmarks/{session_id}", response_model=List[AnalysisResult])
async def get_bookmarks(session_id: str):
    """Get bookmarked products for a session"""
    try:
        # Get bookmark records
        bookmarks = await db.bookmarks.find({"session_id": session_id}).sort("timestamp", -1).to_list(100)
        
        results = []
        for bookmark in bookmarks:
            # Get product info
            product = await db.products.find_one({"id": bookmark["product_id"]})
            if product:
                results.append(AnalysisResult(
                    product=ProductInfo(**product),
                    is_bookmarked=True
                ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting bookmarks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bookmarks")

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()