from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import bcrypt
import jwt
from slugify import slugify
import json
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# JWT Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
security = HTTPBearer()

# Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str

class WebsiteCreate(BaseModel):
    business_name: str
    business_description: str
    industry: str = "ecommerce"
    contact_email: EmailStr
    contact_phone: str
    address: str
    logo_base64: Optional[str] = None
    hero_image_base64: Optional[str] = None
    products: List[Dict[str, Any]] = []
    colors: Dict[str, str] = {
        "primary": "#3B82F6",
        "secondary": "#1E40AF",
        "accent": "#F59E0B"
    }
    social_links: Dict[str, str] = {}

class Website(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    business_name: str
    business_description: str
    industry: str
    contact_email: EmailStr
    contact_phone: str
    address: str
    logo_base64: Optional[str] = None
    hero_image_base64: Optional[str] = None
    products: List[Dict[str, Any]] = []
    colors: Dict[str, str] = {}
    social_links: Dict[str, str] = {}
    slug: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class WebsiteUpdate(BaseModel):
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    logo_base64: Optional[str] = None
    hero_image_base64: Optional[str] = None
    products: Optional[List[Dict[str, Any]]] = None
    colors: Optional[Dict[str, str]] = None
    social_links: Optional[Dict[str, str]] = None

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User(**user)

def generate_website_html(website: Website) -> str:
    """Generate HTML for the website"""
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{website.business_name} - Professional eCommerce Store</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        colors: {{
                            primary: '{website.colors.get("primary", "#3B82F6")}',
                            secondary: '{website.colors.get("secondary", "#1E40AF")}',
                            accent: '{website.colors.get("accent", "#F59E0B")}'
                        }}
                    }}
                }}
            }}
        </script>
        <style>
            .hero-bg {{
                background: linear-gradient(135deg, {website.colors.get("primary", "#3B82F6")} 0%, {website.colors.get("secondary", "#1E40AF")} 100%);
            }}
        </style>
    </head>
    <body class="bg-gray-50">
        <!-- Navigation -->
        <nav class="bg-white shadow-lg sticky top-0 z-50">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div class="flex items-center">
                        {f'<img src="data:image/jpeg;base64,{website.logo_base64}" alt="Logo" class="h-10 w-10 rounded-lg mr-3">' if website.logo_base64 else ''}
                        <span class="text-xl font-bold text-gray-900">{website.business_name}</span>
                    </div>
                    <div class="hidden md:flex space-x-8">
                        <a href="#home" class="text-gray-700 hover:text-primary transition-colors">Home</a>
                        <a href="#products" class="text-gray-700 hover:text-primary transition-colors">Products</a>
                        <a href="#about" class="text-gray-700 hover:text-primary transition-colors">About</a>
                        <a href="#contact" class="text-gray-700 hover:text-primary transition-colors">Contact</a>
                    </div>
                    <div class="flex items-center">
                        <button class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-secondary transition-colors">
                            Cart (<span id="cart-count">0</span>)
                        </button>
                    </div>
                </div>
            </div>
        </nav>

        <!-- Hero Section -->
        <section id="home" class="hero-bg text-white py-20">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                    <div>
                        <h1 class="text-4xl md:text-6xl font-bold mb-6">
                            Welcome to {website.business_name}
                        </h1>
                        <p class="text-xl mb-8 text-gray-100">
                            {website.business_description}
                        </p>
                        <div class="flex flex-wrap gap-4">
                            <button class="bg-accent text-white px-8 py-3 rounded-lg font-semibold hover:bg-yellow-600 transition-colors">
                                Shop Now
                            </button>
                            <button class="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-primary transition-colors">
                                Learn More
                            </button>
                        </div>
                    </div>
                    <div class="flex justify-center">
                        {f'<img src="data:image/jpeg;base64,{website.hero_image_base64}" alt="Hero" class="rounded-lg shadow-2xl max-w-full h-auto">' if website.hero_image_base64 else '<div class="bg-white bg-opacity-20 rounded-lg p-12 text-center"><h3 class="text-2xl font-bold mb-4">Your Hero Image Here</h3><p>Upload a stunning hero image to showcase your business</p></div>'}
                    </div>
                </div>
            </div>
        </section>

        <!-- Products Section -->
        <section id="products" class="py-20 bg-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center mb-12">
                    <h2 class="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Our Products</h2>
                    <p class="text-gray-600 max-w-2xl mx-auto">Discover our amazing collection of premium products</p>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {_generate_product_cards(website.products)}
                </div>
            </div>
        </section>

        <!-- About Section -->
        <section id="about" class="py-20 bg-gray-50">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                    <div>
                        <h2 class="text-3xl md:text-4xl font-bold text-gray-900 mb-6">About {website.business_name}</h2>
                        <p class="text-gray-600 mb-6">{website.business_description}</p>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="flex items-center">
                                <div class="bg-primary text-white p-3 rounded-lg mr-4">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                    </svg>
                                </div>
                                <div>
                                    <h3 class="font-semibold text-gray-900">Quality Products</h3>
                                    <p class="text-gray-600">Premium quality guaranteed</p>
                                </div>
                            </div>
                            <div class="flex items-center">
                                <div class="bg-primary text-white p-3 rounded-lg mr-4">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                </div>
                                <div>
                                    <h3 class="font-semibold text-gray-900">Fast Delivery</h3>
                                    <p class="text-gray-600">Quick and reliable shipping</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="bg-white p-8 rounded-lg shadow-lg">
                        <h3 class="text-xl font-bold text-gray-900 mb-4">Get in Touch</h3>
                        <div class="space-y-4">
                            <div class="flex items-center">
                                <svg class="w-5 h-5 text-primary mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                                </svg>
                                <span class="text-gray-600">{website.contact_email}</span>
                            </div>
                            <div class="flex items-center">
                                <svg class="w-5 h-5 text-primary mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
                                </svg>
                                <span class="text-gray-600">{website.contact_phone}</span>
                            </div>
                            <div class="flex items-center">
                                <svg class="w-5 h-5 text-primary mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                </svg>
                                <span class="text-gray-600">{website.address}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Contact Section -->
        <section id="contact" class="py-20 bg-primary text-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center mb-12">
                    <h2 class="text-3xl md:text-4xl font-bold mb-4">Contact Us</h2>
                    <p class="text-gray-200">Ready to get started? Send us a message!</p>
                </div>
                <div class="max-w-2xl mx-auto">
                    <form class="space-y-6" onsubmit="handleContactForm(event)">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <input type="text" placeholder="Your Name" required class="w-full px-4 py-3 rounded-lg text-gray-900 focus:ring-2 focus:ring-accent focus:outline-none">
                            <input type="email" placeholder="Your Email" required class="w-full px-4 py-3 rounded-lg text-gray-900 focus:ring-2 focus:ring-accent focus:outline-none">
                        </div>
                        <input type="text" placeholder="Subject" required class="w-full px-4 py-3 rounded-lg text-gray-900 focus:ring-2 focus:ring-accent focus:outline-none">
                        <textarea placeholder="Your Message" rows="5" required class="w-full px-4 py-3 rounded-lg text-gray-900 focus:ring-2 focus:ring-accent focus:outline-none resize-none"></textarea>
                        <button type="submit" class="w-full bg-accent text-white py-3 rounded-lg font-semibold hover:bg-yellow-600 transition-colors">
                            Send Message
                        </button>
                    </form>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="bg-gray-900 text-white py-12">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
                    <div>
                        <h3 class="text-xl font-bold mb-4">{website.business_name}</h3>
                        <p class="text-gray-400">{website.business_description[:100]}...</p>
                    </div>
                    <div>
                        <h4 class="text-lg font-semibold mb-4">Quick Links</h4>
                        <ul class="space-y-2 text-gray-400">
                            <li><a href="#home" class="hover:text-white transition-colors">Home</a></li>
                            <li><a href="#products" class="hover:text-white transition-colors">Products</a></li>
                            <li><a href="#about" class="hover:text-white transition-colors">About</a></li>
                            <li><a href="#contact" class="hover:text-white transition-colors">Contact</a></li>
                        </ul>
                    </div>
                    <div>
                        <h4 class="text-lg font-semibold mb-4">Contact Info</h4>
                        <ul class="space-y-2 text-gray-400">
                            <li>{website.contact_email}</li>
                            <li>{website.contact_phone}</li>
                            <li>{website.address}</li>
                        </ul>
                    </div>
                    <div>
                        <h4 class="text-lg font-semibold mb-4">Follow Us</h4>
                        <div class="flex space-x-4">
                            {_generate_social_links(website.social_links)}
                        </div>
                    </div>
                </div>
                <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
                    <p>&copy; 2024 {website.business_name}. All rights reserved.</p>
                </div>
            </div>
        </footer>

        <script>
            let cart = [];
            let cartCount = 0;

            function addToCart(productId, productName, productPrice) {{
                cart.push({{
                    id: productId,
                    name: productName,
                    price: productPrice
                }});
                cartCount++;
                document.getElementById('cart-count').textContent = cartCount;
                alert(`${{productName}} added to cart!`);
            }}

            function handleContactForm(event) {{
                event.preventDefault();
                alert('Thank you for your message! We will get back to you soon.');
                event.target.reset();
            }}

            // Smooth scrolling for navigation links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    document.querySelector(this.getAttribute('href')).scrollIntoView({{
                        behavior: 'smooth'
                    }});
                }});
            }});
        </script>
    </body>
    </html>
    """
    return template

def _generate_product_cards(products):
    if not products:
        return """
        <div class="col-span-full text-center py-12">
            <h3 class="text-xl font-semibold text-gray-900 mb-4">No products yet</h3>
            <p class="text-gray-600">Add products to showcase them here</p>
        </div>
        """
    
    cards = ""
    for i, product in enumerate(products[:6]):  # Show max 6 products
        image_src = f'data:image/jpeg;base64,{product.get("image_base64", "")}' if product.get("image_base64") else "https://via.placeholder.com/300x200?text=Product+Image"
        cards += f"""
        <div class="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow">
            <img src="{image_src}" alt="{product.get('name', 'Product')}" class="w-full h-48 object-cover">
            <div class="p-6">
                <h3 class="text-xl font-bold text-gray-900 mb-2">{product.get('name', 'Product Name')}</h3>
                <p class="text-gray-600 mb-4">{product.get('description', 'Product description')}</p>
                <div class="flex items-center justify-between">
                    <span class="text-2xl font-bold text-primary">${product.get('price', '0.00')}</span>
                    <button onclick="addToCart('{i}', '{product.get('name', 'Product')}', '{product.get('price', '0.00')}')" 
                            class="bg-primary text-white px-6 py-2 rounded-lg hover:bg-secondary transition-colors">
                        Add to Cart
                    </button>
                </div>
            </div>
        </div>
        """
    return cards

def _generate_social_links(social_links):
    if not social_links:
        return ""
    
    links = ""
    for platform, url in social_links.items():
        if url:
            links += f"""
            <a href="{url}" target="_blank" class="text-gray-400 hover:text-white transition-colors">
                <span class="sr-only">{platform}</span>
                <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0C5.374 0 0 5.373 0 12s5.374 12 12 12 12-5.373 12-12S18.626 0 12 0zm5.568 8.16c-.172 1.684-.896 3.262-1.998 4.364-1.102 1.102-2.678 1.826-4.364 1.998-.546.055-1.104.055-1.65 0-1.686-.172-3.262-.896-4.364-1.998C4.09 11.422 3.366 9.846 3.194 8.16c-.055-.546-.055-1.104 0-1.65.172-1.686.896-3.262 1.998-4.364C6.294 1.044 7.87.32 9.556.148c.546-.055 1.104-.055 1.65 0 1.686.172 3.262.896 4.364 1.998 1.102 1.102 1.826 2.678 1.998 4.364.055.546.055 1.104 0 1.65z"/>
                </svg>
            </a>
            """
    return links

# Authentication Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user.password)
    user_data = User(
        name=user.name,
        email=user.email
    )
    user_dict = user_data.dict()
    user_dict["password"] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    # Find user
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user["id"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Website Routes
@api_router.post("/websites", response_model=Website)
async def create_website(website: WebsiteCreate, current_user: User = Depends(get_current_user)):
    # Generate slug
    slug = slugify(website.business_name)
    
    # Check if slug already exists for this user
    existing_website = await db.websites.find_one({"user_id": current_user.id, "slug": slug})
    if existing_website:
        slug = f"{slug}-{uuid.uuid4().hex[:8]}"
    
    # Create website
    website_data = Website(
        user_id=current_user.id,
        business_name=website.business_name,
        business_description=website.business_description,
        industry=website.industry,
        contact_email=website.contact_email,
        contact_phone=website.contact_phone,
        address=website.address,
        logo_base64=website.logo_base64,
        hero_image_base64=website.hero_image_base64,
        products=website.products,
        colors=website.colors,
        social_links=website.social_links,
        slug=slug
    )
    
    await db.websites.insert_one(website_data.dict())
    
    return website_data

@api_router.get("/websites", response_model=List[Website])
async def get_user_websites(current_user: User = Depends(get_current_user)):
    websites = await db.websites.find({"user_id": current_user.id, "is_active": True}).to_list(100)
    return [Website(**website) for website in websites]

@api_router.get("/websites/{website_id}", response_model=Website)
async def get_website(website_id: str, current_user: User = Depends(get_current_user)):
    website = await db.websites.find_one({"id": website_id, "user_id": current_user.id})
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return Website(**website)

@api_router.put("/websites/{website_id}", response_model=Website)
async def update_website(
    website_id: str, 
    website_update: WebsiteUpdate, 
    current_user: User = Depends(get_current_user)
):
    website = await db.websites.find_one({"id": website_id, "user_id": current_user.id})
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    # Update fields
    update_data = website_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.websites.update_one(
        {"id": website_id, "user_id": current_user.id},
        {"$set": update_data}
    )
    
    updated_website = await db.websites.find_one({"id": website_id, "user_id": current_user.id})
    return Website(**updated_website)

@api_router.delete("/websites/{website_id}")
async def delete_website(website_id: str, current_user: User = Depends(get_current_user)):
    result = await db.websites.update_one(
        {"id": website_id, "user_id": current_user.id},
        {"$set": {"is_active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Website not found")
    return {"message": "Website deleted successfully"}

# Website Hosting Routes
@api_router.get("/websites/{website_id}/preview", response_class=HTMLResponse)
async def preview_website(website_id: str, current_user: User = Depends(get_current_user)):
    website = await db.websites.find_one({"id": website_id, "user_id": current_user.id})
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    website_obj = Website(**website)
    html_content = generate_website_html(website_obj)
    return HTMLResponse(content=html_content)

@api_router.get("/sites/{username}/{slug}", response_class=HTMLResponse)
async def serve_website(username: str, slug: str):
    # Find user by username (email for now)
    user = await db.users.find_one({"email": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find website by slug
    website = await db.websites.find_one({"user_id": user["id"], "slug": slug, "is_active": True})
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    website_obj = Website(**website)
    html_content = generate_website_html(website_obj)
    return HTMLResponse(content=html_content)

# Include the router in the main app
app.include_router(api_router)

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