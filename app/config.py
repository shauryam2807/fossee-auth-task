# app/config.py
import os
from dotenv import load_dotenv

# .env file load karo
load_dotenv()

class Config:
    # Flask aur JWT ke liye secret key
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-fallback-secret')
    
    # SQLAlchemy (Database) ki settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
