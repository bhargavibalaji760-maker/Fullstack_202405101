from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from core.config import users_collection
from core.dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# -----------------------------------------------------------
# USER: VIEW OWN PROFILE
# -----------------------------------------------------------
@router.get("/users/profile")
async def user_profile(request: Request, user_email: str = Depends(get_current_user)):
    user = users_collection.find_one({"email": user_email}, {"password": 0})

    if not user:
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user
        }
    )


# -----------------------------------------------------------
# USER: UPDATE OWN PROFILE
# -----------------------------------------------------------
@router.post("/users/update")
async def update_profile(
    request: Request,
    fullname: str = Form(...),
    user_email: str = Depends(get_current_user)
):
    users_collection.update_one(
        {"email": user_email},
        {"$set": {"name": fullname}}
    )

    return RedirectResponse("/users/profile", status_code=303)
