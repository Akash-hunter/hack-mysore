from flask import render_template

from talent_platform import create_app
from talent_platform.demo_data import DEMO_DATA


def test_discovery_template_renders_sample_data():
    app = create_app({"TESTING": True})

    with app.test_request_context("/"):
        html = render_template("discovery.html", demo_data=DEMO_DATA)

    assert "Recruiter dashboard" in html
    assert "SAMPLE DATA" in html
    assert "demo-data" in html
    assert 'data-dashboard-tab="student"' in html
    assert 'data-dashboard-tab="recruiter"' in html
    assert 'data-dashboard-tab="institution"' in html
    assert "Northbridge Institute" in html
    assert "Placement pipeline" in html


def test_dashboard_assets_are_served():
    client = create_app({"TESTING": True}).test_client()

    css_response = client.get("/static/styles.css")
    js_response = client.get("/static/app.js")

    assert css_response.status_code == 200
    assert "--forest" in css_response.get_data(as_text=True)
    assert js_response.status_code == 200
    assert "coverageFor" in js_response.get_data(as_text=True)
