from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from core.config import users_collection
from core.security import hash_password, verify_password
from utils.token_utils import create_access_token

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# -------------------------------------------------------
# LOGIN PAGE (UI)
# -------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    flash = request.cookies.get("flash")
    resp = templates.TemplateResponse(
        "login.html",
        {"request": request, "flash": flash}
    )
    if flash:
        resp.delete_cookie("flash")
    return resp


# -------------------------------------------------------
# USER LOGIN (POST) – USER ONLY
# -------------------------------------------------------
@router.post("/", response_class=HTMLResponse)
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):

    user = users_collection.find_one({"email": email})

    if not user or not verify_password(password, user["password"]):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "flash": "Invalid email or password"}
        )

    # create token
    token = create_access_token(email)

    # always go to home (no admin dashboard)
    resp = RedirectResponse("/home", status_code=303)
    resp.set_cookie("access_token", token, httponly=True)
    resp.set_cookie("flash", "Login successful", max_age=3)
    return resp


# -------------------------------------------------------
# SIGNUP
# -------------------------------------------------------
@router.get("/signup")
async def signup_page(request: Request):
    flash = request.cookies.get("flash")
    resp = templates.TemplateResponse(
        "signup.html",
        {"request": request, "flash": flash}
    )
    if flash:
        resp.delete_cookie("flash")
    return resp


@router.post("/signup")
async def signup_user(fullname: str = Form(...), email: str = Form(...),
                      password: str = Form(...), confirm_password: str = Form(...)):

    if password != confirm_password:
        return {"error": "Passwords do not match"}

    if users_collection.find_one({"email": email}):
        return {"error": "User already exists"}

    users_collection.insert_one({
        "name": fullname,
        "email": email,
        "password": hash_password(password),
        "role": "User",
        "status": "Active",
        "created_at": datetime.utcnow()
    })

    return RedirectResponse("/", status_code=303)


# -------------------------------------------------------
# LOGOUT
# -------------------------------------------------------
@router.get("/logout")
async def logout():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("access_token")
    resp.set_cookie("flash", "Logged out successfully", max_age=3)
    return resp
