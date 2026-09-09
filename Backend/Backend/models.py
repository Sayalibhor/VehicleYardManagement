import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Vehicle(db.Model):
    __tablename__ = "vehicles"

    vehicle_id = db.Column(db.String(32), primary_key=True)
    rfid_tag = db.Column(db.String(64), unique=True, nullable=False, index=True)
    vin = db.Column(db.String(17), unique=True, nullable=False)
    vehicle_class = db.Column(db.String(32), nullable=False)
    current_status = db.Column(db.String(32), default="EXPECTED", nullable=False)
    current_area_id = db.Column(db.String(16), db.ForeignKey("parking_areas.area_id"), nullable=True)
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parking_area = db.relationship("ParkingArea", back_populates="parked_vehicles")

    def to_dict(self):
        return {
            "vehicle_id": self.vehicle_id,
            "rfid_tag": self.rfid_tag,
            "vin": self.vin,
            "vehicle_class": self.vehicle_class,
            "current_status": self.current_status,
            "current_area_id": self.current_area_id,
            "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at else None,
        }


class Driver(db.Model):
    __tablename__ = "drivers"

    driver_id = db.Column(db.String(32), primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "driver_id": self.driver_id,
            "full_name": self.full_name,
            "license_number": self.license_number,
            "is_active": self.is_active,
        }


class ParkingArea(db.Model):
    __tablename__ = "parking_areas"

    area_id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    current_occupancy = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    parked_vehicles = db.relationship("Vehicle", back_populates="parking_area")

    def to_dict(self):
        return {
            "area_id": self.area_id,
            "name": self.name,
            "capacity": self.capacity,
            "current_occupancy": self.current_occupancy,
            "available_slots": self.capacity - self.current_occupancy,
            "is_active": self.is_active,
        }


class VehicleLocationHistory(db.Model):
    __tablename__ = "vehicle_location_history"

    history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vehicle_id = db.Column(db.String(32), db.ForeignKey("vehicles.vehicle_id"), nullable=False)
    from_area_id = db.Column(db.String(16), nullable=True)
    to_area_id = db.Column(db.String(16), nullable=True)
    movement_type = db.Column(db.String(32), nullable=False)
    updated_by = db.Column(db.String(50), nullable=False)
    gps_lat = db.Column(db.Float, nullable=True)
    gps_lng = db.Column(db.Float, nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "history_id": self.history_id,
            "vehicle_id": self.vehicle_id,
            "from_area_id": self.from_area_id,
            "to_area_id": self.to_area_id,
            "movement_type": self.movement_type,
            "updated_by": self.updated_by,
            "gps": {"lat": self.gps_lat, "lng": self.gps_lng} if self.gps_lat else None,
            "recorded_at": self.recorded_at.isoformat(),
        }


class RFIDGateTransaction(db.Model):
    __tablename__ = "rfid_gate_transactions"

    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gate_id = db.Column(db.String(32), nullable=False)
    direction = db.Column(db.String(8), nullable=False)
    rfid_tag = db.Column(db.String(64), nullable=False, index=True)
    vehicle_id = db.Column(db.String(32), nullable=True)
    raw_payload = db.Column(db.Text, nullable=True)
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "gate_id": self.gate_id,
            "direction": self.direction,
            "rfid_tag": self.rfid_tag,
            "vehicle_id": self.vehicle_id,
            "scanned_at": self.scanned_at.isoformat(),
        }


class SAPOutboundEvent(db.Model):
    __tablename__ = "sap_outbound_events"

    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_type = db.Column(db.String(64), nullable=False)
    vehicle_id = db.Column(db.String(32), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    sync_status = db.Column(db.String(16), default="PENDING")
    retry_count = db.Column(db.Integer, default=0)
    sap_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "vehicle_id": self.vehicle_id,
            "payload": json.loads(self.payload),
            "sync_status": self.sync_status,
            "retry_count": self.retry_count,
            "sap_response": self.sap_response,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }