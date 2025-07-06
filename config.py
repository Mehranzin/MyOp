import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "dacertoDeus"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "postgresql://database_gwsy_user:da3yNKwdpJOvSsb7JCtxZOJzFRuG5bAr@dpg-d1lc4g6r433s73dic9lg-a/database_gwsy"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
