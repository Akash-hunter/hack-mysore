from app.extensions import db
from datetime import datetime

class Assessment(db.Model):
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiters.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    questions = db.relationship('Question', backref='assessment', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=True) # Tag question to a skill
    
    text = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='MULTIPLE_CHOICE') # 'MULTIPLE_CHOICE', 'CODING', 'SHORT_ANSWER'
    points = db.Column(db.Integer, default=1)
    
    options = db.relationship('QuestionOption', backref='question', lazy=True, cascade="all, delete-orphan")

class QuestionOption(db.Model):
    __tablename__ = 'question_options'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

class TestSession(db.Model):
    __tablename__ = 'test_sessions'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    status = db.Column(db.String(50), default='STARTED') # 'STARTED', 'SUBMITTED', 'EVALUATED'
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Store integrity signals as JSON
    integrity_signals = db.Column(db.JSON)
    integrity_risk_score = db.Column(db.Float, default=0.0) # 0.0 to 100.0
    
    total_score = db.Column(db.Float)
    
    answers = db.relationship('Answer', backref='test_session', lazy=True, cascade="all, delete-orphan")

class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    test_session_id = db.Column(db.Integer, db.ForeignKey('test_sessions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    # For multiple choice, store option ID. For text/code, store text.
    selected_option_id = db.Column(db.Integer, db.ForeignKey('question_options.id'), nullable=True)
    text_response = db.Column(db.Text, nullable=True)
    
    is_correct = db.Column(db.Boolean, nullable=True)
    points_awarded = db.Column(db.Float, default=0)