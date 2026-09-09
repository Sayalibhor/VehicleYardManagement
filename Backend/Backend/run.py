from app import create_app
from models import db, ParkingArea, Vehicle, Driver

app = create_app()

def seed_initial_data():
    with app.app_context():
        db.create_all()

        # Seed 10 Parking Areas
        if ParkingArea.query.count() == 0:
            for i in range(1, 11):
                area = ParkingArea(
                    area_id=f"AREA_{i:02d}",
                    name=f"Parking Zone {i}",
                    capacity=25,
                    current_occupancy=0
                )
                db.session.add(area)

        # Seed 8 Vehicle Classes
        vehicle_classes = [
            "Heavy Trailer", "Semi-Trailer", "Box Truck", "Flatbed", 
            "Container Chassis", "Tanker", "Cargo Van", "Yard Tug"
        ]
        if Vehicle.query.count() == 0:
            for idx, v_class in enumerate(vehicle_classes, start=1):
                v = Vehicle(
                    vehicle_id=f"V{1000 + idx}",
                    rfid_tag=f"E2801160600002047805{idx:04d}",
                    vin=f"1M8GDM9A_SAMPLE{idx:02d}",
                    vehicle_class=v_class,
                    current_status="EXPECTED"
                )
                db.session.add(v)

        # Seed Drivers
        if Driver.query.count() == 0:
            drivers = [
                Driver(driver_id="DRV_101", full_name="John Doe", license_number="DL-TX-9901"),
                Driver(driver_id="DRV_102", full_name="Jane Smith", license_number="DL-TX-9902"),
            ]
            db.session.add_all(drivers)

        db.session.commit()
        print("[*] Database initialized and seeded with 10 Areas, 8 Classes, and Drivers.")

if __name__ == "__main__":
    seed_initial_data()
    app.run(host="0.0.0.0", port=5000, debug=True)