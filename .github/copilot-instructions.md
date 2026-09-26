# Project Instructions

- Build this as a modular monolith with Flask, SQLAlchemy, and PostgreSQL until the product requires otherwise.
- Keep organization-owned records scoped by `organization_id`; enforce membership and role checks in server-side services, never only in the frontend.
- Student discoverability and evidence visibility must be opt-in and checked on every candidate-data request.
- Store evidence provenance, verification state, and timestamps. Distinguish evidence confidence from skill proficiency; explain matching factors and missing evidence.
- Do not use protected characteristics for matching. Do not add AI-generated candidate scores, real authentication, or external integrations without an explicit design and review.
- Keep changes small, add focused pytest coverage, and document configuration without committing secrets. Local Compose credentials are development-only.
- Follow `architecture/system-design.md` and `architecture/data-model.md`; update them when behavior or data boundaries change.
