from functools import wraps
from flask import request, jsonify, current_app
import jwt
from app.models import User, BlacklistedToken

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Token header me "Authorization: Bearer <token>" format me aana chahiye
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
                
        if not token:
            return jsonify({"error": "Token missing hai! Login kijiye."}), 401
            
        try:
            # Check karo ki token blacklist me toh nahi (yani user logout kar chuka hai)
            blacklisted_token = BlacklistedToken.query.filter_by(token=token).first()
            if blacklisted_token:
                return jsonify({"error": "Token expire ho chuka hai (User logged out)"}), 401
                
            # Token decode karke user id nikalo
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({"error": "Token me diya gaya user database me nahi hai!"}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token ka time khatam (expire) ho gaya hai! Wapas login karein."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 401
            
        # Agar sab sahi hai, toh current_user object aage wale function ko bhej do
        return f(current_user, *args, **kwargs)
        
    return decorated
