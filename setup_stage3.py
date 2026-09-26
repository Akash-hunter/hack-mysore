import os

files = {
    "backend/app/models/student.py": """from app.extensions import db
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
        }""",

    "backend/app/models/recruiter.py": """from app.extensions import db
from datetime import datetime

class Recruiter(db.Model):
    __tablename__ = 'recruiters'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    position = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('recruiter_profile', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'position': self.position
        }""",

    "backend/app/models/institution.py": """from app.extensions import db
from datetime import datetime

class Institution(db.Model):
    __tablename__ = 'institutions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    contact_person = db.Column(db.String(100))
    website = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('institution_profile', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'contact_person': self.contact_person,
            'website': self.website
        }""",

    "backend/app/models/skill.py": """from app.extensions import db

# Association table for Many-to-Many relationship between Student and Skill
student_skill = db.Table('student_skill',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True),
    db.Column('proficiency_level', db.Integer) # e.g., 1-5
)

class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50)) # e.g., 'Backend', 'Frontend', 'Database'
    
    students = db.relationship('Student', secondary=student_skill, lazy='subquery',
        backref=db.backref('skills', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category
        }""",

    "backend/app/models/project.py": """from app.extensions import db
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
        }""",

    "backend/app/models/experience.py": """from app.extensions import db
from datetime import datetime

class Experience(db.Model):
    __tablename__ = 'experiences'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date, nullable=True)
    is_current = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'company_name': self.company_name,
            'position': self.position,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_current': self.is_current
        }""",

    "backend/app/models/certification.py": """from app.extensions import db
from datetime import datetime

class Certification(db.Model):
    __tablename__ = 'certifications'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    issuing_organization = db.Column(db.String(200), nullable=False)
    issue_date = db.Column(db.Date)
    credential_id = db.Column(db.String(100))
    credential_url = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'issuing_organization': self.issuing_organization,
            'credential_url': self.credential_url
        }""",
        
    "backend/app/models/__init__.py": """from .user import User
from .organization import Organization
from .student import Student
from .recruiter import Recruiter
from .institution import Institution
from .skill import Skill
from .project import Project
from .experience import Experience
from .certification import Certification
"""
}

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)

print("Stage 3 models generated.")
