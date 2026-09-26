from sqlalchemy import CheckConstraint, UniqueConstraint

from ..extensions import db
from .monitoring import MonitoringSession, GazeSample, KeystrokeEvent, Assessment


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    identity_subject = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(320), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="active", server_default="active")

    memberships = db.relationship(
        "OrganizationMembership", back_populates="user", cascade="all, delete-orphan"
    )
    student_profile = db.relationship(
        "StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Organization(TimestampMixin, db.Model):
    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint("kind IN ('company', 'institution')", name="ck_organizations_kind"),
        CheckConstraint(
            "verification_state IN ('unverified', 'pending', 'verified', 'rejected')",
            name="ck_organizations_verification_state",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(180), nullable=False, unique=True)
    kind = db.Column(db.String(20), nullable=False)
    verification_state = db.Column(
        db.String(20), nullable=False, default="unverified", server_default="unverified"
    )

    memberships = db.relationship(
        "OrganizationMembership", back_populates="organization", cascade="all, delete-orphan"
    )
    affiliations = db.relationship("InstitutionAffiliation", back_populates="institution")
    jobs = db.relationship("Job", back_populates="organization")


class OrganizationMembership(TimestampMixin, db.Model):
    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_membership_user_organization"),
        CheckConstraint(
            "role IN ('owner', 'recruiter', 'institution_admin', 'faculty')",
            name="ck_memberships_role",
        ),
        CheckConstraint(
            "status IN ('pending', 'active', 'revoked')", name="ck_memberships_status"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", server_default="pending")

    user = db.relationship("User", back_populates="memberships")
    organization = db.relationship("Organization", back_populates="memberships")


class StudentProfile(TimestampMixin, db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    display_name = db.Column(db.String(160))
    headline = db.Column(db.String(240))
    discoverable = db.Column(db.Boolean, nullable=False, default=False, server_default="false")

    user = db.relationship("User", back_populates="student_profile")
    affiliations = db.relationship(
        "InstitutionAffiliation", back_populates="student_profile", cascade="all, delete-orphan"
    )
    evidence_items = db.relationship(
        "EvidenceItem", back_populates="student_profile", cascade="all, delete-orphan"
    )


class InstitutionAffiliation(TimestampMixin, db.Model):
    __tablename__ = "institution_affiliations"
    __table_args__ = (
        UniqueConstraint(
            "student_profile_id", "institution_id", name="uq_affiliation_student_institution"
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'revoked')", name="ck_affiliations_status"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id"), nullable=False
    )
    institution_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", server_default="pending")
    authorization_method = db.Column(db.String(80))

    student_profile = db.relationship("StudentProfile", back_populates="affiliations")
    institution = db.relationship("Organization", back_populates="affiliations")


class Skill(TimestampMixin, db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    category = db.Column(db.String(80))

    evidence_links = db.relationship("EvidenceSkill", back_populates="skill")
    job_requirements = db.relationship("JobSkillRequirement", back_populates="skill")


class EvidenceItem(TimestampMixin, db.Model):
    __tablename__ = "evidence_items"
    __table_args__ = (
        CheckConstraint(
            "evidence_type IN ('project', 'assessment', 'certification', 'hackathon', 'github', 'other')",
            name="ck_evidence_type",
        ),
        CheckConstraint(
            "verification_state IN ('unverified', 'pending', 'verified', 'rejected')",
            name="ck_evidence_verification_state",
        ),
        CheckConstraint(
            "visibility IN ('private', 'recruiters', 'applications_only')",
            name="ck_evidence_visibility",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id"), nullable=False
    )
    evidence_type = db.Column(db.String(24), nullable=False)
    source = db.Column(db.String(80), nullable=False)
    source_reference = db.Column(db.String(500))
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text)
    verification_state = db.Column(
        db.String(20), nullable=False, default="unverified", server_default="unverified"
    )
    visibility = db.Column(db.String(24), nullable=False, default="private", server_default="private")
    observed_at = db.Column(db.DateTime(timezone=True))

    student_profile = db.relationship("StudentProfile", back_populates="evidence_items")
    skill_links = db.relationship(
        "EvidenceSkill", back_populates="evidence_item", cascade="all, delete-orphan"
    )


class EvidenceSkill(TimestampMixin, db.Model):
    __tablename__ = "evidence_skills"
    __table_args__ = (
        CheckConstraint(
            "proficiency_estimate IS NULL OR (proficiency_estimate >= 0 AND proficiency_estimate <= 100)",
            name="ck_evidence_skill_proficiency",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_evidence_skill_confidence",
        ),
    )

    evidence_item_id = db.Column(
        db.Integer, db.ForeignKey("evidence_items.id"), primary_key=True
    )
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), primary_key=True)
    rationale = db.Column(db.String(500), nullable=False)
    proficiency_estimate = db.Column(db.Float)
    confidence = db.Column(db.Float)

    evidence_item = db.relationship("EvidenceItem", back_populates="skill_links")
    skill = db.relationship("Skill", back_populates="evidence_links")


class Job(TimestampMixin, db.Model):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'open', 'closed')", name="ck_jobs_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(160))
    work_mode = db.Column(db.String(20))
    status = db.Column(db.String(20), nullable=False, default="draft", server_default="draft")

    organization = db.relationship("Organization", back_populates="jobs")
    skill_requirements = db.relationship(
        "JobSkillRequirement", back_populates="job", cascade="all, delete-orphan"
    )


class JobSkillRequirement(TimestampMixin, db.Model):
    __tablename__ = "job_skill_requirements"
    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_skill_requirement"),
        CheckConstraint("weight > 0", name="ck_job_skill_weight_positive"),
        CheckConstraint(
            "target_level IS NULL OR (target_level >= 1 AND target_level <= 5)",
            name="ck_job_skill_target_level",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    required = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    target_level = db.Column(db.Integer)
    weight = db.Column(db.Float, nullable=False, default=1.0, server_default="1.0")

    job = db.relationship("Job", back_populates="skill_requirements")
    skill = db.relationship("Skill", back_populates="job_requirements")


__all__ = [
    "TimestampMixin",
    "User",
    "Organization",
    "OrganizationMembership",
    "StudentProfile",
    "InstitutionAffiliation",
    "Skill",
    "EvidenceItem",
    "EvidenceSkill",
    "Job",
    "JobSkillRequirement",
    "MonitoringSession",
    "GazeSample",
    "KeystrokeEvent",
    "Assessment",
]
