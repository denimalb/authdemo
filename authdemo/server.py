import base64
import hmac
import hashlib
import json
from typing import Optional

from fastapi import FastAPI, Form, Cookie, Body
from fastapi.responses import Response


app = FastAPI()

SECRET_KEY = "8c5275f19c7c518b3e1376e4963d03a40841f08c472cf5b2e8fb65a5ebe4b92c"
PASSWORD_SALT = "3ef915b19662b2bcd841ec4395d0d0ee4570755632f131584a008a2657ca1e57"

def sign_data(data: str) -> str:
    """Возвращает подписанные данные data"""
    return hmac.new(
        SECRET_KEY.encode(),
        msg=data.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()

def get_username_from_signed_string(username_signed: str) -> Optional[str]:
    username_base64, sign = username_signed.split(".")
    username = base64.b64decode(username_base64.encode()).decode()
    valid_sign = sign_data(username)
    if hmac.compare_digest(valid_sign, sign):
        return username


def verify_password(username: str, password: str) -> bool:
    password_hash = hashlib.sha256( (password + PASSWORD_SALT).encode() )\
        .hexdigest().lower()
    stored_password_hash = users[username]["password"]
    return password_hash == stored_password_hash


users = {
    "alexey@user.com": {
        "name": "Алексей",
        "password": "1d71c91c92698e09815037d7f3821cdb0534f1372d2f69bae2b123e34bede53c",
        "balance": 100_000
    },
    "petr@user.com": {
        "name": "Пётр",
        "password": "e10d13ec419e05605b77ef516bb821f39cbee4fb534cc79658cc94e5f5ed6b62",
        "balance": 555_555
    }
}


@app.get("/")
def index_page(username: Optional[str] = Cookie(default=None)):
    with open('templates/login.html', 'r') as f:
        login_page = f.read()
    if not username:                    # Проверка валидности cookie
        return Response(login_page, media_type="text/html")
    valid_username = get_username_from_signed_string(username)
    if not valid_username:
        response = Response(login_page, media_type="text/html")
        response.delete_cookie(key="username")
        return response
    try:
        user = users[valid_username]
    except KeyError:
        response = Response(login_page, media_type="text/html")
        response.delete_cookie(key="username")
        return response
    return Response(
        f"Привет, {users[valid_username]['name']}!<br />"
        f"Баланс: {users[valid_username]['balance']}",
        media_type='application/json')                 # media_type Для вывода в браузере текста в читаемой кодировке
    


@app.post("/login")
# def process_login_page(data: dict = Body(...)):
#     username = data["username"]
#     password = data["password"]
def process_login_page(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or not verify_password(username, password):
        return Response(
            json.dumps({
                "success": False,
                "message": "Я вас не знаю!"
            }),
            media_type="application/json")

    response = Response(
        json.dumps({
            "success": True,
            "message": f"Привет, {user['name']}!<br />Баланс: {user['balance']}"
        }),
        media_type='application/json')

    username_signed = base64.b64encode(username.encode()).decode() + "." + \
        sign_data(username)
    response.set_cookie(key="username", value=username_signed)
    return response