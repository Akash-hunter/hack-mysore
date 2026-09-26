from app.extensions import db

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
        }