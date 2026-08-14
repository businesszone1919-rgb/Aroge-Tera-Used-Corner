import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(title="Aroge Tera Mini App API")

# CORS ፈቃድ (ከ Telegram Mini App ለሚመጡ ጥሪዎች)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase ቁልፎችን ከ Environment መውሰድ
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase connection error: {e}")


# --- Pydantic Data Models ---

class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    price: float
    category_id: Optional[int] = None
    condition: Optional[str] = "በጣም ጥሩ"
    images: Optional[List[str]] = []
    seller_telegram_id: Optional[str] = "guest"
    seller_phone: Optional[str] = None


# --- API Endpoints ---

@app.get("/")
def home():
    return {"message": "እንኳን ወደ አሮጌ ተራ API በሰላም መጡ!"}


# 1. ሁሉንም እቃዎች ማምጣት (Get All Products)
@app.get("/products")

def get_products(category_id: Optional[int] = None, search: Optional[str] = None):
    if not supabase:
        raise HTTPException(
            status_code=500, 
            detail="Supabase Connection Error! Render Environment Variables ላይ SUPABASE_URL እና SUPABASE_KEY መኖራቸውን አረጋግጥ።"
        )
    
    try:
        query = supabase.table("products").select("*")
        
        # በካቴጎሪ ለመለየት
        if category_id:
            query = query.eq("category_id", category_id)
            
        # በስም ለመፈለግ
        if search:
            query = query.ilike("title", f"%{search}%")
            
        response = query.order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Query Error: {str(e)}")


# 2. የአንድን እቃ ዝርዝር መረጃ ማምጣት
@app.get("/products/{product_id}")
def get_product_detail(product_id: int):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase connection not configured")
        
    try:
        response = supabase.table("products").select("*").eq("id", product_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="እቃው አልተገኘም")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 3. አዲስ እቃ መሸጫ መለጠፍ
@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase connection not configured")
    
    try:
        data = product.dict()
        response = supabase.table("products").insert(data).execute()
        return {"message": "እቃው በትክክል ተለጥፏል", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"እቃውን መለጠፍ አልተቻለም: {str(e)}")


# 4. እቃ ተሸጧል ብሎ መቀየር
@app.patch("/products/{product_id}/sold")
def mark_as_sold(product_id: int):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase connection not configured")
        
    try:
        response = supabase.table("products").update({"is_sold": True}).eq("id", product_id).execute()
        return {"message": "እቃው ተሸጧል ተብሎ ተቀይሯል", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 5. ካቴጎሪዎችን ማምጣት
@app.get("/categories")
def get_categories():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase connection not configured")
        
    try:
        response = supabase.table("categories").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
