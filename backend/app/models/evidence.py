from app.extensions import db
from datetime import datetime

class Evidence(db.Model):
    __tablename__ = 'evidence'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=True)
    source_type = db.Column(db.String(50), nullable=False) # e.g., 'GITHUB', 'ASSESSMENT', 'PROJECT', 'HACKATHON'
    source_id = db.Column(db.String(100), nullable=True) # external reference id
    
    # Core evidence data
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    weight = db.Column(db.Float, default=1.0) # Importance or confidence of this evidence
    metadata_json = db.Column(db.Text) # Storing raw JSON data or specific metrics
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref='evidence_items', lazy=True)
    skill = db.relationship('Skill', backref='evidence_items', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'skill_id': self.skill_id,
            'source_type': self.source_type,
            'title': self.title,
            'weight': self.weight,
            'created_at': self.created_at.isoformat()
        }