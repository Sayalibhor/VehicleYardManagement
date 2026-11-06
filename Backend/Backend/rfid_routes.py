
from flask import Blueprint, request, jsonify
from tracking_service import TrackingEngine
from rfid_simulator import RFIDSimulator
from models import RFIDGateTransaction

rfid_bp = Blueprint(
    "rfid_bp",
    __name__,
    url_prefix="/api/rfid"
)


# =========================================================
# RFID SCAN
# =========================================================

@rfid_bp.route("/scan", methods=["POST"])
def ingest_rfid_scan():
    """Real hardware gate reader webhook."""

    data = request.get_json() or {}

    for param in ["gate_id", "direction", "rfid_tag"]:
        if param not in data:
            return jsonify({
                "error": f"Missing parameter: {param}"
            }), 400

    res = TrackingEngine.process_gate_rfid(
        gate_id=data["gate_id"],
        direction=data["direction"],
        rfid_tag=data["rfid_tag"],
        raw_meta=data.get("metadata")
    )

    return jsonify(res), 200


# =========================================================
# GET RFID TRANSACTIONS
# =========================================================

@rfid_bp.route("/transactions", methods=["GET"])
def get_rfid_transactions():
    """Return recent RFID gate transactions from backend database."""

    limit = request.args.get(
        "limit",
        default=50,
        type=int
    )

    if limit <= 0:
        limit = 50

    if limit > 500:
        limit = 500

    transactions = RFIDGateTransaction.query.order_by(
        RFIDGateTransaction.scanned_at.desc()
    ).limit(limit).all()

    return jsonify([
        transaction.to_dict()
        for transaction in transactions
    ]), 200


# =========================================================
# GET SINGLE RFID TRANSACTION
# =========================================================

@rfid_bp.route("/transactions/<int:transaction_id>", methods=["GET"])
def get_single_rfid_transaction(transaction_id):

    transaction = RFIDGateTransaction.query.get(
        transaction_id
    )

    if not transaction:
        return jsonify({
            "error":
            f"RFID transaction '{transaction_id}' not found."
        }), 404

    return jsonify(
        transaction.to_dict()
    ), 200


# =========================================================
# RFID ENTRY SIMULATION
# =========================================================

@rfid_bp.route("/simulate/entry", methods=["POST"])
def trigger_entry_simulation():

    res = RFIDSimulator.simulate_random_gate_entry()

    return jsonify(res), 200


# =========================================================
# RFID EXIT SIMULATION
# =========================================================

@rfid_bp.route("/simulate/exit", methods=["POST"])
def trigger_exit_simulation():

    res = RFIDSimulator.simulate_random_gate_exit()

    return jsonify(res), 200
