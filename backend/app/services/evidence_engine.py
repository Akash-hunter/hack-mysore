from app.models.evidence import Evidence
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
        return evidence