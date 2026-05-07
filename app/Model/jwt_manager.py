from fastapi import Request
import jwt
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
import logging
from Model.user import UserSignedIn


class JwtManager:
    def __init__(self):
        try:

            logging.info('jwt_manager.py')

            # 找到 app 目錄
            BASE_DIR = os.path.dirname(os.path.dirname(__file__))

            json_path_app = os.path.join(BASE_DIR, "appsettings.json")
            json_path_security = os.path.join(BASE_DIR, "core", "security.json")

            with open(json_path_app, 'r', encoding='utf-8') as file1:
                data = json.load(file1)
                self.expiration_seconds = data["Expiration"]["Jwt"]

            with open(json_path_security, 'r', encoding='utf-8') as file2:
                data = json.load(file2)
                self.key = data["Jwt"]["Key"]
                self.issuer = data["Jwt"]["Issuer"]

        except Exception as e:
            logging.error(f'jwt_manager error: {str(e)}')
            raise

    def generate_jwt(self, user: UserSignedIn):
        utcnow = datetime.utcnow()
        payload = {
            "FTASn": user.FTASn,
            "FTAId": user.FTAId,
            "YFYId": user.YFYId,
            "Name": user.Name,
            "exp": utcnow + timedelta(seconds=self.expiration_seconds),
            "iat": str(int(datetime.timestamp(utcnow.replace(microsecond=0, tzinfo=timezone.utc)))),
            "nbf": utcnow,
            "jti":str(uuid.uuid4()),
            "iss":self.issuer,
            "aud":self.issuer
        }
        jwt_token = jwt.encode(payload, self.key, algorithm='HS256')
        return jwt_token

    def decode_jwt_from_cookie(self, request: Request) -> dict:
        """解析並驗證 JWT，從 Cookie 中取得"""
        token = request.cookies.get('jwt')
        if not token:
            raise PermissionError("JWT not found in cookie")

        try:
            payload = jwt.decode(
                token,
                self.key,
                algorithms=["HS256"],
                issuer=self.issuer,
                audience=self.issuer
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise PermissionError("JWT expired")
        except jwt.InvalidTokenError as e:
            raise PermissionError(f"Invalid JWT: {str(e)}")