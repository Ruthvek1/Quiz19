from flask import Blueprint, request, jsonify
from src.models.user import db, User, Quiz, Question, UserSession, UserAnswer, QuizResult
from src.routes.user import token_required, admin_required
from datetime import datetime, timedelta
import random

session_bp = Blueprint('session', __name__)

@session_bp.route('/sessions/<session_token>', methods=['GET'])
@token_required
def get_session_info(current_user, session_token):
    """Get current session information"""
    try:
        session = UserSession.query.filter_by(session_token=session_token).first_or_404()
        
        # Verify session belongs to current user
        if session.user_id != current_user.id:
            return jsonify({'success': False, 'error': {'message': 'Access denied'}}), 403
        
        if not session.is_active():
            return jsonify({'success': False, 'error': {'message': 'Session has expired'}}), 410
        
        return jsonify({
            'success': True,
            'data': session.to_dict(),
            'message': 'Session information retrieved'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@session_bp.route('/sessions/<session_token>/question', methods=['GET'])
@token_required
def get_current_question(current_user, session_token):
    """Get current question for the session"""
    try:
        session = UserSession.query.filter_by(session_token=session_token).first_or_404()
        
        # Verify session belongs to current user
        if session.user_id != current_user.id:
            return jsonify({'success': False, 'error': {'message': 'Access denied'}}), 403
        
        if not session.is_active():
            return jsonify({'success': False, 'error': {'message': 'Session has expired'}}), 410
        
        quiz = session.quiz
        questions = Question.query.filter_by(quiz_id=quiz.id).order_by(Question.question_order).all()
        
        if not questions:
            return jsonify({'success': False, 'error': {'message': 'No questions found'}}), 404
        
        # Randomize questions if enabled
        if quiz.randomize_questions:
            # Use session ID as seed for consistent randomization per user
            random.seed(session.id)
            questions = random.sample(questions, len(questions))
        
        # Check if current question index is valid
        if session.current_question_index >= len(questions):
            return jsonify({'success': False, 'error': {'message': 'All questions completed'}}), 410
        
        current_question = questions[session.current_question_index]
        
        # Get user's previous answer for this question if any
        previous_answer = UserAnswer.query.filter_by(
            session_id=session.id,
            question_id=current_question.id
        ).first()
        
        # Prepare question data (without correct answer)
        question_data = current_question.to_dict()
        
        # Randomize options if enabled
        if quiz.randomize_options:
            options = question_data['options']
            option_keys = list(options.keys())
            option_values = list(options.values())
            
            # Use question ID + session ID as seed for consistent randomization
            random.seed(current_question.id + session.id)
            random.shuffle(option_values)
            
            # Create mapping for answer conversion
            shuffled_options = dict(zip(option_keys, option_values))
            question_data['options'] = shuffled_options
        
        response_data = {
            'question': question_data,
            'session_info': {
                'current_index': session.current_question_index,
                'total_questions': len(questions),
                'time_remaining': session.calculate_time_remaining(),
                'has_previous': session.current_question_index > 0,
                'has_next': session.current_question_index < len(questions) - 1
            }
        }
        
        # Include previous answer if exists
        if previous_answer:
            response_data['previous_answer'] = previous_answer.to_dict()
        
        return jsonify({
            'success': True,
            'data': response_data,
            'message': 'Current question retrieved'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@session_bp.route('/sessions/<session_token>/answer', methods=['POST'])
@token_required
def submit_answer(current_user, session_token):
    """Submit answer for current question"""
    try:
        session = UserSession.query.filter_by(session_token=session_token).first_or_404()
        
        # Verify session belongs to current user
        if session.user_id != current_user.id:
            return jsonify({'success': False, 'error': {'message': 'Access denied'}}), 403
        
        if not session.is_active():
            return jsonify({'success': False, 'error': {'message': 'Session has expired'}}), 410
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': {'message': 'No data provided'}}), 400
        
        question_id = data.get('question_id')
        selected_answer = data.get('answer', '').lower()
        time_taken = data.get('time_taken', 0)
        
        if not question_id:
            return jsonify({'success': False, 'error': {'message': 'Question ID is required'}}), 400
        
        if selected_answer and selected_answer not in ['a', 'b', 'c', 'd']:
            return jsonify({'success': False, 'error': {'message': 'Answer must be a, b, c, or d'}}), 400
        
        # Verify question belongs to the quiz
        question = Question.query.filter_by(id=question_id, quiz_id=session.quiz_id).first_or_404()
        
        # Check if answer already exists
        existing_answer = UserAnswer.query.filter_by(
            session_id=session.id,
            question_id=question_id
        ).first()
        
        if existing_answer:
            # Update existing answer
            existing_answer.selected_answer = selected_answer if selected_answer else None
            existing_answer.time_taken_seconds = time_taken
            existing_answer.answered_at = datetime.utcnow()
            existing_answer.calculate_is_correct()
            answer = existing_answer
        else:
            # Create new answer
            answer = UserAnswer(
                session_id=session.id,
                question_id=question_id,
                selected_answer=selected_answer if selected_answer else None,
                time_taken_seconds=time_taken
            )
            answer.calculate_is_correct()
            db.session.add(answer)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': answer.to_dict(),
            'message': 'Answer submitted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@session_bp.route('/sessions/<session_token>/next', methods=['POST'])
@token_required
def next_question(current_user, session_token):
    """Move to next question"""
    try:
        session = UserSession.query.filter_by(session_token=session_token).first_or_404()
        
        # Verify session belongs to current user
        if session.user_id != current_user.id:
            return jsonify({'success': False, 'error': {'message': 'Access denied'}}), 403
        
        if not session.is_active():
            return jsonify({'success': False, 'error': {'message': 'Session has expired'}}), 410
        
        quiz = session.quiz
        total_questions = len(quiz.questions)
        
        if session.current_question_index < total_questions - 1:
            session.current_question_index += 1
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'current_index': session.current_question_index,
                    'total_questions': total_questions
                },
                'message': 'Moved to next question'
            }), 200
        else:
            return jsonify({'success': False, 'error': {'message': 'Already at last question'}}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@session_bp.route('/sessions/<session_token>/previous', methods=['POST'])
@token_required
def previous_question(current_user, session_token):
    """Move to previous question"""
    try:
        session = UserSession.query.filter_by(session_token=session_token).first_or_404()
        
        # Verify session belongs to current user
        if session.user_id != current_user.id:
            return jsonify({'success': False, 'error': {'message': 'Access denied'}}), 403
        
        if not session.is_active():
            return jsonify({'success': False, 'error': {'message': 'Session has expired'}}), 410
        
        if session.current_question_index > 0:
            session.current_question_index -= 1
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'current_index': session.current_question_index,
                    'total_questions': len(session.quiz.questions)
                },
                'message': 'Moved to previous question'
            }), 200
        else:
            return jsonify({'success': False, 'error': {'message': 'Already at first question'}}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@session_bp.route('/sessions/<session_token>/submit', methods=['POST'])
@token_required
def submit_quiz(current_user, session_token):
    """Submit entire quiz and calculate results"""
    try:
        session = UserSession.query.filter_by(session_token=session_token).first_or_404()
        
        # Verify session belongs to current user
        if session.user_id != current_user.id:
            return jsonify({'success': False, 'error': {'message': 'Access denied'}}), 403
        
        if session.is_completed:
            return jsonify({'success': False, 'error': {'message': 'Quiz already submitted'}}), 400
        
        # Mark session as completed
        session.is_completed = True
        session.end_time = datetime.utcnow()
        
        # Check if result already exists
        existing_result = QuizResult.query.filter_by(session_id=session.id).first()
        
        if existing_result:
            result = existing_result
        else:
            # Create quiz result
            result = QuizResult(
                session_id=session.id,
                user_id=session.user_id,
                quiz_id=session.quiz_id
            )
            db.session.add(result)
        
        # Calculate scores
        result.calculate_scores()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': result.to_dict(),
            'message': 'Quiz submitted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@session_bp.route('/sessions/<session_token>/result', methods=['GET'])
@token_required
def get_quiz_result(current_user, session_token):
    """Get quiz result"""
    try:
        session = UserSession.query.filter_by(session_token=session_token).first_or_404()
        
        # Verify session belongs to current user
        if session.user_id != current_user.id:
            return jsonify({'success': False, 'error': {'message': 'Access denied'}}), 403
        
        if not session.is_completed:
            return jsonify({'success': False, 'error': {'message': 'Quiz not yet submitted'}}), 400
        
        result = QuizResult.query.filter_by(session_id=session.id).first_or_404()
        
        # Get detailed answer breakdown
        answers = UserAnswer.query.filter_by(session_id=session.id).all()
        answer_details = []
        
        for answer in answers:
            question = answer.question
            answer_detail = {
                'question_id': question.id,
                'question_text': question.question_text,
                'selected_answer': answer.selected_answer,
                'correct_answer': question.correct_answer,
                'is_correct': answer.is_correct,
                'time_taken': answer.time_taken_seconds,
                'options': question.get_options()
            }
            answer_details.append(answer_detail)
        
        response_data = result.to_dict()
        response_data['answer_details'] = answer_details
        response_data['quiz_info'] = session.quiz.to_dict()
        
        return jsonify({
            'success': True,
            'data': response_data,
            'message': 'Quiz result retrieved'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

# Admin Session Monitoring

@session_bp.route('/admin/sessions/active', methods=['GET'])
@token_required
@admin_required
def get_active_sessions(current_user):
    """Get all active sessions (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        quiz_id = request.args.get('quiz_id', type=int)
        
        query = UserSession.query.filter_by(is_completed=False)
        
        if quiz_id:
            query = query.filter_by(quiz_id=quiz_id)
        
        sessions = query.paginate(page=page, per_page=per_page, error_out=False)
        
        session_data = []
        for session in sessions.items:
            data = session.to_dict()
            data['user'] = session.user.to_dict()
            data['quiz'] = session.quiz.to_dict()
            session_data.append(data)
        
        return jsonify({
            'success': True,
            'data': {
                'sessions': session_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': sessions.total,
                    'pages': sessions.pages
                }
            },
            'message': 'Active sessions retrieved'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@session_bp.route('/admin/sessions/<int:session_id>', methods=['GET'])
@token_required
@admin_required
def get_session_details(current_user, session_id):
    """Get detailed session information (admin only)"""
    try:
        session = UserSession.query.get_or_404(session_id)
        
        # Get session answers
        answers = UserAnswer.query.filter_by(session_id=session_id).all()
        
        session_data = session.to_dict()
        session_data['user'] = session.user.to_dict()
        session_data['quiz'] = session.quiz.to_dict()
        session_data['answers'] = [answer.to_dict() for answer in answers]
        
        # Get result if completed
        if session.is_completed:
            result = QuizResult.query.filter_by(session_id=session_id).first()
            if result:
                session_data['result'] = result.to_dict()
        
        return jsonify({
            'success': True,
            'data': session_data,
            'message': 'Session details retrieved'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

@session_bp.route('/admin/analytics/<int:quiz_id>', methods=['GET'])
@token_required
@admin_required
def get_quiz_analytics(current_user, quiz_id):
    """Get quiz analytics (admin only)"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Get all sessions for this quiz
        sessions = UserSession.query.filter_by(quiz_id=quiz_id).all()
        completed_sessions = [s for s in sessions if s.is_completed]
        
        # Get all results
        results = QuizResult.query.filter_by(quiz_id=quiz_id).all()
        
        # Calculate analytics
        analytics = {
            'quiz_info': quiz.to_dict(),
            'total_attempts': len(sessions),
            'completed_attempts': len(completed_sessions),
            'completion_rate': (len(completed_sessions) / len(sessions) * 100) if sessions else 0,
            'average_score': sum(r.total_score for r in results) / len(results) if results else 0,
            'average_time': sum(r.total_time_taken for r in results if r.total_time_taken) / len([r for r in results if r.total_time_taken]) if results else 0,
            'score_distribution': {
                '0-25%': len([r for r in results if r.completion_percentage <= 25]),
                '26-50%': len([r for r in results if 25 < r.completion_percentage <= 50]),
                '51-75%': len([r for r in results if 50 < r.completion_percentage <= 75]),
                '76-100%': len([r for r in results if r.completion_percentage > 75])
            }
        }
        
        # Question-wise analytics
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        question_analytics = []
        
        for question in questions:
            answers = UserAnswer.query.filter_by(question_id=question.id).all()
            correct_answers = [a for a in answers if a.is_correct]
            
            question_stats = {
                'question_id': question.id,
                'question_text': question.question_text[:100] + '...' if len(question.question_text) > 100 else question.question_text,
                'total_attempts': len(answers),
                'correct_attempts': len(correct_answers),
                'accuracy_rate': (len(correct_answers) / len(answers) * 100) if answers else 0,
                'average_time': sum(a.time_taken_seconds for a in answers if a.time_taken_seconds) / len([a for a in answers if a.time_taken_seconds]) if answers else 0
            }
            question_analytics.append(question_stats)
        
        analytics['question_analytics'] = question_analytics
        
        return jsonify({
            'success': True,
            'data': analytics,
            'message': 'Quiz analytics retrieved'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500

