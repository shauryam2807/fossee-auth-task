from flask import Blueprint, jsonify
from app.models import File
from app.middleware.auth_middleware import token_required

files_bp = Blueprint('files', __name__)

# ──────────────────────────────────────────────
# GET /files — Get ALL files of the current user
# Protected route: requires valid JWT token
# ──────────────────────────────────────────────
@files_bp.route('/files', methods=['GET'])
@token_required
def get_all_files(current_user):
    # Only fetch files belonging to the authenticated user (data isolation)
    files = File.query.filter_by(user_id=current_user.id).all()
    
    file_list = [{
        "id": file.id,
        "filename": file.filename,
        "file_size": file.file_size,
        "uploaded_at": file.uploaded_at.isoformat() if file.uploaded_at else None
    } for file in files]
        
    return jsonify({"files": file_list, "count": len(file_list)}), 200

# ──────────────────────────────────────────────
# GET /files/:id — Get a specific file by ID
# SECURITY: Must reject other users' files with 403
#           Must reject non-existent files with 404
# ──────────────────────────────────────────────
@files_bp.route('/files/<int:file_id>', methods=['GET'])
@token_required
def get_file(current_user, file_id):
    file = File.query.get(file_id)
    
    # 404: File does not exist at all
    if not file:
        return jsonify({"error": "File not found"}), 404
        
    # 403: File exists but belongs to another user (DISTINCT from 404!)
    if file.user_id != current_user.id:
        return jsonify({"error": "Access denied — this file does not belong to you"}), 403
        
    return jsonify({
        "id": file.id,
        "filename": file.filename,
        "file_size": file.file_size,
        "file_path": file.file_path,
        "uploaded_at": file.uploaded_at.isoformat() if file.uploaded_at else None
    }), 200
