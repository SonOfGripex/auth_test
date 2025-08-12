from fastapi import APIRouter, HTTPException, Cookie
from fastapi import Response
from starlette.responses import JSONResponse
from password_validator import PasswordValidator
from app.user.schemas.user import UserRegister, UserLogin, PasswordResetRequest, PasswordReset
from app.user.models.user import User, RefreshToken
from tortoise.transactions import in_transaction
from app.services import jwt_service
from app.services.password import hash_password, check_password
from fastapi.security import HTTPBearer
from app.services.utils import set_auth_cookies
from app.services.jwt_service import hash_token, encode_token, decode_token
from datetime import datetime, timedelta


router = APIRouter(prefix="/auth")
security = HTTPBearer()


@router.post("/register")
async def register(user: UserRegister, response: Response):
    async with in_transaction() as db:
        existing = await User.get_or_none(email=user.email)
        if existing:
            raise HTTPException(status_code=400, detail="email already exists")

        validator = PasswordValidator()
        validator.min(8).max(100).has().uppercase().has().lowercase().has().letters().has().no().spaces()

        if not validator.validate(user.password):
            raise HTTPException(status_code=400, detail="password is invalid")

        hashed = hash_password(user.password)
        new_user = await User.create(
            email=user.email,
            password=hashed,
            using_db=db
        )
        access_token = jwt_service.create_access_token(str(new_user.uuid), [], [], str(new_user.email))
        refresh_token = jwt_service.create_refresh_token(str(new_user.uuid))

        await RefreshToken.create(
            user=new_user,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        set_auth_cookies(response, access_token, refresh_token)

        return {"status": "success"}

@router.post("/login")
async def login(user: UserLogin, response: Response):
    db_user = await User.get_or_none(email=user.email).prefetch_related("user_roles",
                                                                        "user_roles__role",
                                                                        "user_permissions",
                                                                        "user_permissions__permission")

    if not db_user or not check_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials or user doesn't exist")

    roles = [i.name for i in [i.role for i in db_user.user_roles]]
    perms = [i.name for i in [i.permission for i in db_user.user_permissions]]

    access_token = jwt_service.create_access_token(str(db_user.uuid), roles, perms, str(db_user.email))
    refresh_token = jwt_service.create_refresh_token(str(db_user.uuid))

    await RefreshToken.filter(user_id=db_user.id, revoked=False).update(revoked=True)
    await RefreshToken.create(
        user=db_user,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )

    set_auth_cookies(response, access_token, refresh_token)

    return {"status": "success"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="accessToken", httponly=True, secure=True, samesite="none", path="/")
    response.delete_cookie(key="refreshToken", httponly=True, secure=True, samesite="none", path="/")
    return {"status": "success"}

@router.post("/me")
async def me(access_token: str = Cookie(None, alias="accessToken")):

    if not access_token:
        raise HTTPException(status_code=401, detail="Access token is missing")

    try:
        try:
            payload = jwt_service.decode_token(access_token)
        except:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_email: str = payload.get("email")
        roles = [r for r in payload['roles']]
        permissions = [p for p in payload['permissions']]

    except HTTPException:
        return HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return JSONResponse(
        {
            'email': user_email,
            'roles': roles,
            'permissions': permissions
        },
        status_code=200
    )


@router.post("/request_password_reset")
async def request_password_reset(data: PasswordResetRequest):
    user_exists = await User.exists(email=data.email)
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found.")

    token_data = {
        "email": data.email,
        "exp": datetime.utcnow() + timedelta(minutes=10)
    }

    token = encode_token(token_data)
    return {"token": token} # Пример для сброса (обычно отправляется на почту)


@router.post("/reset_password")
async def reset_password(data: PasswordReset, token: str = Cookie(None, alias="resetPasswordToken")):
    try:
        payload = decode_token(token)
        email = payload["email"]

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    validator = PasswordValidator()
    validator.min(8).max(100).has().uppercase().has().lowercase().has().letters().has().no().spaces()

    if not validator.validate(data.new_password):
        raise HTTPException(status_code=400, detail="password is invalid")

    async with in_transaction() as db:
        user = await User.get_or_none(email=email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if check_password(data.new_password, user.password):
            raise HTTPException(status_code=400, detail="new_password must be different")

        hashed_password = hash_password(data.new_password)
        user.password = hashed_password
        await user.save(update_fields=["password"], using_db=db)

    return {"message": "Password has been reset successfully"}
