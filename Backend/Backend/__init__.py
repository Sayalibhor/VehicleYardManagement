from flask import Flask
from config import Config
from app.models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    from app.routes.rfid_routes import rfid_bp
    from app.routes.driver_routes import driver_bp
    from app.routes.yard_routes import yard_bp
    from app.routes.sap_routes import sap_bp

    app.register_blueprint(rfid_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(yard_bp)
    app.register_blueprint(sap_bp)

    return app