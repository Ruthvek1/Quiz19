from flask import Blueprint, request, jsonify, current_app
from src.models.user import db, User
import jwt
from datetime import datetime, timedelta
from functools import wraps

user_bp = Blueprint('user', __name__)

def token_required(f):
    """Decorator to require JWT token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'success': False, 'error': {'message': 'Token is missing'}}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            
            if not current_user or not current_user.is_active:
                return jsonify({'success': False, 'error': {'message': 'Invalid token'}}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': {'message': 'Token has expired'}}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'error': {'message': 'Invalid token'}}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': {'message': 'Admin access required'}}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated

@user_bp.route('/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': {'message': 'No data provided'}}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'user')
        
        # Validation
        if not username or not email or not password:
            return jsonify({'success': False, 'error': {'message': 'Username, email, and password are required'}}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': {'message': 'Password must be at least 6 characters'}}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': {'message': 'Username already exists'}}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': {'message': 'Email already exists'}}), 400
        
        # Create new user
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': 'User registered successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@user_bp.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': {'message': 'No data provided'}}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'error': {'message': 'Username and password are required'}}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'error': {'message': 'Invalid credentials'}}), 401
        
        if not user.is_active:
            return jsonify({'success': False, 'error': {'message': 'Account is deactivated'}}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'token': token
            },
            'message': 'Login successful'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@user_bp.route('/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user information"""
    return jsonify({
        'success': True,
        'data': current_user.to_dict(),
        'message': 'User information retrieved'
    }), 200

@user_bp.route('/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """User logout endpoint (client-side token removal)"""
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    }), 200

@user_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    """Get all users (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        users = User.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'users': [user.to_dict() for user in users.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': users.total,
                    'pages': users.pages
                }
            },
            'message': 'Users retrieved successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
@admin_required
def get_user(current_user, user_id):
    """Get specific user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        
        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': 'User retrieved successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(current_user, user_id):
    """Update user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': {'message': 'No data provided'}}), 400
        
        # Update allowed fields
        if 'username' in data:
            username = data['username'].strip()
            if username != user.username:
                if User.query.filter_by(username=username).first():
                    return jsonify({'success': False, 'error': {'message': 'Username already exists'}}), 400
                user.username = username
        
        if 'email' in data:
            email = data['email'].strip()
            if email != user.email:
                if User.query.filter_by(email=email).first():
                    return jsonify({'success': False, 'error': {'message': 'Email already exists'}}), 400
                user.email = email
        
        if 'role' in data:
            user.role = data['role']
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': 'User updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_id):
    """Delete user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent admin from deleting themselves
        if user.id == current_user.id:
            return jsonify({'success': False, 'error': {'message': 'Cannot delete your own account'}}), 400
        
        # Soft delete by deactivating
        user.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User deactivated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500