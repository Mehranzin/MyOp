import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "dacertoDeus"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "postgresql://your_connection_string"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
