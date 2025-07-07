import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "dacertoDeus"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "postgresql://database_zgax_user:deOzGpWkFnVZqRwakvVP5zjIrQ6McPkj@dpg-d1lltumr433s73dsoki0-a/database_zgax"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
