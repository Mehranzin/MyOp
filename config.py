import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "dacertoDeus"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "postgresql://database_3c3l_user:iUeI609oE6aF4a2WB6PIJm1VpRI3vtLc@dpg-d29u6eidbo4c73ap8rj0-a/database_3c3l"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
