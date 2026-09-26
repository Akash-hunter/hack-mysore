from app.models.assessment import TestSession, Question, Answer, QuestionOption
from app.extensions import db

class AssessmentEngine:
    @staticmethod
    def evaluate_session(session_id):
        session = TestSession.query.get(session_id)
        if not session:
            return None
            
        total_score = 0
        
        for answer in session.answers:
            question = Question.query.get(answer.question_id)
            
            if question.type == 'MULTIPLE_CHOICE':
                if answer.selected_option_id:
                    option = QuestionOption.query.get(answer.selected_option_id)
                    if option and option.is_correct:
                        answer.is_correct = True
                        answer.points_awarded = question.points
                        total_score += question.points
                    else:
                        answer.is_correct = False
                        answer.points_awarded = 0
            
            # For coding or text answers, AI or manual grading would be hooked in here
        
        session.total_score = total_score
        session.status = 'EVALUATED'
        db.session.commit()
        
        # NOTE: After evaluation, you would call EvidenceEngine 
        # to convert this test score into candidate Evidence.
        
        return session