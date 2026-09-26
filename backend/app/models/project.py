from app.extensions import db
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    technologies = db.Column(db.String(255)) # Comma separated or JSON
    repository_url = db.Column(db.String(255))
    documentation_url = db.Column(db.String(255))
    status = db.Column(db.String(50), default='COMPLETED')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'title': self.title,
            'description': self.description,
            'technologies': self.technologies,
            'repository_url': self.repository_url,
            'status': self.status
        }