import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
, HTTPException, Status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(title="Aroge Tera API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class UserRegister(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    phone_number: Optional[str] = None

class ProductCreate(BaseModel):
    seller_id: int
    title: str
    description: Optional[str] = ""
    price: float
    category_id: int
    condition: str
    images: List[str] = []

@app.get("/")
def home():
    return {"status": "Aroge Tera API is running successfully!"}

@app.post("/api/users")
def register_user(user: UserRegister):
    data = user.model_dump()
    response = supabase.table("users").upsert(data).execute()
    return {"data": response.data}

@app.get("/api/products")
def get_products(category_id: Optional[int] = None, search: Optional[str] = None):
    query = supabase.table("products").select("*, users(username, first_name, phone_number)").eq("is_sold", False)
    if category_id:
        query = query.eq("category_id", category_id)
    if search:
        query = query.ilike("title", f"%{search}%")
    response = query.order("created_at", desc=True).execute()
    return response.data

@app.post("/api/products", status_code=Status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    data = product.model_dump()
    response = supabase.table("products").insert(data).execute()
    return {"data": response.data}
