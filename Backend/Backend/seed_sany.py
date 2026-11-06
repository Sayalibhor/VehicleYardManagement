from app import create_app
from models import db, Vehicle


# ============================================================
# SANY VEHICLES
#
# Existing Vehicle IDs are kept unchanged.
# Only RFID, VIN and Vehicle Class are updated.
#
# This prevents existing:
# - RFID records
# - Movement history
# - Vehicle entries
# from breaking.
# ============================================================

SANY_VEHICLES = [

    {
        "vehicle_id": "V1001",
        "rfid_tag": "SANY-RFID-001",
        "vin": "SANYDEMO00000001A",
        "vehicle_class": "STC500T5 - Truck Crane"
    },

    {
        "vehicle_id": "V1002",
        "rfid_tag": "SANY-RFID-002",
        "vin": "SANYDEMO00000002A",
        "vehicle_class": "STC800T5 - Truck Crane"
    },

    {
        "vehicle_id": "V1003",
        "rfid_tag": "SANY-RFID-003",
        "vin": "SANYDEMO00000003A",
        "vehicle_class": "SY215C-9LC SPARC+ - Excavator"
    },

    {
        "vehicle_id": "V1004",
        "rfid_tag": "SANY-RFID-004",
        "vin": "SANYDEMO00000004A",
        "vehicle_class": "SY210C-9 SPARC+ - Excavator"
    },

    {
        "vehicle_id": "V1005",
        "rfid_tag": "SANY-RFID-005",
        "vin": "SANYDEMO00000005A",
        "vehicle_class": "SCC450A-6 - Crawler Crane"
    },

    {
        "vehicle_id": "V1006",
        "rfid_tag": "SANY-RFID-006",
        "vin": "SANYDEMO00000006A",
        "vehicle_class": "SKT130 PRO - Mining Truck"
    },

    {
        "vehicle_id": "V1007",
        "rfid_tag": "SANY-RFID-007",
        "vin": "SANYDEMO00000007A",
        "vehicle_class": "STG170C-10 - Motor Grader"
    },

    {
        "vehicle_id": "V1008",
        "rfid_tag": "SANY-RFID-008",
        "vin": "SANYDEMO00000008A",
        "vehicle_class": "SCP350C - Forklift"
    }

]


# ============================================================
# CREATE FLASK APPLICATION
# ============================================================

app = create_app()


# ============================================================
# UPDATE DATABASE
# ============================================================

with app.app_context():

    print()
    print("==============================================")
    print("       SANY VEHICLE DATABASE UPDATE")
    print("==============================================")
    print()

    updated = 0
    not_found = 0

    for data in SANY_VEHICLES:

        vehicle = Vehicle.query.filter_by(
            vehicle_id=data["vehicle_id"]
        ).first()

        # ----------------------------------------------------
        # VEHICLE FOUND
        # ----------------------------------------------------

        if vehicle:

            vehicle.rfid_tag = data["rfid_tag"]

            vehicle.vin = data["vin"]

            vehicle.vehicle_class = data["vehicle_class"]

            updated += 1

            print(
                f"[UPDATED] {data['vehicle_id']} "
                f"-> {data['vehicle_class']}"
            )

        # ----------------------------------------------------
        # VEHICLE NOT FOUND
        # ----------------------------------------------------

        else:

            not_found += 1

            print(
                f"[NOT FOUND] {data['vehicle_id']}"
            )

    # ========================================================
    # COMMIT
    # ========================================================

    try:

        db.session.commit()

        print()
        print("----------------------------------------------")
        print("SANY UPDATE COMPLETED")
        print("----------------------------------------------")

        print(f"Updated vehicles : {updated}")
        print(f"Not found        : {not_found}")

        print()
        print("Vehicle IDs were NOT changed.")
        print("Existing RFID / movement references are preserved.")
        print()

    except Exception as e:

        db.session.rollback()

        print()
        print("----------------------------------------------")
        print("DATABASE UPDATE FAILED")
        print("----------------------------------------------")

        print(f"Error: {e}")
        print()