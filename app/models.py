# app/models.py
from datetime import datetime
from app import db

# 1. Users Table
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # Hashed password aayega yahan
    full_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ye batata hai ki ek User ke paas bahut saari Files ho sakti hain (One-to-Many relationship)
    files = db.relationship('File', backref='owner', lazy=True, cascade="all, delete-orphan")

# 2. Files Table
class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key: Ye batati hai ki ye file kis user ki hai
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
# 3. Blacklisted Tokens Table (Logout ke liye)
class BlacklistedToken(db.Model):
    __tablename__ = 'blacklisted_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text, nullable=False, unique=True)
    blacklisted_at = db.Column(db.DateTime, default=datetime.utcnow)
