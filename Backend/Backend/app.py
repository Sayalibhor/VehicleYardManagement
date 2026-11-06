from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)
    db.init_app(app)

    # Register Vehicle Yard Management Blueprints
    from rfid_routes import rfid_bp
    from driver_routes import driver_bp
    from sap_routes import sap_bp
    from entry_routes import entry_bp
    from camera_patrol_routes import camera_patrol_bp

    app.register_blueprint(rfid_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(sap_bp)
    app.register_blueprint(entry_bp)
    app.register_blueprint(camera_patrol_bp)

    with app.app_context():
        db.create_all()

    @app.route("/", methods=["GET"])
    def home():
        return jsonify({
            "status": "success",
            "message": "Vehicle Yard Management Backend is running",
            "service": "Vehicle Yard Management System"
        })

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
