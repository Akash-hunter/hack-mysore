from app.models.student import Student
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
        
        return is_eligible, match_score