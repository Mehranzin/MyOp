import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "dacertoDeus"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "postgresql://database_fgg4_user:KERYBt5keA9hy1yOidgqrRRfxckh3BCl@dpg-d1lak4vdiees73fel3c0-a.virginia-postgres.render.com/database_fgg4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
