from sqlalchemy.orm import selectinload

from . import db
from .models import Organization, OrganizationMembership, StudentProfile


class DiscoveryAccessDenied(PermissionError):
    pass


def get_discoverable_candidates(viewer_user_id, organization_id):
    """Return opt-in profiles for an authorized recruiter in a verified company.

    The caller must resolve ``viewer_user_id`` from authenticated server-side identity,
    never from a request field.
    """
    membership_id = db.session.scalar(
        db.select(OrganizationMembership.id)
        .join(Organization)
        .where(
            OrganizationMembership.user_id == viewer_user_id,
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.status == "active",
            OrganizationMembership.role.in_(("owner", "recruiter")),
            Organization.kind == "company",
            Organization.verification_state == "verified",
        )
        .limit(1)
    )
    if membership_id is None:
        raise DiscoveryAccessDenied("Active verified-company membership is required.")

    profiles = db.session.scalars(
        db.select(StudentProfile)
        .options(selectinload(StudentProfile.evidence_items))
        .where(StudentProfile.discoverable.is_(True))
        .order_by(StudentProfile.id)
    ).all()

    return [
        {
            "profile_id": profile.id,
            "display_name": profile.display_name,
            "headline": profile.headline,
            "evidence": [
                {
                    "id": item.id,
                    "evidence_type": item.evidence_type,
                    "title": item.title,
                    "source": item.source,
                    "verification_state": item.verification_state,
                    "observed_at": item.observed_at,
                }
                for item in sorted(profile.evidence_items, key=lambda evidence: evidence.id)
                if item.visibility == "recruiters"
            ],
        }
        for profile in profiles
    ]
