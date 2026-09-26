from app.extensions import db
from datetime import datetime

class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiters.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50)) # 'Full-time', 'Internship', 'Contract'
    location = db.Column(db.String(100))
    is_remote = db.Column(db.Boolean, default=False)
    
    # Required skills JSON or comma-separated for simple matching
    required_skills = db.Column(db.JSON) 
    
    status = db.Column(db.String(50), default='OPEN') # 'OPEN', 'CLOSED', 'DRAFT'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)

    organization = db.relationship('Organization', backref='jobs', lazy=True)
    recruiter = db.relationship('Recruiter', backref='posted_jobs', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'type': self.type,
            'organization_id': self.organization_id,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }