import random
from models import Vehicle
from tracking_service import TrackingEngine

class RFIDSimulator:

    @staticmethod
    def simulate_random_gate_entry(gate_id="GATE_ENTRY_01"):
        """Picks a random expected or exited vehicle and simulates an arrival scan."""
        candidate = Vehicle.query.filter(Vehicle.current_status.in_(["EXPECTED", "EXITED"])).first()
        if not candidate:
            return {"message": "No vehicles eligible for entry simulation."}

        return TrackingEngine.process_gate_rfid(
            gate_id=gate_id,
            direction="IN",
            rfid_tag=candidate.rfid_tag,
            raw_meta={"simulation": True, "rssi": random.randint(-65, -35)}
        )

    @staticmethod
    def simulate_random_gate_exit(gate_id="GATE_EXIT_01"):
        """Picks a parked or staged vehicle and simulates gate departure."""
        candidate = Vehicle.query.filter(Vehicle.current_status.in_(["READY_FOR_DISPATCH", "PARKED"])).first()
        if not candidate:
            return {"message": "No vehicles eligible for exit simulation."}

        return TrackingEngine.process_gate_rfid(
            gate_id=gate_id,
            direction="OUT",
            rfid_tag=candidate.rfid_tag,
            raw_meta={"simulation": True, "rssi": random.randint(-60, -40)}
        )