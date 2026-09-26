import pytest
from sqlalchemy.exc import IntegrityError

from talent_platform import create_app, db
from talent_platform.discovery import DiscoveryAccessDenied, get_discoverable_candidates
from talent_platform.models import (
    EvidenceItem,
    EvidenceSkill,
    Job,
    JobSkillRequirement,
    Organization,
    OrganizationMembership,
    Skill,
    StudentProfile,
    User,
)


@pytest.fixture

def app():
    application = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"}
    )
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


def test_core_models_create_relationships(app):
    with app.app_context():
        user = User(identity_subject="subject-1", email="student@example.test")
        profile = StudentProfile(user=user, display_name="Student")
        organization = Organization(
            name="Example Co", slug="example-co", kind="company"
        )
        membership = OrganizationMembership(
            user=user, organization=organization, role="recruiter", status="active"
        )
        skill = Skill(name="Python")
        evidence = EvidenceItem(
            student_profile=profile,
            evidence_type="project",
            source="manual",
            title="Portfolio API",
        )
        evidence_link = EvidenceSkill(
            evidence_item=evidence,
            skill=skill,
            rationale="The project uses Python.",
            proficiency_estimate=75,
            confidence=0.7,
        )
        job = Job(organization=organization, title="Backend intern")
        requirement = JobSkillRequirement(job=job, skill=skill)

        db.session.add_all(
            [user, profile, organization, membership, skill, evidence, evidence_link, job, requirement]
        )
        db.session.commit()

        assert profile.discoverable is False
        assert evidence.visibility == "private"
        assert evidence.skill_links[0].skill.name == "Python"
        assert job.skill_requirements[0].skill.name == "Python"
        assert membership.organization.kind == "company"


def test_user_cannot_have_duplicate_membership_for_organization(app):
    with app.app_context():
        user = User(identity_subject="subject-2", email="recruiter@example.test")
        organization = Organization(
            name="Example Co", slug="example-co", kind="company"
        )
        db.session.add_all([user, organization])
        db.session.flush()
        db.session.add(
            OrganizationMembership(
                user_id=user.id, organization_id=organization.id, role="recruiter"
            )
        )
        db.session.commit()

        db.session.add(
            OrganizationMembership(
                user_id=user.id, organization_id=organization.id, role="owner"
            )
        )
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_discovery_requires_verified_recruiter_and_filters_private_data(app):
    with app.app_context():
        recruiter = User(identity_subject="subject-3", email="recruiter2@example.test")
        organization = Organization(
            name="Verified Co", slug="verified-co", kind="company"
        )
        membership = OrganizationMembership(
            user=recruiter,
            organization=organization,
            role="recruiter",
            status="active",
        )
        visible_profile = StudentProfile(
            user=User(identity_subject="subject-4", email="student2@example.test"),
            display_name="Candidate",
            headline="Backend developer",
            discoverable=True,
        )
        hidden_profile = StudentProfile(
            user=User(identity_subject="subject-5", email="student3@example.test"),
            display_name="Private candidate",
            discoverable=False,
        )
        visible_evidence = EvidenceItem(
            student_profile=visible_profile,
            evidence_type="project",
            source="manual",
            title="Public portfolio",
            summary="Not returned by discovery.",
            visibility="recruiters",
        )
        private_evidence = EvidenceItem(
            student_profile=visible_profile,
            evidence_type="certification",
            source="manual",
            title="Private certificate",
            visibility="private",
        )
        hidden_evidence = EvidenceItem(
            student_profile=hidden_profile,
            evidence_type="project",
            source="manual",
            title="Hidden project",
            visibility="recruiters",
        )
        db.session.add_all(
            [
                recruiter,
                organization,
                membership,
                visible_profile,
                hidden_profile,
                visible_evidence,
                private_evidence,
                hidden_evidence,
            ]
        )
        db.session.commit()

        with pytest.raises(DiscoveryAccessDenied):
            get_discoverable_candidates(recruiter.id, organization.id)

        organization.verification_state = "verified"
        db.session.commit()
        candidates = get_discoverable_candidates(recruiter.id, organization.id)

        assert len(candidates) == 1
        assert candidates[0]["display_name"] == "Candidate"
        assert candidates[0]["evidence"] == [
            {
                "id": visible_evidence.id,
                "evidence_type": "project",
                "title": "Public portfolio",
                "source": "manual",
                "verification_state": "unverified",
                "observed_at": None,
            }
        ]
