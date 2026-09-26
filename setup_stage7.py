import os

files = {
    "backend/app/models/assessment.py": """from app.extensions import db
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
    points_awarded = db.Column(db.Float, default=0)""",

    "backend/app/services/assessment_engine.py": """from app.models.assessment import TestSession, Question, Answer, QuestionOption
from app.extensions import db

class AssessmentEngine:
    @staticmethod
    def evaluate_session(session_id):
        session = TestSession.query.get(session_id)
        if not session:
            return None
            
        total_score = 0
        
        for answer in session.answers:
            question = Question.query.get(answer.question_id)
            
            if question.type == 'MULTIPLE_CHOICE':
                if answer.selected_option_id:
                    option = QuestionOption.query.get(answer.selected_option_id)
                    if option and option.is_correct:
                        answer.is_correct = True
                        answer.points_awarded = question.points
                        total_score += question.points
                    else:
                        answer.is_correct = False
                        answer.points_awarded = 0
            
            # For coding or text answers, AI or manual grading would be hooked in here
        
        session.total_score = total_score
        session.status = 'EVALUATED'
        db.session.commit()
        
        # NOTE: After evaluation, you would call EvidenceEngine 
        # to convert this test score into candidate Evidence.
        
        return session""",

    "backend/app/services/integrity_engine.py": """class IntegrityEngine:
    @staticmethod
    def analyze_signals(test_session):
        # Expects test_session.integrity_signals to be a list of events:
        # e.g. [{"type": "tab_switch", "timestamp": "...", "duration": 15}]
        
        signals = test_session.integrity_signals
        if not signals:
            return 0.0 # No risk detected
            
        risk_score = 0.0
        
        for event in signals:
            if event.get('type') == 'tab_switch':
                # Penalize for switching tabs during test
                duration = event.get('duration', 0)
                risk_score += min(10.0, duration * 0.5) 
            
            elif event.get('type') == 'copy_paste':
                risk_score += 15.0
                
            elif event.get('type') == 'focus_lost':
                risk_score += 5.0
                
        # Cap at 100
        test_session.integrity_risk_score = min(100.0, risk_score)
        
        return test_session.integrity_risk_score"""
}

# Update __init__.py in models
with open("backend/app/models/__init__.py", "a") as f:
    f.write("from .assessment import Assessment, Question, QuestionOption, TestSession, Answer\n")

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)

print("Stage 7 assessment models and engines generated.")
