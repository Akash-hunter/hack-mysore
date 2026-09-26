from app.extensions import db
from datetime import datetime

class ExternalSource(db.Model):
    __tablename__ = 'external_sources'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # 'GitHub', 'LinkedIn', 'LeetCode'
    base_url = db.Column(db.String(255))

class ExternalConnection(db.Model):
    __tablename__ = 'external_connections'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('external_sources.id'), nullable=False)
    
    # Authentication / Linking data
    external_user_id = db.Column(db.String(255))
    username = db.Column(db.String(255))
    access_token = db.Column(db.String(500))
    refresh_token = db.Column(db.String(500))
    last_synced = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='external_connections', lazy=True)
    source = db.relationship('ExternalSource', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'source_name': self.source.name if self.source else None,
            'username': self.username,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None
        }