# Talent Ecosystem

A beginner-friendly starter for an evidence-backed talent discovery platform. The first milestone is a narrow, explainable demo: a student opts into discovery and adds evidence, a recruiter creates a role, and the system explains which candidate evidence relates to each requirement.

## Stack

- Python 3.12+
- Flask application factory with SQLAlchemy and Flask-Migrate
- PostgreSQL for local development through Docker Compose
- pytest for tests

## Setup on Windows

1. Open this folder in VS Code and open a PowerShell terminal.
2. Create and activate a virtual environment:

   ```powershell
   & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If Python is already on PATH, `python -m venv .venv` also works.
3. Install the app and test dependencies:

   ```powershell
   python -m pip install -e ".[dev]"
   ```
4. Create your local environment file and start PostgreSQL:

   ```powershell
   Copy-Item .env.example .env
   docker compose up -d db
   ```

   The Compose credentials are for local development only. Do not reuse them in a deployed environment.
5. Start the Flask development server:

   ```powershell
   flask --app talent_platform:create_app run --debug
   ```

   Or run the VS Code task `Run Talent Ecosystem API (localhost)` from Terminal > Run Task.
6. In another terminal, run the tests:

   ```powershell
   python -m pytest
   ```

Open `http://127.0.0.1:5000/` for the landing page, then choose Sign in or Create account. After the account preview, select a role to open `/portal/student`, `/portal/recruiter`, or `/portal/institution`. These portals use fictional sample data and do not read or write database records. The account form does not submit or store credentials. The health endpoint is at `http://127.0.0.1:5000/health` and does not verify database readiness.

## Project map

- `architecture/system-design.md`: scope, boundaries, access rules, API outline, and matching principles.
- `architecture/data-model.md`: initial entities, relationships, and invariants.
- `migrations/`: Flask-Migrate configuration; no initial revision has been generated yet.
- `backend/talent_platform/`: Flask app factory, models, extensions, and recruiter discovery policy.
- `tests/`: focused automated tests.
- `.env.example`: local configuration template; copy to `.env` and keep `.env` untracked.

## Current limits

The landing, sign-in/sign-up, role-selection, and portal routes demonstrate the requested flow, but are not authentication. The preview session remembers one selected role, rejects requests to another role's portal, and is cleared by Sign out. This is a UI-flow guard only: anyone can start the demo and choose a role, so it is not production access control. Account fields have no submitted names, are cleared before navigation, and are never stored; do not enter real credentials. The three role dashboards currently use fictional sample data. The initial SQLAlchemy models, recruiter discovery policy, and Flask-Migrate scaffold are in place, but no migration revision has been generated or applied. Identity-provider integration, authenticated HTTP routes, database-backed dashboards and matching, and external integrations are intentionally deferred. The discovery policy expects a user ID resolved by trusted server-side authentication; it is not exposed as an unauthenticated endpoint. The architecture documents describe the intended design; review them with the team before feature work.
