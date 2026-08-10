import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(title="Aroge Tera Mini App API")

# Telegram Mini App Frontend ኮድህ ጥሪ ሲያደርግ እንዳይከለከል CORS መፍቀድ
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
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- Pydantic Data Models ---

class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category_id: Optional[int] = None
    condition: str  # 'አዲስ', 'በጣም ጥሩ', 'ከፊል ያገለገለ', 'ጥገና የሚያስፈልገው'
    images: List[str] = []
    seller_telegram_id: str
    seller_phone: Optional[str] = None


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
    is_sold: Optional[bool] = None


# --- API Endpoints ---

@app.get("/")
def home():
    return {"message": "እንኳን ወደ አሮጌ ተራ API በሰላም መጡ!"}


# 1. ሁሉንም ያልተሸጡ እቃዎች ማምጣት (Get All Available Products)
@app.get("/products")
def get_products(category_id: Optional[int] = None, search: Optional[str] = None):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase connection not configured")
    
    query = supabase.table("products").select("*").eq("is_sold", False)
    
    # በካቴጎሪ ለመለየት
    if category_id:
        query = query.eq("category_id", category_id)
        
    # በስም ለመፈለግ
    if search:
        query = query.ilike("title", f"%{search}%")
        
    response = query.order("created_at", desc=True).execute()
    return response.data


# 2. የአንድን እቃ ዝርዝር መረጃ ማምጣት (Get Product by ID)
@app.get("/products/{product_id}")
def get_product_detail(product_id: int):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase connection not configured")
        
    response = supabase.table("products").select("*").eq("id", product_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="እቃው አልተገኘም")
    return response.data[0]


# 3. አዲስ እቃ መሸጫ መለጠፍ (Post New Product)
@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase connection not configured")
    
    # በ Supabase ቴብልህ ላይ የተወሰነውን የ condition ህግ ማረጋገጥ
    valid_conditions = ['አዲስ', 'በጣም ጥሩ', 'ከፊል ያገለገለ', 'ጥገና የሚያስፈልገው']
    if product.condition not in valid_conditions:
        raise HTTPException(
            status_code=400, 
            detail=f"Condition እሴት ከነዚህ አንዱ መሆን አለበት: {', '.join(valid_conditions)}"
        )
    
    data = product.dict()
    response = supabase.table("products").insert(data).execute()
    return {"message": "እቃው በትክክል ተለጥፏል", "data": response.data}


# 4. እቃ ተሸጧል ብሎ መቀየር (Mark as Sold)
@app.patch("/products/{product_id}/sold")
def mark_as_sold(product_id: int):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase connection not configured")
        
    response = supabase.table("products").update({"is_sold": True}).eq("id", product_id).execute()
    return {"message": "እቃው ተሸጧል ተብሎ ተቀይሯል", "data": response.data}


# 5. የካቴጎሪዎችን ዝርዝር ማምጣት (Get Categories)
@app.get("/categories")
def get_categories():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase connection not configured")
        
    response = supabase.table("categories").select("*").execute()
    return response.data
