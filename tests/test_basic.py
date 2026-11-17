from app import create_app

def test_app_starts():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test",
        "DATABASE": ":memory:",
    })
    with app.app_context():
        from app.db import init_db
        init_db()
    client = app.test_client()
    response = client.get("/login")
    assert response.status_code == 200
