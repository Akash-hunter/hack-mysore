from app.extensions import db
from datetime import datetime

class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    status = db.Column(db.String(50), default='APPLIED') # 'APPLIED', 'ASSESSMENT', 'INTERVIEW', 'OFFER', 'REJECTED'
    
    # Snapshot of their match score at time of application or latest calculated
    match_score = db.Column(db.Float)
    ranking_position = db.Column(db.Integer)
    
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = db.relationship('Job', backref='applications', lazy=True)
    student = db.relationship('Student', backref='applications', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'student_id': self.student_id,
            'status': self.status,
            'match_score': self.match_score,
            'applied_at': self.applied_at.isoformat()
        }