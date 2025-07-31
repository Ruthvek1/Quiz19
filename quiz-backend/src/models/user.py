from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    created_quizzes = db.relationship('Quiz', backref='creator', lazy=True)
    sessions = db.relationship('UserSession', backref='user', lazy=True)
    results = db.relationship('QuizResult', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, nullable=False)  # Global timer
    per_question_time_seconds = db.Column(db.Integer)  # Optional per-question timer
    total_questions = db.Column(db.Integer, default=0)
    randomize_questions = db.Column(db.Boolean, default=False)
    randomize_options = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.DateTime)  # When quiz becomes available
    end_time = db.Column(db.DateTime)    # When quiz closes
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', backref='quiz', lazy=True)
    results = db.relationship('QuizResult', backref='quiz', lazy=True)

    def __repr__(self):
        return f'<Quiz {self.title}>'

    def is_available(self):
        """Check if quiz is currently available"""
        now = datetime.utcnow()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return self.is_active

    def to_dict(self, include_questions=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'per_question_time_seconds': self.per_question_time_seconds,
            'total_questions': self.total_questions,
            'randomize_questions': self.randomize_questions,
            'randomize_options': self.randomize_options,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_available': self.is_available()
        }
        
        if include_questions:
            data['questions'] = [q.to_dict() for q in self.questions]
            
        return data

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_image_path = db.Column(db.String(255))  # Generated image path
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    option_d = db.Column(db.String(500), nullable=False)
    options_image_path = db.Column(db.String(255))  # Generated image path for options
    correct_answer = db.Column(db.String(1), nullable=False)  # 'a', 'b', 'c', or 'd'
    question_order = db.Column(db.Integer, default=0)
    time_bonus_factor = db.Column(db.Float, default=1.0)  # Multiplier for time bonus
    
    # Relationships
    answers = db.relationship('UserAnswer', backref='question', lazy=True)

    def __repr__(self):
        return f'<Question {self.id}: {self.question_text[:50]}...>'

    def get_options(self):
        """Get all options as a dictionary"""
        return {
            'a': self.option_a,
            'b': self.option_b,
            'c': self.option_c,
            'd': self.option_d
        }

    def to_dict(self, include_correct_answer=False):
        data = {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'question_text': self.question_text,
            'question_image_path': self.question_image_path,
            'options': self.get_options(),
            'options_image_path': self.options_image_path,
            'question_order': self.question_order,
            'time_bonus_factor': self.time_bonus_factor
        }
        
        if include_correct_answer:
            data['correct_answer'] = self.correct_answer
            
        return data

class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    current_question_index = db.Column(db.Integer, default=0)
    time_remaining = db.Column(db.Integer)  # Seconds remaining
    is_completed = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.Text)
    
    # Relationships
    answers = db.relationship('UserAnswer', backref='session', lazy=True)
    result = db.relationship('QuizResult', backref='session', uselist=False)

    def __init__(self, **kwargs):
        super(UserSession, self).__init__(**kwargs)
        if not self.session_token:
            self.session_token = secrets.token_urlsafe(32)

    def __repr__(self):
        return f'<UserSession {self.session_token}>'

    def is_active(self):
        """Check if session is still active"""
        if self.is_completed:
            return False
        if self.end_time and datetime.utcnow() > self.end_time:
            return False
        return True

    def calculate_time_remaining(self):
        """Calculate remaining time for the session"""
        if not self.quiz or self.is_completed:
            return 0
        
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        total_time = self.quiz.duration_minutes * 60
        remaining = max(0, total_time - elapsed)
        
        self.time_remaining = int(remaining)
        return self.time_remaining

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'quiz_id': self.quiz_id,
            'session_token': self.session_token,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'current_question_index': self.current_question_index,
            'time_remaining': self.calculate_time_remaining(),
            'is_completed': self.is_completed,
            'is_active': self.is_active()
        }

class UserAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('user_session.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_answer = db.Column(db.String(1))  # 'a', 'b', 'c', 'd' or null if unanswered
    time_taken_seconds = db.Column(db.Integer)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_correct = db.Column(db.Boolean)

    def __repr__(self):
        return f'<UserAnswer {self.session_id}-{self.question_id}: {self.selected_answer}>'

    def calculate_is_correct(self):
        """Calculate if the answer is correct"""
        if self.selected_answer and self.question:
            self.is_correct = self.selected_answer == self.question.correct_answer
        else:
            self.is_correct = False
        return self.is_correct

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'question_id': self.question_id,
            'selected_answer': self.selected_answer,
            'time_taken_seconds': self.time_taken_seconds,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None,
            'is_correct': self.is_correct
        }

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('user_session.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    total_score = db.Column(db.Float, default=0.0)
    accuracy_score = db.Column(db.Integer, default=0)  # Correct answers count
    time_bonus_score = db.Column(db.Float, default=0.0)
    total_time_taken = db.Column(db.Integer)  # Total seconds taken
    questions_attempted = db.Column(db.Integer, default=0)
    questions_correct = db.Column(db.Integer, default=0)
    completion_percentage = db.Column(db.Float, default=0.0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<QuizResult {self.user_id}-{self.quiz_id}: {self.total_score}>'

    def calculate_scores(self):
        """Calculate all scores based on session answers"""
        if not self.session or not self.session.answers:
            return
        
        answers = self.session.answers
        total_questions = len(self.session.quiz.questions)
        
        # Count correct answers and calculate accuracy
        correct_count = sum(1 for answer in answers if answer.is_correct)
        attempted_count = sum(1 for answer in answers if answer.selected_answer is not None)
        
        self.accuracy_score = correct_count
        self.questions_attempted = attempted_count
        self.questions_correct = correct_count
        self.completion_percentage = (attempted_count / total_questions * 100) if total_questions > 0 else 0
        
        # Calculate time bonus
        time_bonus = 0.0
        for answer in answers:
            if answer.is_correct and answer.time_taken_seconds:
                # Bonus for answering quickly (0.1 point per second saved from 30 seconds)
                max_time = 30  # Maximum time for full bonus
                time_saved = max(0, max_time - answer.time_taken_seconds)
                bonus_factor = answer.question.time_bonus_factor if answer.question else 1.0
                time_bonus += time_saved * 0.1 * bonus_factor
        
        self.time_bonus_score = time_bonus
        self.total_score = self.accuracy_score + self.time_bonus_score
        
        # Calculate total time taken
        if self.session.start_time and self.session.end_time:
            self.total_time_taken = int((self.session.end_time - self.session.start_time).total_seconds())

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'quiz_id': self.quiz_id,
            'total_score': self.total_score,
            'accuracy_score': self.accuracy_score,
            'time_bonus_score': self.time_bonus_score,
            'total_time_taken': self.total_time_taken,
            'questions_attempted': self.questions_attempted,
            'questions_correct': self.questions_correct,
            'completion_percentage': self.completion_percentage,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }

class AdminLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target_id = db.Column(db.Integer)  # ID of affected resource
    details = db.Column(db.Text)  # JSON field with action details
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    admin = db.relationship('User', backref='admin_logs')

    def __repr__(self):
        return f'<AdminLog {self.admin_id}: {self.action}>'

    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'action': self.action,
            'target_id': self.target_id,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
