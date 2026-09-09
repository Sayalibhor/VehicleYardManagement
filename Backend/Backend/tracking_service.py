import json
from datetime import datetime
from models import db, Vehicle, ParkingArea, VehicleLocationHistory, RFIDGateTransaction, SAPOutboundEvent
class TrackingEngine:

    @staticmethod
    def process_gate_rfid(gate_id: str, direction: str, rfid_tag: str, raw_meta: dict = None):
        """Processes fixed gate RFID reader scans."""
        vehicle = Vehicle.query.filter_by(rfid_tag=rfid_tag).first()
        vehicle_id = vehicle.vehicle_id if vehicle else None

        # 1. Log Raw Gate Transaction
        tx = RFIDGateTransaction(
            gate_id=gate_id,
            direction=direction,
            rfid_tag=rfid_tag,
            vehicle_id=vehicle_id,
            raw_payload=json.dumps(raw_meta or {})
        )
        db.session.add(tx)

        if not vehicle:
            db.session.commit()
            return {"status": "UNREGISTERED_TAG", "rfid_tag": rfid_tag, "message": "Unknown RFID tag"}

        # 2. State Engine Validation
        event_name = None
        if direction.upper() == "IN":
            vehicle.current_status = "IN_YARD"
            vehicle.current_area_id = None  # Not yet parked in a slot
            event_name = "VEHICLE_ENTERED_YARD"
        elif direction.upper() == "OUT":
            # If vehicle was occupying an area, free it up
            if vehicle.current_area_id:
                area = ParkingArea.query.get(vehicle.current_area_id)
                if area and area.current_occupancy > 0:
                    area.current_occupancy -= 1
            vehicle.current_status = "EXITED"
            vehicle.current_area_id = None
            event_name = "VEHICLE_EXITED_YARD"

        # 3. Create Validated SAP Business Event
        if event_name:
            TrackingEngine._enqueue_sap_event(
                event_type=event_name,
                vehicle=vehicle,
                additional_data={"gate_id": gate_id, "direction": direction}
            )

        db.session.commit()
        return {"status": "SUCCESS", "vehicle": vehicle.to_dict(), "event": event_name}

    @staticmethod
    def update_parking_location(vehicle_id: str, driver_id: str, target_area_id: str,
                                movement_type: str, gps: dict = None):
        """Driver Mobile App Location Update Workflow."""
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle '{vehicle_id}' not found.")

        target_area = ParkingArea.query.get(target_area_id)
        if not target_area:
            raise ValueError(f"Parking Area '{target_area_id}' not found.")

        if target_area.current_occupancy >= target_area.capacity and vehicle.current_area_id != target_area_id:
            raise ValueError(f"Parking Area '{target_area.name}' is already at full capacity ({target_area.capacity}).")

        old_area_id = vehicle.current_area_id

        # 1. Update Area Capacities
        if old_area_id != target_area_id:
            if old_area_id:
                old_area = ParkingArea.query.get(old_area_id)
                if old_area and old_area.current_occupancy > 0:
                    old_area.current_occupancy -= 1
            target_area.current_occupancy += 1

        # 2. Update Vehicle State
        vehicle.current_area_id = target_area_id
        vehicle.current_status = "READY_FOR_DISPATCH" if movement_type == "READY_FOR_DISPATCH" else "PARKED"

        # 3. Audit Movement
        lat = gps.get("lat") if gps else None
        lng = gps.get("lng") if gps else None
        history = VehicleLocationHistory(
            vehicle_id=vehicle.vehicle_id,
            from_area_id=old_area_id,
            to_area_id=target_area_id,
            movement_type=movement_type,
            updated_by=driver_id,
            gps_lat=lat,
            gps_lng=lng
        )
        db.session.add(history)

        # 4. Enqueue Business Event for SAP CPI
        event_type = "VEHICLE_RELOCATED" if old_area_id else "VEHICLE_ASSIGNED_TO_PARKING"
        TrackingEngine._enqueue_sap_event(
            event_type=event_type,
            vehicle=vehicle,
            additional_data={
                "parking_area": target_area_id,
                "driver_id": driver_id,
                "movement_type": movement_type,
                "gps": gps
            }
        )

        db.session.commit()
        return vehicle.to_dict()

    @staticmethod
    def _enqueue_sap_event(event_type: str, vehicle: Vehicle, additional_data: dict):
        payload = {
            "businessEvent": event_type,
            "vehicleId": vehicle.vehicle_id,
            "vin": vehicle.vin,
            "vehicleClass": vehicle.vehicle_class,
            "currentStatus": vehicle.current_status,
            "targetArea": vehicle.current_area_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": additional_data
        }

        outbound = SAPOutboundEvent(
            event_type=event_type,
            vehicle_id=vehicle.vehicle_id,
            payload=json.dumps(payload),
            sync_status="PENDING"
        )
        db.session.add(outbound)