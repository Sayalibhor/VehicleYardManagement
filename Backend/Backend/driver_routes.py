from flask import Blueprint, request, jsonify

from tracking_service import TrackingEngine

from models import (
    Vehicle,
    ParkingArea,
    Driver,
    VehicleLocationHistory
)


# ============================================================
# BLUEPRINT
# ============================================================

driver_bp = Blueprint(
    "driver_bp",
    __name__,
    url_prefix="/api/driver"
)


# ============================================================
# GET ALL VEHICLES
# Used by:
# - RFID page
# - Driver application
# - Vehicle dropdowns
# ============================================================

@driver_bp.route("/vehicles", methods=["GET"])
def get_all_vehicles():

    try:

        vehicles = (
            Vehicle.query
            .order_by(Vehicle.vehicle_id.asc())
            .all()
        )

        result = []

        for vehicle in vehicles:

            result.append({

                "vehicle_id":
                    vehicle.vehicle_id,

                "rfid_tag":
                    vehicle.rfid_tag,

                "vin":
                    vehicle.vin,

                "vehicle_class":
                    vehicle.vehicle_class,

                "current_status":
                    vehicle.current_status,

                "current_area_id":
                    vehicle.current_area_id

            })

        return jsonify(result), 200

    except Exception as e:

        return jsonify({

            "status": "ERROR",

            "message":
                "Failed to load vehicles",

            "error":
                str(e)

        }), 500


# ============================================================
# GET SINGLE VEHICLE
# Supports:
# - Vehicle ID
# - RFID Tag
# ============================================================

@driver_bp.route(
    "/vehicle/<string:identifier>",
    methods=["GET"]
)
def lookup_vehicle(identifier):

    try:

        vehicle = Vehicle.query.filter(
            (Vehicle.vehicle_id == identifier) |
            (Vehicle.rfid_tag == identifier)
        ).first()

        if not vehicle:

            return jsonify({

                "status": "ERROR",

                "error":
                    f"Vehicle '{identifier}' not found."

            }), 404

        return jsonify(
            vehicle.to_dict()
        ), 200

    except Exception as e:

        return jsonify({

            "status": "ERROR",

            "message":
                "Failed to lookup vehicle",

            "error":
                str(e)

        }), 500


# ============================================================
# GET ALL PARKING AREAS
# ============================================================

@driver_bp.route(
    "/parking-areas",
    methods=["GET"]
)
def get_all_parking_areas():

    try:

        areas = (
            ParkingArea.query
            .order_by(ParkingArea.area_id.asc())
            .all()
        )

        return jsonify([
            area.to_dict()
            for area in areas
        ]), 200

    except Exception as e:

        return jsonify({

            "status": "ERROR",

            "message":
                "Failed to load parking areas",

            "error":
                str(e)

        }), 500


# ============================================================
# GET ALL DRIVERS
# ============================================================

@driver_bp.route(
    "/drivers",
    methods=["GET"]
)
def get_all_drivers():

    try:

        drivers = (
            Driver.query
            .order_by(Driver.driver_id.asc())
            .all()
        )

        return jsonify([
            driver.to_dict()
            for driver in drivers
        ]), 200

    except Exception as e:

        return jsonify({

            "status": "ERROR",

            "message":
                "Failed to load drivers",

            "error":
                str(e)

        }), 500


# ============================================================
# GET SINGLE DRIVER
# ============================================================

@driver_bp.route(
    "/driver/<string:driver_id>",
    methods=["GET"]
)
def get_single_driver(driver_id):

    try:

        driver = Driver.query.get(driver_id)

        if not driver:

            return jsonify({

                "status": "ERROR",

                "error":
                    f"Driver '{driver_id}' not found."

            }), 404

        return jsonify(
            driver.to_dict()
        ), 200

    except Exception as e:

        return jsonify({

            "status": "ERROR",

            "message":
                "Failed to load driver",

            "error":
                str(e)

        }), 500


# ============================================================
# GET ALL VEHICLE MOVEMENT HISTORY
# ============================================================

@driver_bp.route(
    "/movements",
    methods=["GET"]
)
def get_movements():

    try:

        limit = request.args.get(
            "limit",
            default=100,
            type=int
        )

        if limit <= 0:
            limit = 100

        if limit > 500:
            limit = 500

        movements = (
            VehicleLocationHistory.query
            .order_by(
                VehicleLocationHistory.recorded_at.desc()
            )
            .limit(limit)
            .all()
        )

        return jsonify([
            movement.to_dict()
            for movement in movements
        ]), 200

    except Exception as e:

        return jsonify({

            "status": "ERROR",

            "message":
                "Failed to load movements",

            "error":
                str(e)

        }), 500


# ============================================================
# GET MOVEMENT HISTORY FOR SPECIFIC VEHICLE
# ============================================================

@driver_bp.route(
    "/movements/<string:vehicle_id>",
    methods=["GET"]
)
def get_vehicle_movements(vehicle_id):

    try:

        vehicle = Vehicle.query.get(vehicle_id)

        if not vehicle:

            return jsonify({

                "status": "ERROR",

                "error":
                    f"Vehicle '{vehicle_id}' not found."

            }), 404

        movements = (
            VehicleLocationHistory.query
            .filter_by(
                vehicle_id=vehicle_id
            )
            .order_by(
                VehicleLocationHistory.recorded_at.desc()
            )
            .all()
        )

        return jsonify([
            movement.to_dict()
            for movement in movements
        ]), 200

    except Exception as e:

        return jsonify({

            "status": "ERROR",

            "message":
                "Failed to load vehicle movements",

            "error":
                str(e)

        }), 500


# ============================================================
# CONFIRM VEHICLE LOCATION
# Driver handheld / mobile application
# ============================================================

@driver_bp.route(
    "/confirm-location",
    methods=["POST"]
)
def confirm_location():

    data = request.get_json(silent=True) or {}

    required = [
        "vehicle_id",
        "driver_id",
        "parking_area_id",
        "movement_type"
    ]

    for field in required:

        if not data.get(field):

            return jsonify({

                "status": "ERROR",

                "error":
                    f"Missing required parameter: {field}"

            }), 400

    try:

        updated_vehicle = (
            TrackingEngine.update_parking_location(

                vehicle_id=
                    data["vehicle_id"],

                driver_id=
                    data["driver_id"],

                target_area_id=
                    data["parking_area_id"],

                movement_type=
                    data["movement_type"],

                gps=
                    data.get("coordinates")

            )
        )

        return jsonify({

            "status": "SUCCESS",

            "message":
                "Location recorded successfully",

            "vehicle":
                updated_vehicle

        }), 200

    except ValueError as ve:

        return jsonify({

            "status": "ERROR",

            "error":
                str(ve)

        }), 409

    except Exception as e:

        return jsonify({

            "status": "ERROR",

            "message":
                "Failed to confirm vehicle location",

            "error":
                str(e)

        }), 500