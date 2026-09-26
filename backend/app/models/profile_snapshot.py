from app.extensions import db
from datetime import datetime

class ProfileSnapshot(db.Model):
    __tablename__ = 'profile_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    # Store the entire calculated profile state as JSON to keep history
    profile_data = db.Column(db.JSON, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='profile_snapshots', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'profile_data': self.profile_data,
            'created_at': self.created_at.isoformat()
        }