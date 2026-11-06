from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid

from models import db, CameraPatrolRecord


# =========================================================
# CAMERA PATROL BLUEPRINT
# =========================================================

camera_patrol_bp = Blueprint(
    "camera_patrol_bp",
    __name__,
    url_prefix="/api/camera/patrol"
)


# =========================================================
# START / SAVE PATROL ROUND
# =========================================================

@camera_patrol_bp.route("/start", methods=["POST"])
def start_patrol():

    data = request.get_json(silent=True) or {}

    camera_id = data.get(
        "camera_id",
        "PARKING_CAMERA_01"
    )

    detections = data.get(
        "detections",
        []
    )

    # Create unique patrol round ID
    round_id = (
        "ROUND-"
        + datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        + "-"
        + uuid.uuid4().hex[:6]
    )

    saved_records = []

    # -----------------------------------------------------
    # Save every vehicle detected by camera
    # -----------------------------------------------------

    for detection in detections:

        vehicle_number = detection.get(
            "vehicle_number"
        )

        # Vehicle number is required
        if not vehicle_number:
            continue

        record = CameraPatrolRecord(

            round_id=round_id,

            camera_id=camera_id,

            vehicle_id=detection.get(
                "vehicle_id"
            ),

            vehicle_number=vehicle_number,

            rfid_tag=detection.get(
                "rfid_tag"
            ),

            parking_area=detection.get(
                "parking_area"
            ),

            slot_number=detection.get(
                "slot_number"
            ),

            detected_at=datetime.utcnow(),

            image_path=detection.get(
                "image_path"
            ),

            confidence=detection.get(
                "confidence"
            ),

            detection_status=detection.get(
                "detection_status",
                "Detected"
            )
        )

        db.session.add(record)

        saved_records.append(record)

    db.session.commit()

    return jsonify({

        "success": True,

        "message":
            "Camera patrol round saved successfully",

        "round_id":
            round_id,

        "camera_id":
            camera_id,

        "vehicles_detected":
            len(saved_records),

        "records": [
            record.to_dict()
            for record in saved_records
        ]

    }), 201


# =========================================================
# LATEST PATROL ROUND
# =========================================================

@camera_patrol_bp.route(
    "/latest",
    methods=["GET"]
)
def latest_patrol():

    latest_record = (
        CameraPatrolRecord.query
        .order_by(
            CameraPatrolRecord.detected_at.desc()
        )
        .first()
    )

    if not latest_record:

        return jsonify({

            "success": True,

            "message":
                "No camera patrol records found",

            "round_id": None,

            "records": []

        })

    records = (
        CameraPatrolRecord.query
        .filter_by(
            round_id=latest_record.round_id
        )
        .order_by(
            CameraPatrolRecord.detected_at.asc()
        )
        .all()
    )

    return jsonify({

        "success": True,

        "round_id":
            latest_record.round_id,

        "camera_id":
            latest_record.camera_id,

        "vehicles_detected":
            len(records),

        "records": [
            record.to_dict()
            for record in records
        ]

    })


# =========================================================
# ALL PATROL HISTORY
# =========================================================

@camera_patrol_bp.route(
    "/history",
    methods=["GET"]
)
def patrol_history():

    records = (
        CameraPatrolRecord.query
        .order_by(
            CameraPatrolRecord.detected_at.desc()
        )
        .all()
    )

    return jsonify({

        "success": True,

        "count":
            len(records),

        "records": [
            record.to_dict()
            for record in records
        ]

    })


# =========================================================
# SEARCH VEHICLE CAMERA HISTORY
# =========================================================

@camera_patrol_bp.route(
    "/vehicle/<vehicle_number>",
    methods=["GET"]
)
def vehicle_camera_history(vehicle_number):

    records = (
        CameraPatrolRecord.query
        .filter(
            db.func.lower(
                CameraPatrolRecord.vehicle_number
            )
            ==
            vehicle_number.lower()
        )
        .order_by(
            CameraPatrolRecord.detected_at.desc()
        )
        .all()
    )

    return jsonify({

        "success": True,

        "vehicle_number":
            vehicle_number,

        "count":
            len(records),

        "records": [
            record.to_dict()
            for record in records
        ]

    })