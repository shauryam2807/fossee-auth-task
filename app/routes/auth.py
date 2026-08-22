from flask import Blueprint, request, jsonify, current_app
from app import db, limiter
from app.models import User, BlacklistedToken
from app.utils.security import hash_password, check_password
from app.middleware.auth_middleware import token_required
import jwt
import datetime

auth_bp = Blueprint('auth', __name__)

# ──────────────────────────────────────────────
# POST /register — Create a new user account
# ──────────────────────────────────────────────
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields (full_name is optional — frontend may not send it)
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"error": "This email is already registered"}), 409
    
    # Hash the password (NEVER store plaintext!)
    hashed_pwd = hash_password(data['password'])
    
    # If full_name not provided, use the part before @ in email
    full_name = data.get('full_name', data['email'].split('@')[0].title())
    
    new_user = User(
        email=data['email'],
        password=hashed_pwd,
        full_name=full_name
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        "message": "User registered successfully",
        "user_id": new_user.id
    }), 201

# ──────────────────────────────────────────────
# POST /login — Authenticate user & return JWT
# Rate limited to 5 per minute (brute-force protection)
# ──────────────────────────────────────────────
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400
        
    user = User.query.filter_by(email=data['email']).first()
    
    # SECURITY: Generic error message — never reveal if email exists or not
    if not user or not check_password(data['password'], user.password):
        return jsonify({"error": "Invalid email or password"}), 401
        
    # Generate JWT token (valid for 24 hours)
    token = jwt.encode({
        'user_id': user.id,
        'email': user.email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        "message": "Login successful",
        "token": token
    }), 200

# ──────────────────────────────────────────────
# POST /logout — Invalidate JWT token (blacklist it)
# ──────────────────────────────────────────────
@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(" ")[1]
    
    # Add token to blacklist so it can never be used again
    blacklisted_token = BlacklistedToken(token=token)
    db.session.add(blacklisted_token)
    db.session.commit()
    
    return jsonify({"message": "Successfully logged out"}), 200
