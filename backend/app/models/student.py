from app.extensions import db
from datetime import datetime

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)
    github_url = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    projects = db.relationship('Project', backref='student', lazy=True)
    experiences = db.relationship('Experience', backref='student', lazy=True)
    certifications = db.relationship('Certification', backref='student', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'bio': self.bio,
            'github_url': self.github_url,
            'linkedin_url': self.linkedin_url
        }