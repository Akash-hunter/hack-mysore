from talent_platform import create_app


def test_login_and_signup_routes_are_separate():
    client = create_app({"TESTING": True}).test_client()

    login_response = client.get("/login")
    signup_response = client.get("/signup")

    assert b"Welcome back" in login_response.data
    assert b"Create your account" in signup_response.data
    assert b"Do not enter real credentials" in login_response.data


def test_login_assets_are_served():
    client = create_app({"TESTING": True}).test_client()

    assert client.get("/static/login.css").status_code == 200
    assert client.get("/static/account-flow.js").status_code == 200
    assert client.get("/static/role-select.js").status_code == 200
    assert client.get("/static/landing.css").status_code == 200


def test_role_selection_opens_each_matching_portal():
    role_response = create_app({"TESTING": True}).test_client().get("/select-role?flow=signup")

    assert role_response.status_code == 200
    assert b"Choose your role" in role_response.data
    for role in ("student", "recruiter", "institution"):
        client = create_app({"TESTING": True}).test_client()
        selection = client.post("/select-role", data={"role": role})
        response = client.get(selection.location)

        assert selection.status_code == 302
        assert response.status_code == 200
        assert f'data-initial-role="{role}"'.encode() in response.data
        assert f'id="{role}-dashboard"'.encode() in response.data
        other_roles = {"student", "recruiter", "institution"} - {role}
        for other_role in other_roles:
            assert f'id="{other_role}-dashboard"'.encode() not in response.data


def test_preview_session_cannot_open_another_role_until_signout():
    client = create_app({"TESTING": True}).test_client()

    assert client.get("/portal/student").status_code == 403
    client.post("/select-role", data={"role": "student"})

    recruiter_response = client.get("/portal/recruiter")
    institution_response = client.get("/portal/institution")
    assert recruiter_response.status_code == 403
    assert institution_response.status_code == 403
    assert b"This workspace is unavailable" in recruiter_response.data
    assert b"Sign out before choosing a different workspace" in institution_response.data
    assert client.get("/select-role").headers["Location"].endswith("/portal/student")
    assert client.post("/select-role", data={"role": "recruiter"}).status_code == 403

    client.post("/logout")
    assert client.get("/select-role").status_code == 200


def test_legacy_dashboard_preview_redirects_to_role_portal():
    client = create_app({"TESTING": True}).test_client()

    response = client.get("/dashboard?role=institution")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/portal/institution")
