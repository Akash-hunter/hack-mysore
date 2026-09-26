import os
import json

files = {
    "backend/app/models/evidence.py": """from app.extensions import db
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
        }""",

    "backend/app/models/external_connection.py": """from app.extensions import db
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
        }""",

    "backend/app/services/__init__.py": """""",

    "backend/app/services/github_service.py": """class GitHubService:
    @staticmethod
    def connect_github(student_id, auth_code):
        # TODO: Exchange auth_code for access_token, save to ExternalConnection
        pass

    @staticmethod
    def fetch_repositories(access_token):
        # TODO: Call GitHub API to get repos
        pass

    @staticmethod
    def fetch_languages(access_token, repo_name):
        # TODO: Call GitHub API to get languages for a repo
        pass

    @staticmethod
    def sync_github_data(student_id):
        # 1. Fetch connection from db
        # 2. Fetch repos & languages
        # 3. Call Evidence Engine to store/process
        pass""",

    "backend/app/services/evidence_engine.py": """from app.models.evidence import Evidence
from app.extensions import db
import json

class EvidenceEngine:
    @staticmethod
    def process_github_evidence(student_id, github_data):
        # Convert raw github data into Evidence records
        # E.g. finding that student used 'Java' heavily
        pass
        
    @staticmethod
    def record_evidence(student_id, source_type, title, metadata=None, skill_id=None, weight=1.0):
        evidence = Evidence(
            student_id=student_id,
            source_type=source_type,
            title=title,
            skill_id=skill_id,
            weight=weight,
            metadata_json=json.dumps(metadata) if metadata else None
        )
        db.session.add(evidence)
        db.session.commit()
        return evidence"""
}

# Update __init__.py in models
with open("backend/app/models/__init__.py", "a") as f:
    f.write("from .evidence import Evidence\n")
    f.write("from .external_connection import ExternalSource, ExternalConnection\n")

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)

print("Stage 4 evidence models and services generated.")
