import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "dacertoDeus"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "postgresql://database_rr7z_user:xfXL4L4EvqmTs1xxwAO1jTHnqR7go6gB@dpg-d2ci5r3uibrs738hd6f0-a/database_rr7z"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
