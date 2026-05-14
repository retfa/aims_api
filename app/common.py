import datetime
import json
import os
# from flask_restx import reqparse, fields
from urllib.parse import quote
import logging
import jwt
from pathlib import Path



def create_parser(model):
    dto_parser = reqparse.RequestParser()
    
    # 定義可支援的基礎型別對應
    base_type_mapping = {
        fields.String: str,
        fields.Integer: int,
        fields.Float: float,
        fields.Boolean: str_to_bool,
        fields.Raw: str  # fallback 為 str
    }

    for field_name, field in model.items():
        # 是否為 List 型別
        if isinstance(field, fields.List):
            container = field.container
            matched_type = next((py_type for field_type, py_type in base_type_mapping.items()
                                 if isinstance(container, field_type)), None)
            if matched_type is None:
                raise ValueError(f"Unsupported List item type: {type(container)} in field '{field_name}'")

            dto_parser.add_argument(
                name=field_name,
                type=matched_type,
                action='append',
                required=field.required,
                help=field.description,
                default=field.default
            )
            continue

        # 處理單一非 List 型別
        matched_type = next((py_type for field_type, py_type in base_type_mapping.items()
                             if isinstance(field, field_type)), None)
        if matched_type is None:
            raise ValueError(f"Unsupported field type: {type(field)} in field '{field_name}'")

        dto_parser.add_argument(
            name=field_name,
            type=matched_type,
            required=field.required,
            help=field.description,
            default=field.default
        )

    return dto_parser

def str_to_bool(val):
    """
    將字串轉為布林值：
    - 如果 val 為 None 或空字串 → 回傳 False（也可視需求改為丟錯誤或回 None）
    - 小寫後若在 ('true','1','yes','y') → 回傳 True
    - 小寫後若在 ('false','0','no','n') → 回傳 False
    - 其他字串 → ValueError（代表 400 Bad Request）
    """
    if val is None:
        return False
    s = str(val).strip().lower()
    if s in ('true', '1', 'yes', 'y'):
        return True
    if s in ('false', '0', 'no', 'n'):
        return False
    raise ValueError(f"布林解析失敗：無法將 '{val}' 轉為布林")

def get_connection_string(json_path, cs_name):
    with open(json_path, encoding="utf-8") as json_file:
        connections = json.load(json_file)
        if cs_name in connections['ConnectionStrings']:
            if isinstance(connections['ConnectionStrings'][cs_name], dict):
                connection_info = connections['ConnectionStrings'][cs_name]
                username = connection_info['username']
                password = quote(connection_info['password'])
                server = connection_info['server']
                database = connection_info['database']
                connection_string = (f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC"
                                     f"+Driver+17+for+SQL+Server")
            elif isinstance(connections['ConnectionStrings'][cs_name], str):
                connection_string = connections['ConnectionStrings'][cs_name]
            else:
                raise Exception("Database connection not found in connections.json")
        else:
            raise Exception("Database connection not found in connections.json")
    return connection_string


def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))

    return d


def format_datetime(dt, format):
    try:
        return dt.strftime(format)
    except (AttributeError, ValueError, TypeError):
        return None


def GetJwtPayload(security, req):
    token = req.cookies.get('jwt')

    # 如果 cookies 中沒有 token，則檢查 Authorization header
    if not token:
        auth_header = req.headers.get('Authorization')
        if auth_header:
            # Authorization header 格式通常是 "Bearer <token>"
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]

    # 如果 token 存在，進行處理
    if token:
        payload = jwt.decode(token, security["key"], algorithms=['HS256'], audience=security["aud"])
        print(f'jwtpayload: {type(payload)}')
        return payload


def set_security(target, app):
    BASE_DIR = Path(__file__).resolve().parent
    json_path_security = os.path.join(BASE_DIR, "core", "security.json")
    logging.info(f'json_path_security: {json_path_security}')
    with open(json_path_security, 'r', encoding='utf-8') as file2:
        data = json.load(file2)
        target.security = {}
        target.security['key'] = data["Jwt"]["Key"]
        target.security['aud'] = data["Jwt"]["Audience"]


def add_to_dict(cls):
    cls.to_dict = class_to_dict
    return cls


def class_to_dict(obj):
    dict_ = {}
    for key in obj.__mapper__.c.keys():
        value = getattr(obj, key)
        if isinstance(value, datetime.datetime):
            value = value.strftime('%Y-%m-%d %H:%M:%S')
        dict_[key] = value
    return dict_
