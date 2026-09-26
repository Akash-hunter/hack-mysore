import os

files = {
    "backend/app/models/job.py": """from app.extensions import db
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
        }""",

    "backend/app/models/application.py": """from app.extensions import db
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
        }""",

    "backend/app/services/matching_engine.py": """from app.models.student import Student
from app.models.skill import Skill
from app.models.profile_snapshot import ProfileSnapshot

class MatchingEngine:
    @staticmethod
    def calculate_eligibility(job, student_profile_data):
        # job.required_skills could be {"Python": 3, "SQL": 2} (Skill name : Required Level)
        # student_profile_data is {"skills": {"Python": 4, "SQL": 1}}
        
        if not job.required_skills:
            return True, 100.0 # No requirements, fully eligible
            
        required = job.required_skills
        student_skills = student_profile_data.get('skills', {})
        
        total_reqs = len(required)
        met_reqs = 0
        
        for skill_name, req_level in required.items():
            student_level = student_skills.get(skill_name, 0)
            if student_level >= req_level:
                met_reqs += 1
                
        # Basic match score %
        match_score = (met_reqs / total_reqs) * 100
        
        # Determine if they pass a basic threshold (e.g., 50%)
        is_eligible = match_score >= 50.0
        
        return is_eligible, match_score""",

    "backend/app/services/ranking_engine.py": """class RankingEngine:
    @staticmethod
    def rank_candidates(applications):
        # A simple ranking by match_score descending
        # Real-world would involve weights, recruiter preferences, and AI scoring
        
        ranked = sorted(applications, key=lambda a: (a.match_score or 0), reverse=True)
        
        # Update ranking positions
        for i, app in enumerate(ranked):
            app.ranking_position = i + 1
            
        return ranked"""
}

# Update __init__.py in models
with open("backend/app/models/__init__.py", "a") as f:
    f.write("from .job import Job\n")
    f.write("from .application import Application\n")

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)

print("Stage 6 recruitment models and engines generated.")
