from flask import render_template

from talent_platform import create_app


def test_landing_and_role_selection_templates_render():
    app = create_app({"TESTING": True})

    with app.test_request_context("/"):
        landing = render_template("landing.html")
        role_selection = render_template("select_role.html", flow="signup")
        sign_in = render_template("account.html", mode="login")
        sign_up = render_template("account.html", mode="signup")

    assert "Talent Ecosystem" in landing
    assert 'href="/signup"' in landing
    assert "Choose your role" in role_selection
    assert "ACCOUNT ACCESS / 02" in role_selection
    assert "Welcome back" in sign_in
    assert "Create your account" in sign_up
    assert 'action="/select-role" method="get"' in sign_in
    assert 'name="password"' not in sign_in
