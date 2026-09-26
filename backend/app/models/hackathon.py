from app.extensions import db
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
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)