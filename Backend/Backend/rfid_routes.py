from flask import Blueprint, request, jsonify
from tracking_service import TrackingEngine
from rfid_simulator import RFIDSimulator

rfid_bp = Blueprint("rfid_bp", __name__, url_prefix="/api/rfid")

@rfid_bp.route("/scan", methods=["POST"])
def ingest_rfid_scan():
    """Real hardware gate reader webhook."""
    data = request.get_json() or {}
    for param in ["gate_id", "direction", "rfid_tag"]:
        if param not in data:
            return jsonify({"error": f"Missing parameter: {param}"}), 400

    res = TrackingEngine.process_gate_rfid(
        gate_id=data["gate_id"],
        direction=data["direction"],
        rfid_tag=data["rfid_tag"],
        raw_meta=data.get("metadata")
    )
    return jsonify(res), 200

@rfid_bp.route("/simulate/entry", methods=["POST"])
def trigger_entry_simulation():
    res = RFIDSimulator.simulate_random_gate_entry()
    return jsonify(res), 200

@rfid_bp.route("/simulate/exit", methods=["POST"])
def trigger_exit_simulation():
    res = RFIDSimulator.simulate_random_gate_exit()
    return jsonify(res), 200