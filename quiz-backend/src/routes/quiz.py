from flask import Blueprint, request, jsonify, current_app
from src.models.user import db, Quiz, Question, User, UserSession, UserAnswer
from src.routes.user import token_required, admin_required
from datetime import datetime, timedelta
from sqlalchemy import func

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/admin/stats', methods=['GET'])
@token_required
@admin_required
def get_admin_stats(current_user):
    """Get admin dashboard statistics"""
    try:
        # Count total users
        total_users = User.query.count()
        
        # Count total quizzes
        total_quizzes = Quiz.query.count()
        
        # Count total sessions
        total_sessions = UserSession.query.count()
        
        # Calculate average score
        avg_score_query = db.session.query(func.avg(UserAnswer.is_correct * 100)).scalar()
        average_score = round(avg_score_query, 1) if avg_score_query else 0
        
        # Count active users (users who have taken a quiz in the last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        active_users = UserSession.query.filter(
            UserSession.start_time >= yesterday
        ).distinct(UserSession.user_id).count()
        
        return jsonify({
            'success': True,
            'data': {
                'totalUsers': total_users,
                'totalQuizzes': total_quizzes,
                'totalSessions': total_sessions,
                'averageScore': average_score,
                'activeUsers': active_users
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': f'Failed to get stats: {str(e)}'}
        }), 500

# Public Quiz Endpoints (for users)

@quiz_bp.route('/quizzes', methods=['GET'])
@token_required
def get_available_quizzes(current_user):
    """Get all available quizzes for users"""
    try:
        quizzes = Quiz.query.filter_by(is_active=True).all()
        available_quizzes = [quiz.to_dict() for quiz in quizzes if quiz.is_available()]
        
        return jsonify({
            'success': True,
            'data': available_quizzes,
            'message': 'Available quizzes retrieved'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@quiz_bp.route('/quizzes/<int:quiz_id>', methods=['GET'])
@token_required
def get_quiz_info(current_user, quiz_id):
    """Get quiz information (without questions)"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        if not quiz.is_available():
            return jsonify({'success': False, 'error': {'message': 'Quiz is not available'}}), 403
        
        return jsonify({
            'success': True,
            'data': quiz.to_dict(),
            'message': 'Quiz information retrieved'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@quiz_bp.route('/quizzes/<int:quiz_id>/start', methods=['POST'])
@token_required
def start_quiz(current_user, quiz_id):
    """Start a new quiz session"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        if not quiz.is_available():
            return jsonify({'success': False, 'error': {'message': 'Quiz is not available'}}), 403
        
        # Check if user already has an active session for this quiz
        existing_session = UserSession.query.filter_by(
            user_id=current_user.id,
            quiz_id=quiz_id,
            is_completed=False
        ).first()
        
        if existing_session and existing_session.is_active():
            return jsonify({
                'success': True,
                'data': existing_session.to_dict(),
                'message': 'Existing active session found'
            }), 200
        
        # Create new session
        session = UserSession(
            user_id=current_user.id,
            quiz_id=quiz_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        # Set end time based on quiz duration
        session.end_time = datetime.utcnow().replace(
            second=0, microsecond=0
        ) + timedelta(minutes=quiz.duration_minutes)
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': session.to_dict(),
            'message': 'Quiz session started'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

# Admin Quiz Management Endpoints

@quiz_bp.route('/admin/quizzes', methods=['GET'])
@token_required
@admin_required
def get_all_quizzes(current_user):
    """Get all quizzes (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        quizzes = Quiz.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'quizzes': [quiz.to_dict() for quiz in quizzes.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': quizzes.total,
                    'pages': quizzes.pages
                }
            },
            'message': 'Quizzes retrieved successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@quiz_bp.route('/admin/quizzes', methods=['POST'])
@token_required
@admin_required
def create_quiz(current_user):
    """Create a new quiz (admin only)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': {'message': 'No data provided'}}), 400
        
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        duration_minutes = data.get('duration_minutes')
        
        if not title or not duration_minutes:
            return jsonify({'success': False, 'error': {'message': 'Title and duration are required'}}), 400
        
        quiz = Quiz(
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            per_question_time_seconds=data.get('per_question_time_seconds'),
            randomize_questions=data.get('randomize_questions', False),
            randomize_options=data.get('randomize_options', False),
            created_by=current_user.id,
            start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': quiz.to_dict(),
            'message': 'Quiz created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@quiz_bp.route('/admin/quizzes/<int:quiz_id>', methods=['GET'])
@token_required
@admin_required
def get_quiz_details(current_user, quiz_id):
    """Get quiz details with questions (admin only)"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        return jsonify({
            'success': True,
            'data': quiz.to_dict(include_questions=True),
            'message': 'Quiz details retrieved'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@quiz_bp.route('/admin/quizzes/<int:quiz_id>', methods=['PUT'])
@token_required
@admin_required
def update_quiz(current_user, quiz_id):
    """Update quiz (admin only)"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': {'message': 'No data provided'}}), 400
        
        # Update allowed fields
        if 'title' in data:
            quiz.title = data['title'].strip()
        if 'description' in data:
            quiz.description = data['description'].strip()
        if 'duration_minutes' in data:
            quiz.duration_minutes = data['duration_minutes']
        if 'per_question_time_seconds' in data:
            quiz.per_question_time_seconds = data['per_question_time_seconds']
        if 'randomize_questions' in data:
            quiz.randomize_questions = data['randomize_questions']
        if 'randomize_options' in data:
            quiz.randomize_options = data['randomize_options']
        if 'is_active' in data:
            quiz.is_active = data['is_active']
        if 'start_time' in data:
            quiz.start_time = datetime.fromisoformat(data['start_time']) if data['start_time'] else None
        if 'end_time' in data:
            quiz.end_time = datetime.fromisoformat(data['end_time']) if data['end_time'] else None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': quiz.to_dict(),
            'message': 'Quiz updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@quiz_bp.route('/admin/quizzes/<int:quiz_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_quiz(current_user, quiz_id):
    """Delete quiz (admin only)"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Soft delete by deactivating
        quiz.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quiz deactivated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

# Question Management Endpoints

@quiz_bp.route('/admin/questions/<int:quiz_id>', methods=['GET'])
@token_required
@admin_required
def get_quiz_questions(current_user, quiz_id):
    """Get all questions for a quiz (admin only)"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        questions = Question.query.filter_by(quiz_id=quiz_id).order_by(Question.question_order).all()
        
        return jsonify({
            'success': True,
            'data': [question.to_dict(include_correct_answer=True) for question in questions],
            'message': 'Questions retrieved successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@quiz_bp.route('/admin/questions', methods=['POST'])
@token_required
@admin_required
def create_question(current_user):
    """Create a new question (admin only)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': {'message': 'No data provided'}}), 400
        
        required_fields = ['quiz_id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': {'message': f'{field} is required'}}), 400
        
        # Validate correct answer
        if data['correct_answer'] not in ['a', 'b', 'c', 'd']:
            return jsonify({'success': False, 'error': {'message': 'Correct answer must be a, b, c, or d'}}), 400
        
        # Check if quiz exists
        quiz = Quiz.query.get_or_404(data['quiz_id'])
        
        # Get next question order
        max_order = db.session.query(db.func.max(Question.question_order)).filter_by(quiz_id=data['quiz_id']).scalar() or 0
        
        question = Question(
            quiz_id=data['quiz_id'],
            question_text=data['question_text'],
            option_a=data['option_a'],
            option_b=data['option_b'],
            option_c=data['option_c'],
            option_d=data['option_d'],
            correct_answer=data['correct_answer'],
            question_order=max_order + 1,
            time_bonus_factor=data.get('time_bonus_factor', 1.0)
        )
        
        db.session.add(question)
        
        # Update quiz total questions count
        quiz.total_questions = len(quiz.questions) + 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': question.to_dict(include_correct_answer=True),
            'message': 'Question created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@quiz_bp.route('/admin/questions/<int:question_id>', methods=['PUT'])
@token_required
@admin_required
def update_question(current_user, question_id):
    """Update question (admin only)"""
    try:
        question = Question.query.get_or_404(question_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': {'message': 'No data provided'}}), 400
        
        # Update allowed fields
        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'option_a' in data:
            question.option_a = data['option_a']
        if 'option_b' in data:
            question.option_b = data['option_b']
        if 'option_c' in data:
            question.option_c = data['option_c']
        if 'option_d' in data:
            question.option_d = data['option_d']
        if 'correct_answer' in data:
            if data['correct_answer'] not in ['a', 'b', 'c', 'd']:
                return jsonify({'success': False, 'error': {'message': 'Correct answer must be a, b, c, or d'}}), 400
            question.correct_answer = data['correct_answer']
        if 'question_order' in data:
            question.question_order = data['question_order']
        if 'time_bonus_factor' in data:
            question.time_bonus_factor = data['time_bonus_factor']
        
        # Clear image paths if text changed (will be regenerated)
        if any(field in data for field in ['question_text', 'option_a', 'option_b', 'option_c', 'option_d']):
            question.question_image_path = None
            question.options_image_path = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': question.to_dict(include_correct_answer=True),
            'message': 'Question updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@quiz_bp.route('/admin/questions/<int:question_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_question(current_user, question_id):
    """Delete question (admin only)"""
    try:
        question = Question.query.get_or_404(question_id)
        quiz = question.quiz
        
        db.session.delete(question)
        
        # Update quiz total questions count
        quiz.total_questions = len(quiz.questions) - 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Question deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@quiz_bp.route('/admin/quizzes/<int:quiz_id>/upload', methods=['POST'])
@token_required
@admin_required
def bulk_upload_questions(current_user, quiz_id):
    """Bulk upload questions from CSV (admin only)"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': {'message': 'No file provided'}}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': {'message': 'No file selected'}}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': {'message': 'Only CSV files are supported'}}), 400
        
        # Read CSV content
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        questions_created = 0
        errors = []
        
        # Get current max order
        max_order = db.session.query(db.func.max(Question.question_order)).filter_by(quiz_id=quiz_id).scalar() or 0
        
        for row_num, row in enumerate(csv_input, start=2):  # Start at 2 because row 1 is header
            try:
                # Validate required fields
                required_fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
                missing_fields = [field for field in required_fields if not row.get(field, '').strip()]
                
                if missing_fields:
                    errors.append(f"Row {row_num}: Missing fields: {', '.join(missing_fields)}")
                    continue
                
                # Validate correct answer
                correct_answer = row['correct_answer'].strip().lower()
                if correct_answer not in ['a', 'b', 'c', 'd']:
                    errors.append(f"Row {row_num}: Correct answer must be a, b, c, or d")
                    continue
                
                max_order += 1
                
                question = Question(
                    quiz_id=quiz_id,
                    question_text=row['question_text'].strip(),
                    option_a=row['option_a'].strip(),
                    option_b=row['option_b'].strip(),
                    option_c=row['option_c'].strip(),
                    option_d=row['option_d'].strip(),
                    correct_answer=correct_answer,
                    question_order=max_order,
                    time_bonus_factor=float(row.get('time_bonus_factor', 1.0))
                )
                
                db.session.add(question)
                questions_created += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        if questions_created > 0:
            # Update quiz total questions count
            quiz.total_questions = len(quiz.questions) + questions_created
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'questions_created': questions_created,
                'errors': errors
            },
            'message': f'Bulk upload completed. {questions_created} questions created.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

