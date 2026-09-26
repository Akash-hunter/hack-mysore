from app.models.student import Student
from app.models.application import Application
from app.extensions import db
from sqlalchemy import func

class AnalyticsService:
    @staticmethod
    def get_student_analytics(student_id):
        # Aggregate applications count, test scores, skill growth
        applications_count = Application.query.filter_by(student_id=student_id).count()
        
        return {
            "applications_submitted": applications_count,
            # Placeholder for skill growth from ProfileSnapshots
            "skill_growth_trend": [] 
        }
        
    @staticmethod
    def get_institution_analytics(institution_id):
        # Would join users with organization_id = institution_id
        return {
            "students_placed": 0,
            "average_test_scores": 0
        }