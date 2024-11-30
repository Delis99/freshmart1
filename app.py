from flask import Flask
from apps.user_app import user_bp # type: ignore
from apps.employee_app import employee_bp # type: ignore
from apps.delivery_app import delivery_bp # type: ignore

def create_app():
    app = Flask(__name__)

    # Register Blueprints
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app.register_blueprint(delivery_bp, url_prefix='/delivery')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
