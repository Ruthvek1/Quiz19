import json
import jwt
from datetime import datetime, timedelta
from flask import request, current_app
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from src.models.user import db, User, Quiz, UserSession, UserAnswer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global SocketIO instance (will be initialized in main.py)
socketio = None

# Store active quiz sessions and their timers
active_sessions = {}
quiz_rooms = {}  # quiz_id -> list of session_tokens

def verify_token(token):
    """Verify JWT token and return user data"""
    try:
        if token.startswith('Bearer '):
            token = token[7:]
        
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.query.get(data['user_id'])
        
        if not user or not user.is_active:
            return None
        
        return {
            'user_id': user.id,
            'username': user.username,
            'role': user.role
        }
        
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
    
    # Register event handlers
    register_handlers()
    
    return socketio

def register_handlers():
    """Register all WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection"""
        try:
            logger.info(f"Client connecting: {request.sid}")
            
            # Verify authentication
            token = auth.get('token') if auth else None
            if not token:
                logger.warning("Connection rejected: No token provided")
                disconnect()
                return False
            
            user_data = verify_token(token)
            if not user_data:
                logger.warning("Connection rejected: Invalid token")
                disconnect()
                return False
            
            logger.info(f"User {user_data['username']} connected with session {request.sid}")
            emit('connected', {'message': 'Connected successfully', 'user': user_data})
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            disconnect()
            return False
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid}")
        
        # Remove from any quiz rooms
        for quiz_id, sessions in quiz_rooms.items():
            if request.sid in sessions:
                sessions.remove(request.sid)
                break
    
    @socketio.on('join_quiz')
    def handle_join_quiz(data):
        """Handle user joining a quiz session"""
        try:
            session_token = data.get('session_token')
            if not session_token:
                emit('error', {'message': 'Session token required'})
                return
            
            # Verify session exists
            session = UserSession.query.filter_by(session_token=session_token).first()
            if not session:
                emit('error', {'message': 'Invalid session'})
                return
            
            # Join the quiz room
            room = f"quiz_{session.quiz_id}"
            join_room(room)
            
            # Track the session
            if session.quiz_id not in quiz_rooms:
                quiz_rooms[session.quiz_id] = []
            if request.sid not in quiz_rooms[session.quiz_id]:
                quiz_rooms[session.quiz_id].append(request.sid)
            
            # Store session info
            active_sessions[request.sid] = {
                'session_token': session_token,
                'quiz_id': session.quiz_id,
                'user_id': session.user_id,
                'start_time': session.start_time,
                'room': room
            }
            
            logger.info(f"User joined quiz {session.quiz_id} with session {session_token}")
            
            # Send current quiz state
            quiz = Quiz.query.get(session.quiz_id)
            time_remaining = calculate_time_remaining(session, quiz)
            
            emit('quiz_joined', {
                'quiz_id': session.quiz_id,
                'quiz_title': quiz.title,
                'time_remaining': time_remaining,
                'current_question_index': session.current_question_index,
                'total_questions': quiz.total_questions
            })
            
            # Notify others in the room
            emit('user_joined', {
                'user_id': session.user_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"Error joining quiz: {e}")
            emit('error', {'message': 'Failed to join quiz'})
    
    @socketio.on('leave_quiz')
    def handle_leave_quiz():
        """Handle user leaving a quiz session"""
        try:
            if request.sid in active_sessions:
                session_info = active_sessions[request.sid]
                room = session_info['room']
                quiz_id = session_info['quiz_id']
                
                # Leave the room
                leave_room(room)
                
                # Remove from tracking
                if quiz_id in quiz_rooms and request.sid in quiz_rooms[quiz_id]:
                    quiz_rooms[quiz_id].remove(request.sid)
                
                # Notify others
                emit('user_left', {
                    'user_id': session_info['user_id'],
                    'timestamp': datetime.utcnow().isoformat()
                }, room=room)
                
                # Clean up
                del active_sessions[request.sid]
                
                logger.info(f"User left quiz {quiz_id}")
                
        except Exception as e:
            logger.error(f"Error leaving quiz: {e}")
    
    @socketio.on('submit_answer')
    def handle_submit_answer(data):
        """Handle answer submission with real-time feedback"""
        try:
            if request.sid not in active_sessions:
                emit('error', {'message': 'Not in an active quiz session'})
                return
            
            session_info = active_sessions[request.sid]
            session_token = session_info['session_token']
            
            # Get session from database
            session = UserSession.query.filter_by(session_token=session_token).first()
            if not session:
                emit('error', {'message': 'Session not found'})
                return
            
            question_id = data.get('question_id')
            selected_answer = data.get('selected_answer')
            time_taken = data.get('time_taken', 0)
            
            if not question_id or not selected_answer:
                emit('error', {'message': 'Question ID and answer required'})
                return
            
            # Save the answer
            existing_answer = UserAnswer.query.filter_by(
                session_id=session.id,
                question_id=question_id
            ).first()
            
            if existing_answer:
                # Update existing answer
                existing_answer.selected_answer = selected_answer
                existing_answer.time_taken = time_taken
                existing_answer.answered_at = datetime.utcnow()
            else:
                # Create new answer
                answer = UserAnswer(
                    session_id=session.id,
                    question_id=question_id,
                    selected_answer=selected_answer,
                    time_taken=time_taken
                )
                db.session.add(answer)
            
            db.session.commit()
            
            # Send confirmation
            emit('answer_submitted', {
                'question_id': question_id,
                'selected_answer': selected_answer,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Answer submitted for question {question_id} by user {session.user_id}")
            
        except Exception as e:
            logger.error(f"Error submitting answer: {e}")
            emit('error', {'message': 'Failed to submit answer'})
    
    @socketio.on('next_question')
    def handle_next_question(data):
        """Handle moving to next question"""
        try:
            if request.sid not in active_sessions:
                emit('error', {'message': 'Not in an active quiz session'})
                return
            
            session_info = active_sessions[request.sid]
            session_token = session_info['session_token']
            
            # Get session from database
            session = UserSession.query.filter_by(session_token=session_token).first()
            if not session:
                emit('error', {'message': 'Session not found'})
                return
            
            new_index = data.get('question_index')
            if new_index is None:
                emit('error', {'message': 'Question index required'})
                return
            
            # Update current question index
            session.current_question_index = new_index
            db.session.commit()
            
            # Update local tracking
            active_sessions[request.sid]['current_question_index'] = new_index
            
            emit('question_changed', {
                'question_index': new_index,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error changing question: {e}")
            emit('error', {'message': 'Failed to change question'})
    
    @socketio.on('request_time_sync')
    def handle_time_sync():
        """Handle time synchronization request"""
        try:
            if request.sid not in active_sessions:
                emit('error', {'message': 'Not in an active quiz session'})
                return
            
            session_info = active_sessions[request.sid]
            session_token = session_info['session_token']
            
            # Get session from database
            session = UserSession.query.filter_by(session_token=session_token).first()
            if not session:
                emit('error', {'message': 'Session not found'})
                return
            
            quiz = Quiz.query.get(session.quiz_id)
            time_remaining = calculate_time_remaining(session, quiz)
            
            emit('time_sync', {
                'time_remaining': time_remaining,
                'server_time': datetime.utcnow().isoformat(),
                'quiz_duration': quiz.duration_minutes * 60
            })
            
        except Exception as e:
            logger.error(f"Error syncing time: {e}")
            emit('error', {'message': 'Failed to sync time'})
    
    @socketio.on('finish_quiz')
    def handle_finish_quiz():
        """Handle quiz completion"""
        try:
            if request.sid not in active_sessions:
                emit('error', {'message': 'Not in an active quiz session'})
                return
            
            session_info = active_sessions[request.sid]
            session_token = session_info['session_token']
            
            # Get session from database
            session = UserSession.query.filter_by(session_token=session_token).first()
            if not session:
                emit('error', {'message': 'Session not found'})
                return
            
            # Mark session as completed
            session.is_completed = True
            session.end_time = datetime.utcnow()
            db.session.commit()
            
            # Calculate final score
            score_data = calculate_final_score(session)
            
            emit('quiz_completed', {
                'session_token': session_token,
                'score': score_data,
                'completion_time': session.end_time.isoformat()
            })
            
            # Leave the quiz room
            handle_leave_quiz()
            
            logger.info(f"Quiz completed by user {session.user_id} with score {score_data['total_score']}")
            
        except Exception as e:
            logger.error(f"Error finishing quiz: {e}")
            emit('error', {'message': 'Failed to finish quiz'})

def calculate_time_remaining(session, quiz):
    """Calculate remaining time for a quiz session"""
    if session.is_completed:
        return 0
    
    elapsed = datetime.utcnow() - session.start_time
    total_duration = timedelta(minutes=quiz.duration_minutes)
    remaining = total_duration - elapsed
    
    return max(0, int(remaining.total_seconds()))

def calculate_final_score(session):
    """Calculate the final score for a completed session"""
    try:
        quiz = Quiz.query.get(session.quiz_id)
        answers = UserAnswer.query.filter_by(session_id=session.id).all()
        
        total_score = 0
        correct_answers = 0
        total_questions = len(answers)
        
        for answer in answers:
            question = answer.question
            if answer.selected_answer == question.correct_answer:
                correct_answers += 1
                # Base score of 1 point
                score = 1
                
                # Time bonus calculation
                if answer.time_taken and question.time_limit:
                    time_saved = question.time_limit - answer.time_taken
                    if time_saved > 0:
                        # 0.1 point per second saved
                        time_bonus = min(0.5, time_saved * 0.1)  # Max 0.5 bonus
                        score += time_bonus
                
                total_score += score
        
        accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        return {
            'total_score': round(total_score, 2),
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'accuracy': round(accuracy, 2),
            'completion_time': session.end_time.isoformat() if session.end_time else None
        }
        
    except Exception as e:
        logger.error(f"Error calculating score: {e}")
        return {
            'total_score': 0,
            'correct_answers': 0,
            'total_questions': 0,
            'accuracy': 0,
            'completion_time': None
        }

def broadcast_quiz_update(quiz_id, event, data):
    """Broadcast an update to all users in a quiz"""
    if socketio and quiz_id in quiz_rooms:
        room = f"quiz_{quiz_id}"
        socketio.emit(event, data, room=room)

def get_active_users_count(quiz_id):
    """Get the number of active users in a quiz"""
    return len(quiz_rooms.get(quiz_id, []))

