from pathlib import Path
from flask import Flask

from app.db import init_app as init_db_app


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="change-this-before-deployment",
        DATABASE=str(Path(app.instance_path) / "korabiz.sqlite"),
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    init_db_app(app)

    @app.get("/")
    def home():
        return (
            "<h1>KoraBiz</h1>"
            "<p>The project is running. Database setup is ready for the next stage.</p>"
        )

    return app
