from flask import Blueprint, request, jsonify
from tracking_service import TrackingEngine
from models import Vehicle, ParkingArea

driver_bp = Blueprint("driver_bp", __name__, url_prefix="/api/driver")

@driver_bp.route("/vehicle/<string:identifier>", methods=["GET"])
def lookup_vehicle(identifier):
    """Lookup vehicle by Vehicle ID or RFID tag."""
    vehicle = Vehicle.query.filter(
        (Vehicle.vehicle_id == identifier) | (Vehicle.rfid_tag == identifier)
    ).first_or_404(description=f"Vehicle '{identifier}' not found.")
    return jsonify(vehicle.to_dict()), 200

@driver_bp.route("/confirm-location", methods=["POST"])
def confirm_location():
    """Triggered when driver parks/relocates vehicle in 1 of the 10 areas."""
    data = request.get_json() or {}
    required = ["vehicle_id", "driver_id", "parking_area_id", "movement_type"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required parameter: {field}"}), 400

    try:
        updated_vehicle = TrackingEngine.update_parking_location(
            vehicle_id=data["vehicle_id"],
            driver_id=data["driver_id"],
            target_area_id=data["parking_area_id"],
            movement_type=data["movement_type"],
            gps=data.get("coordinates")
        )
        return jsonify({"message": "Location recorded successfully", "vehicle": updated_vehicle}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 409