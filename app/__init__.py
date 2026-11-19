import os
from pathlib import Path
from flask import Flask, redirect, url_for, g
from .db import init_app as init_db_app, init_db
from .auth import bp as auth_bp, load_logged_in_user
from .shop import bp as shop_bp

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("KORABIZ_SECRET_KEY", "local-development-key-change-before-deployment"),
        DATABASE=str(Path(app.instance_path) / "korabiz.sqlite"),
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_db_app(app)
    with app.app_context():
        init_db()
    app.before_request(load_logged_in_user)
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)

    @app.context_processor
    def inject_user():
        return {"current_user": g.get("user")}

    return app
