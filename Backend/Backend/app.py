from flask import Flask
from config import Config
from models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SQLite database
    db.init_app(app)

    # Register API blueprints
    from rfid_routes import rfid_bp
    from driver_routes import driver_bp
    from sap_routes import sap_bp

    app.register_blueprint(rfid_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(sap_bp)

    return app