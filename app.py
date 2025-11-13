from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from pymongo import MongoClient
from datetime import datetime
import uvicorn
import os
from dotenv import load_dotenv 

# ===================================================
# CONFIGURATION
# ===================================================
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise ValueError("❌ MONGO_URL environment variable is not set!")

DB_NAME = os.getenv("DB_NAME", "fastapi_auth_db")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
users_collection = db["users"]
shipments_collection = db["shipments"]

# ✅ Using ARGON2 (No bcrypt bugs)
pwd_context = CryptContext(
    schemes=["argon2"],
    default="argon2",
    deprecated="auto"
)

# ===================================================
# FASTAPI SETUP
# ===================================================
app = FastAPI(title="SCMLite - Supply Chain Management System")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def connect_db():
    try:
        client.admin.command("ping")
        print(f"✅ Connected to MongoDB: {DB_NAME}")
    except Exception as e:
        print("❌ MongoDB connection failed:", e)


# ===================================================
# LOGIN ROUTES
# ===================================================
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/home", status_code=303)
    
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("login.html", {"request": request, "flash": flash})


@app.post("/", response_class=HTMLResponse)
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    user = users_collection.find_one({"email": email})

    if user and pwd_context.verify(password, user["password"]):
        request.session["user"] = user["email"]
        print("✅ Logged in:", email)
        return RedirectResponse("/home", status_code=303)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "flash": "❌ Invalid email or password."
    })


# ===================================================
# SIGNUP ROUTES
# ===================================================
@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("signup.html", {"request": request, "flash": flash})


@app.post("/signup", response_class=HTMLResponse)
async def signup_user(
    request: Request,
    fullname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "flash": "❌ Passwords do not match."
        })

    if users_collection.find_one({"email": email}):
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "flash": "⚠️ Email already exists."
        })

    hashed_pw = pwd_context.hash(password)

    users_collection.insert_one({
        "name": fullname,
        "email": email,
        "password": hashed_pw,
        "created_at": datetime.utcnow()
    })

    request.session["flash"] = "✅ Signup successful! Please log in."
    print("👤 New user registered:", email)

    return RedirectResponse("/", status_code=303)


# ===================================================
# HOME / DASHBOARD
# ===================================================
@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/", status_code=303)

    shipment_count = shipments_collection.count_documents({})
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "shipment_count": shipment_count
    })


# ===================================================
# CREATE SHIPMENT
# ===================================================
@app.get("/create-shipment", response_class=HTMLResponse)
async def create_shipment_page(request: Request):
    if not request.session.get("user"):
        return RedirectResponse("/")

    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("create_shipment.html", {"request": request, "flash": flash})


@app.post("/create-shipment", response_class=HTMLResponse)
async def create_shipment(
    request: Request,
    shipment_id: str = Form(...),
    sender_name: str = Form(...),
    receiver_name: str = Form(...),
    destination: str = Form(...),
    weight: float = Form(...),
    status: str = Form(...)
):
    if shipments_collection.find_one({"shipment_id": shipment_id}):
        return templates.TemplateResponse("create_shipment.html", {
            "request": request,
            "flash": "⚠️ Shipment ID already exists."
        })

    shipments_collection.insert_one({
        "shipment_id": shipment_id,
        "sender_name": sender_name,
        "receiver_name": receiver_name,
        "destination": destination,
        "weight": weight,
        "status": status,
        "created_at": datetime.utcnow()
    })

    request.session["flash"] = "✅ Shipment created!"
    print("📦 Shipment created:", shipment_id)
    return RedirectResponse("/create-shipment", status_code=303)


from fastapi.responses import StreamingResponse
import json
import asyncio

@app.get("/stream-shipments")
async def stream_shipments():
    """Live shipment stream using SSE"""
    async def event_generator():
        last_count = shipments_collection.count_documents({})

        while True:
            await asyncio.sleep(2)  # check every 2 seconds

            new_count = shipments_collection.count_documents({})
            if new_count != last_count:
                last_count = new_count
                latest_data = list(shipments_collection.find().sort("created_at", -1).limit(10))
                
                # Convert ObjectId to string for JSON
                for item in latest_data:
                    item["_id"] = str(item["_id"])

                yield f"data: {json.dumps(latest_data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/DataStream", response_class=HTMLResponse)
async def data_stream_page(request: Request):
    return templates.TemplateResponse("data_stream.html", {"request": request})


# ===================================================
# LOGOUT
# ===================================================
@app.get("/logout")
async def logout(request: Request):
    user = request.session.get("user")
    request.session.clear()
    print("👋 Logged out:", user)
    return RedirectResponse("/", status_code=303)



# ===================================================
# SERVER RUN
# ===================================================
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
