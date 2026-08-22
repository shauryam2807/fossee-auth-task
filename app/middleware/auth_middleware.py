from functools import wraps
from flask import request, jsonify, current_app
import jwt
from app.models import User, BlacklistedToken

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Token must come in "Authorization: Bearer <token>" format
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
                
        if not token:
            return jsonify({"error": "Token missing. Please login."}), 401
            
        try:
            # Check if token is blacklisted (user has logged out)
            blacklisted_token = BlacklistedToken.query.filter_by(token=token).first()
            if blacklisted_token:
                return jsonify({"error": "Token has been invalidated (User logged out)"}), 401
                
            # Decode the token to extract user_id
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({"error": "User not found in database"}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please login again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 401
            
        # All checks passed — pass the current_user to the route handler
        return f(current_user, *args, **kwargs)
        
    return decorated
