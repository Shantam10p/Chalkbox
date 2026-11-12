from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app import auth

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


@router.post("/login")
def login(body: LoginIn, response: Response):
    user = auth.authenticate(body.username, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Wrong username or password")
    token = auth.create_session(user["id"])
    # HttpOnly: page scripts can't read it. Not "secure", because the hub serves plain
    # http on the school's local network.
    response.set_cookie(
        auth.COOKIE_NAME, token, httponly=True, samesite="lax",
        max_age=auth.SESSION_DAYS * 24 * 3600, path="/",
    )
    return user


@router.post("/logout")
def logout(response: Response, chalkbox_session: str | None = Cookie(default=None)):
    auth.end_session(chalkbox_session)
    response.delete_cookie(auth.COOKIE_NAME, path="/")
    return {"signed_out": True}


@router.get("/me")
def me(user: dict = Depends(auth.current_user)):
    return user
