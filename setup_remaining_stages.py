import os

files = {
    "backend/app/models/hackathon.py": """from app.extensions import db
from datetime import datetime

class Hackathon(db.Model):
    __tablename__ = 'hackathons'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='UPCOMING') # 'UPCOMING', 'ACTIVE', 'COMPLETED'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    problems = db.relationship('HackathonProblem', backref='hackathon', lazy=True)
    participants = db.relationship('HackathonParticipant', backref='hackathon', lazy=True)

class HackathonProblem(db.Model):
    __tablename__ = 'hackathon_problems'
    id = db.Column(db.Integer, primary_key=True)
    hackathon_id = db.Column(db.Integer, db.ForeignKey('hackathons.id'), nullable=False)
    title = db.Column(db.String(200))
    statement = db.Column(db.Text)

class HackathonParticipant(db.Model):
    __tablename__ = 'hackathon_participants'
    id = db.Column(db.Integer, primary_key=True)
    hackathon_id = db.Column(db.Integer, db.ForeignKey('hackathons.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    submissions = db.relationship('HackathonSubmission', backref='participant', lazy=True)

class HackathonSubmission(db.Model):
    __tablename__ = 'hackathon_submissions'
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('hackathon_participants.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('hackathon_problems.id'), nullable=True)
    repository_url = db.Column(db.String(255))
    demo_url = db.Column(db.String(255))
    description = db.Column(db.Text)
    score = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)""",

    "backend/app/models/message.py": """from app.extensions import db
from datetime import datetime

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    messages = db.relationship('Message', backref='conversation', lazy=True)

class ConversationMember(db.Model):
    __tablename__ = 'conversation_members'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)""",

    "backend/app/models/notification.py": """from app.extensions import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50)) # 'MESSAGE', 'ASSESSMENT', 'SYSTEM'
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)""",

    "backend/app/services/analytics_service.py": """from app.models.student import Student
from app.models.application import Application
from app.extensions import db
from sqlalchemy import func

class AnalyticsService:
    @staticmethod
    def get_student_analytics(student_id):
        # Aggregate applications count, test scores, skill growth
        applications_count = Application.query.filter_by(student_id=student_id).count()
        
        return {
            "applications_submitted": applications_count,
            # Placeholder for skill growth from ProfileSnapshots
            "skill_growth_trend": [] 
        }
        
    @staticmethod
    def get_institution_analytics(institution_id):
        # Would join users with organization_id = institution_id
        return {
            "students_placed": 0,
            "average_test_scores": 0
        }""",

    "backend/app/services/ai_service.py": """class AIService:
    @staticmethod
    def analyze_profile(student_id):
        # Hook for calling an LLM (like Gemini or OpenAI) to generate structured feedback
        # on a candidate's profile based on their evidence and skill gaps.
        return {
            "recommendation": "Contribute more to open-source Python projects to improve ranking for Backend roles."
        }
        
    @staticmethod
    def analyze_project(github_repo_data):
        # Hook to analyze a repository's code quality, architecture, and tech stack
        return {
            "complexity_score": 85,
            "tech_stack": ["React", "Node.js"]
        }"""
}

# Update __init__.py in models
with open("backend/app/models/__init__.py", "a") as f:
    f.write("from .hackathon import Hackathon, HackathonProblem, HackathonParticipant, HackathonSubmission\n")
    f.write("from .message import Conversation, ConversationMember, Message\n")
    f.write("from .notification import Notification\n")

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)

print("Remaining stages generated (Hackathons, Communication, Analytics, AI).")
