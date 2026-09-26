from flask import render_template

from talent_platform import create_app


def test_login_page_renders_all_account_domains():
    app = create_app({"TESTING": True})

    with app.test_request_context("/login"):
        html = render_template("login.html")

    assert 'data-domain="student"' in html
    assert 'data-domain="recruiter"' in html
    assert 'data-domain="institution"' in html
    assert "Do not enter real credentials" in html
    assert "/dashboard?role=student" in html


def test_login_assets_are_served():
    client = create_app({"TESTING": True}).test_client()

    assert client.get("/static/login.css").status_code == 200
    assert client.get("/static/login.js").status_code == 200


def test_login_and_role_dashboard_routes_are_available():
    client = create_app({"TESTING": True}).test_client()

    login_response = client.get("/login")
    dashboard_response = client.get("/dashboard?role=institution")

    assert login_response.status_code == 200
    assert b"Choose your workspace" in login_response.data
    assert dashboard_response.status_code == 200
    assert b"Northbridge Institute" in dashboard_response.data
