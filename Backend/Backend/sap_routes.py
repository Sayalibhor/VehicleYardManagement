from flask import Blueprint, jsonify
from models import SAPOutboundEvent
from sap_service import SAPIntegrationService

sap_bp = Blueprint("sap_bp", __name__, url_prefix="/api/sap")

@sap_bp.route("/events", methods=["GET"])
def get_sap_events():
    events = SAPOutboundEvent.query.order_by(SAPOutboundEvent.created_at.desc()).limit(50).all()
    return jsonify([e.to_dict() for e in events]), 200

@sap_bp.route("/sync-now", methods=["POST"])
def trigger_sap_sync():
    summary = SAPIntegrationService.process_pending_events()
    return jsonify({"message": "SAP Sync completed", "summary": summary}), 200