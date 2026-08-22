from flask import Blueprint, jsonify
from app.middleware.auth_middleware import token_required

user_bp = Blueprint('user', __name__)

# ──────────────────────────────────────────────
# GET /me — Get current logged-in user's profile
# Protected route: requires valid JWT token
# ──────────────────────────────────────────────
@user_bp.route('/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }), 200
