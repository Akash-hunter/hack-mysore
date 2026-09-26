import os

files = {
    "backend/app/models/profile_snapshot.py": """from app.extensions import db
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
        }""",

    "backend/app/services/profile_engine.py": """from app.extensions import db
from app.models.student import Student
from app.models.skill import Skill, student_skill
from app.models.evidence import Evidence
from app.models.profile_snapshot import ProfileSnapshot
from sqlalchemy.sql import func
import json

class ProfileEngine:
    @staticmethod
    def calculate_skill_proficiency(student_id, skill_id):
        # 1. Fetch all evidence for this student and skill
        evidence_items = Evidence.query.filter_by(student_id=student_id, skill_id=skill_id).all()
        
        if not evidence_items:
            return 0
            
        # 2. Base algorithm: sum the weights (can be made much more complex)
        total_weight = sum(item.weight for item in evidence_items)
        
        # 3. Normalize score out of 100 or 1-5 level
        # This is a very basic normalization for demonstration
        proficiency_level = min(5, max(1, int(total_weight / 10))) 
        return proficiency_level

    @staticmethod
    def recalculate_profile(student_id):
        # Triggered when new evidence is added
        student = Student.query.get(student_id)
        if not student:
            return None
            
        # 1. Get all distinct skills the student has evidence for
        distinct_skills = db.session.query(Evidence.skill_id).filter_by(student_id=student_id).distinct().all()
        
        profile_data = {
            "skills": {}
        }
        
        for (skill_id,) in distinct_skills:
            if skill_id is None:
                continue
                
            # 2. Calculate proficiency
            proficiency = ProfileEngine.calculate_skill_proficiency(student_id, skill_id)
            
            # 3. Update the student_skill association table
            # (In a real app, you'd use raw SQL or SQLAlchemy Core to upsert easily)
            # This is simplified:
            stmt = student_skill.update().where(
                student_skill.c.student_id == student_id
            ).where(
                student_skill.c.skill_id == skill_id
            ).values(proficiency_level=proficiency)
            db.session.execute(stmt)
            
            skill = Skill.query.get(skill_id)
            profile_data["skills"][skill.name] = proficiency
            
        # 4. Save snapshot
        snapshot = ProfileSnapshot(student_id=student_id, profile_data=profile_data)
        db.session.add(snapshot)
        
        db.session.commit()
        return profile_data"""
}

# Update __init__.py in models
with open("backend/app/models/__init__.py", "a") as f:
    f.write("from .profile_snapshot import ProfileSnapshot\n")

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)

print("Stage 5 dynamic profile engine and models generated.")
