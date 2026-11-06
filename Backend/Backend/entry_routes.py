from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import re
import uuid
import json
from werkzeug.utils import secure_filename

from models import (
    db,
    Vehicle,
    Driver,
    ParkingArea,
    VehicleLocationHistory,
    VehicleEntry,
    SAPOutboundEvent
)


# ============================================================
# BLUEPRINT
# ============================================================

entry_bp = Blueprint(
    "entry_bp",
    __name__,
    url_prefix="/api/entry"
)


# ============================================================
# UPLOAD FOLDER
# ============================================================

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "entry_uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

ALLOWED_EXTENSIONS = {
    "pdf",
    "xlsx",
    "xls"
}


# ============================================================
# EXACT PROJECT VEHICLE CLASS MAPPING
# ============================================================

PROJECT_CLASS_MAP = {
    "container": "Container Chassis",
    "container chassis": "Container Chassis",
    "tanker": "Tanker",
    "flatbed": "Flatbed",
    "box truck": "Box Truck",
    "van": "Cargo Van",
    "cargo van": "Cargo Van",
    "chassis": "Container Chassis",
    "heavy rig": "Heavy Trailer",
    "heavy trailer": "Heavy Trailer",
    "trailer": "Semi-Trailer",
    "semi trailer": "Semi-Trailer",
    "semi-trailer": "Semi-Trailer",
    "yard tug": "Yard Tug"
}


# ============================================================
# BASIC HELPERS
# ============================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


def clean_value(value):

    if value is None:
        return ""

    value = str(value).strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


# ============================================================
# DRIVER RESOLVER
#
# IMPORTANT:
# No fake Driver Name is created.
#
# Priority:
# 1. Driver table
# 2. VehicleEntry record
# 3. None
# ============================================================

def resolve_driver_details(
    driver_id="",
    driver_name="",
    license_number=""
):

    driver_id = clean_value(
        driver_id
    )

    driver_name = clean_value(
        driver_name
    )

    license_number = clean_value(
        license_number
    )

    driver = None

    # --------------------------------------------------------
    # First priority: Driver table
    # --------------------------------------------------------

    if driver_id:

        driver = Driver.query.filter_by(
            driver_id=driver_id
        ).first()

    # --------------------------------------------------------
    # If Driver table has actual record,
    # use actual database values.
    # --------------------------------------------------------

    if driver:

        return {
            "driver": driver,
            "driver_id": driver.driver_id,
            "driver_name": driver.full_name,
            "license_number": driver.license_number
        }

    # --------------------------------------------------------
    # If Driver table does not contain the ID,
    # preserve supplied information.
    #
    # Do NOT create fake driver.
    # --------------------------------------------------------

    return {
        "driver": None,
        "driver_id": driver_id or None,
        "driver_name": driver_name or None,
        "license_number": license_number or None
    }


# ============================================================
# FIND BEST DRIVER FOR VEHICLE
#
# Used by QR lookup.
#
# Priority:
# 1. Latest VehicleEntry having Driver ID
# 2. Latest VehicleEntry
# 3. Driver table lookup
# ============================================================

def get_vehicle_driver(vehicle_id):

    vehicle_id = clean_value(
        vehicle_id
    ).upper()

    if not vehicle_id:
        return {
            "driver": None,
            "driver_id": None,
            "driver_name": None,
            "license_number": None
        }

    # --------------------------------------------------------
    # First try latest entry that actually has Driver ID
    # --------------------------------------------------------

    entry_with_driver = VehicleEntry.query.filter(
        VehicleEntry.vehicle_id == vehicle_id,
        VehicleEntry.driver_id.isnot(None),
        VehicleEntry.driver_id != ""
    ).order_by(
        VehicleEntry.entry_id.desc()
    ).first()

    # --------------------------------------------------------
    # If found, resolve Driver table
    # --------------------------------------------------------

    if entry_with_driver:

        driver_id = clean_value(
            entry_with_driver.driver_id
        )

        driver = None

        if driver_id:

            driver = Driver.query.filter_by(
                driver_id=driver_id
            ).first()

        if driver:

            return {
                "driver": driver,
                "driver_id": driver.driver_id,
                "driver_name": driver.full_name,
                "license_number": driver.license_number
            }

        return {
            "driver": None,
            "driver_id": driver_id or None,
            "driver_name": (
                clean_value(
                    entry_with_driver.driver_name
                )
                or None
            ),
            "license_number": (
                clean_value(
                    entry_with_driver.license_number
                )
                or None
            )
        }

    # --------------------------------------------------------
    # Fallback: latest VehicleEntry
    # --------------------------------------------------------

    latest_entry = VehicleEntry.query.filter_by(
        vehicle_id=vehicle_id
    ).order_by(
        VehicleEntry.entry_id.desc()
    ).first()

    if latest_entry:

        driver_id = clean_value(
            latest_entry.driver_id
        )

        driver = None

        if driver_id:

            driver = Driver.query.filter_by(
                driver_id=driver_id
            ).first()

        if driver:

            return {
                "driver": driver,
                "driver_id": driver.driver_id,
                "driver_name": driver.full_name,
                "license_number": driver.license_number
            }

        return {
            "driver": None,
            "driver_id": driver_id or None,
            "driver_name": (
                clean_value(
                    latest_entry.driver_name
                )
                or None
            ),
            "license_number": (
                clean_value(
                    latest_entry.license_number
                )
                or None
            )
        }

    # --------------------------------------------------------
    # Nothing found
    # --------------------------------------------------------

    return {
        "driver": None,
        "driver_id": None,
        "driver_name": None,
        "license_number": None
    }


# ============================================================
# VEHICLE CLASS NORMALIZATION
# ============================================================

def normalize_vehicle_class(value):

    value = clean_value(value)

    if not value:
        return ""

    key = value.lower()

    if key in PROJECT_CLASS_MAP:
        return PROJECT_CLASS_MAP[key]

    if "semi" in key:
        return "Semi-Trailer"

    if "heavy" in key:
        return "Heavy Trailer"

    if "box" in key:
        return "Box Truck"

    if "flat" in key:
        return "Flatbed"

    if "container" in key:
        return "Container Chassis"

    if "chassis" in key:
        return "Container Chassis"

    if "tanker" in key:
        return "Tanker"

    if "van" in key:
        return "Cargo Van"

    if "tug" in key:
        return "Yard Tug"

    return value


# ============================================================
# DATE NORMALIZATION
# ============================================================

def normalize_date_value(date_value):

    date_value = clean_value(
        date_value
    )

    if not date_value:
        return ""

    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d/%m/%Y"
    ]

    for date_format in formats:

        try:

            return datetime.strptime(
                date_value,
                date_format
            ).strftime("%Y-%m-%d")

        except ValueError:
            pass

    return date_value


# ============================================================
# DATE / TIME
# ============================================================

def get_record_datetime(data):

    date_value = normalize_date_value(
        data.get("date", "")
    )

    time_value = clean_value(
        data.get("time", "")
    )

    if date_value and time_value:

        time_formats = [
            "%H:%M:%S",
            "%H:%M"
        ]

        for time_format in time_formats:

            try:

                return datetime.strptime(
                    f"{date_value} {time_value}",
                    f"%Y-%m-%d {time_format}"
                )

            except ValueError:
                pass

    return datetime.utcnow()


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(pdf_path):

    try:

        from pypdf import PdfReader

    except ImportError:

        raise RuntimeError(
            "pypdf is not installed. "
            "Run: pip install pypdf"
        )

    reader = PdfReader(
        pdf_path
    )

    pages = []

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            pages.append(
                page_text
            )

    return "\n".join(
        pages
    )


# ============================================================
# NORMALIZE PDF TEXT
# ============================================================

def normalize_pdf_text(text):

    if not text:
        return ""

    text = text.replace(
        "\r\n",
        "\n"
    )

    text = text.replace(
        "\r",
        "\n"
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# DETECT OPERATIONAL PDF
# ============================================================

def is_operational_pdf(text):

    if not text:
        return False

    operational_title = re.search(
        r"Operational Vehicle",
        text,
        re.IGNORECASE
    )

    operational_header = re.search(
        r"Rec\s*#\s+Driver\s+ID\s+Vehicle\s+ID\s+RFID\s+Tag",
        text,
        re.IGNORECASE
    )

    return bool(
        operational_title
        or operational_header
    )


# ============================================================
# OPERATIONAL PDF RECORD EXTRACTION
# ============================================================

def extract_operational_records(text):

    text = normalize_pdf_text(
        text
    )

    if not text:
        return []

    record_pattern = re.compile(
        r"""
        \b
        (?P<record_no>\d{1,3})
        \s+
        (?P<driver_id>DRV-\d+)
        \s+
        (?P<vehicle_id>V\d+)
        \s+
        (?P<rfid_tag>RF-\d{4}-[A-Z]\d)
        \s+
        (?P<vehicle_class>
            Container
            |
            Tanker
            |
            Flatbed
            |
            Box\s+Truck
            |
            Van
            |
            Chassis
            |
            Heavy\s+Rig
            |
            Trailer
        )
        \s+
        (?P<date>
            \d{4}-\d{1,2}-\d{1,2}
            |
            \d{1,2}/\d{1,2}/\d{4}
        )
        \s+
        (?P<time>
            \d{1,2}:\d{2}:\d{2}
        )
        \s+
        (?P<parking_area>
            Area\s+\d+
        )
        \s+
        (?P<movement>
            Gate\s+Arrival
            |
            Parked
            |
            Shifted
            |
            Ready\s+for\s+Dispatch
        )
        \s+
        (?P<sap_status>
            Synced
            |
            Pending
        )
        \b
        """,
        re.IGNORECASE | re.VERBOSE
    )

    records = []

    seen_record_numbers = set()

    for match in record_pattern.finditer(text):

        data = match.groupdict()

        record_no = int(
            data["record_no"]
        )

        if record_no in seen_record_numbers:
            continue

        seen_record_numbers.add(
            record_no
        )

        driver_id = clean_value(
            data["driver_id"]
        ).upper()

        vehicle_id = clean_value(
            data["vehicle_id"]
        ).upper()

        rfid_tag = clean_value(
            data["rfid_tag"]
        ).upper()

        vehicle_class = normalize_vehicle_class(
            data["vehicle_class"]
        )

        parking_area = clean_value(
            data["parking_area"]
        )

        movement = clean_value(
            data["movement"]
        )

        sap_status = clean_value(
            data["sap_status"]
        )

        date_value = normalize_date_value(
            data["date"]
        )

        time_value = clean_value(
            data["time"]
        )

        if movement.lower() == "gate arrival":
            movement = "Gate Arrival"

        elif movement.lower() == "parked":
            movement = "Parked"

        elif movement.lower() == "shifted":
            movement = "Shifted"

        elif movement.lower() == "ready for dispatch":
            movement = "Ready for Dispatch"

        if sap_status.lower() == "synced":
            sap_status = "Synced"
        else:
            sap_status = "Pending"

        # ----------------------------------------------------
        # IMPORTANT:
        # If Driver table already has this Driver ID,
        # return real Driver Name / License.
        # Otherwise keep them empty.
        # ----------------------------------------------------

        existing_driver = Driver.query.filter_by(
            driver_id=driver_id
        ).first()

        driver_name = ""

        license_number = ""

        if existing_driver:

            driver_name = (
                existing_driver.full_name
            )

            license_number = (
                existing_driver.license_number
            )

        records.append({

            "record_no":
                record_no,

            "driver_id":
                driver_id,

            "vehicle_id":
                vehicle_id,

            "rfid_tag":
                rfid_tag,

            "vehicle_class":
                vehicle_class,

            "date":
                date_value,

            "time":
                time_value,

            "parking_area_id":
                parking_area,

            "parking_area":
                parking_area,

            "movement":
                movement,

            "sap_status":
                sap_status,

            "vin":
                "",

            "driver_name":
                driver_name,

            "license_number":
                license_number,

            "notes":
                (
                    f"Operational PDF Record #{record_no} | "
                    f"Movement: {movement} | "
                    f"SAP: {sap_status}"
                )
        })

    records.sort(
        key=lambda x: x["record_no"]
    )

    print()
    print("=" * 70)
    print("PDF OPERATIONAL RECORD EXTRACTION")
    print("=" * 70)

    print(
        "Records extracted:",
        len(records)
    )

    if records:

        print()
        print("FIRST RECORD:")
        print(records[0])

        print()
        print("LAST RECORD:")
        print(records[-1])

    print("=" * 70)

    return records


# ============================================================
# EXCEL EXTRACTION
# ============================================================

def extract_excel_records(excel_path):

    try:

        import pandas as pd

    except ImportError:

        raise RuntimeError(
            "pandas is not installed. "
            "Run: pip install pandas openpyxl"
        )

    dataframe = pd.read_excel(
        excel_path
    )

    required_columns = [

        "Rec #",
        "Driver ID",
        "Vehicle ID",
        "RFID Tag",
        "Class",
        "Date",
        "Time (UTC)",
        "Parking Area",
        "Movement",
        "SAP"
    ]

    missing_columns = [

        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing Excel columns: "
            + ", ".join(missing_columns)
        )

    records = []

    for _, row in dataframe.iterrows():

        try:

            record_no = int(
                row["Rec #"]
            )

        except Exception:

            record_no = (
                len(records) + 1
            )

        date_value = row["Date"]

        if hasattr(
            date_value,
            "strftime"
        ):

            normalized_date = (
                date_value.strftime(
                    "%Y-%m-%d"
                )
            )

        else:

            normalized_date = normalize_date_value(
                date_value
            )

        time_value = clean_value(
            row["Time (UTC)"]
        )

        parking_area = clean_value(
            row["Parking Area"]
        )

        movement = clean_value(
            row["Movement"]
        )

        sap_status = clean_value(
            row["SAP"]
        )

        driver_id = clean_value(
            row["Driver ID"]
        )

        # ----------------------------------------------------
        # Get actual Driver information if available
        # ----------------------------------------------------

        existing_driver = Driver.query.filter_by(
            driver_id=driver_id
        ).first()

        driver_name = ""

        license_number = ""

        if existing_driver:

            driver_name = (
                existing_driver.full_name
            )

            license_number = (
                existing_driver.license_number
            )

        records.append({

            "record_no":
                record_no,

            "driver_id":
                driver_id,

            "vehicle_id":
                clean_value(
                    row["Vehicle ID"]
                ),

            "rfid_tag":
                clean_value(
                    row["RFID Tag"]
                ),

            "vehicle_class":
                normalize_vehicle_class(
                    row["Class"]
                ),

            "date":
                normalized_date,

            "time":
                time_value,

            "parking_area_id":
                parking_area,

            "parking_area":
                parking_area,

            "movement":
                movement,

            "sap_status":
                sap_status,

            "vin":
                "",

            "driver_name":
                driver_name,

            "license_number":
                license_number,

            "notes":
                (
                    f"Operational Excel Record "
                    f"#{record_no}"
                )
        })

    return records


# ============================================================
# GENERIC LABEL EXTRACTION
# ============================================================

def extract_label_value(text, labels):

    if not text:
        return ""

    lines = text.splitlines()

    for index, line in enumerate(lines):

        current_line = clean_value(
            line
        )

        if not current_line:
            continue

        for label in labels:

            pattern = (
                r"^\s*"
                + re.escape(label)
                + r"\s*[:\-]\s*(.*?)\s*$"
            )

            match = re.match(
                pattern,
                current_line,
                re.IGNORECASE
            )

            if match:

                value = clean_value(
                    match.group(1)
                )

                if value:
                    return value

            if current_line.lower() == label.lower():

                if index + 1 < len(lines):

                    next_value = clean_value(
                        lines[index + 1]
                    )

                    if (
                        next_value
                        and
                        next_value.lower()
                        != label.lower()
                    ):

                        return next_value

    return ""


# ============================================================
# SINGLE VEHICLE DATA EXTRACTION
# ============================================================

def extract_vehicle_data(text):

    vehicle_id = extract_label_value(
        text,
        [
            "Vehicle ID",
            "Vehicle"
        ]
    )

    rfid_tag = extract_label_value(
        text,
        [
            "RFID Tag",
            "RFID"
        ]
    )

    vin = extract_label_value(
        text,
        [
            "VIN",
            "Chassis Number"
        ]
    )

    vehicle_class = extract_label_value(
        text,
        [
            "Class",
            "Vehicle Class"
        ]
    )

    driver_id = extract_label_value(
        text,
        [
            "Driver ID",
            "Driver"
        ]
    )

    driver_name = extract_label_value(
        text,
        [
            "Driver Name",
            "Name"
        ]
    )

    license_number = extract_label_value(
        text,
        [
            "License Number",
            "License"
        ]
    )

    parking_area = extract_label_value(
        text,
        [
            "Parking Area",
            "Area"
        ]
    )

    return {

        "vehicle_id":
            vehicle_id,

        "rfid_tag":
            rfid_tag,

        "vin":
            vin,

        "vehicle_class":
            normalize_vehicle_class(
                vehicle_class
            ),

        "driver_id":
            driver_id,

        "driver_name":
            driver_name,

        "license_number":
            license_number,

        "parking_area_id":
            parking_area,

        "notes":
            "Single vehicle PDF upload"
    }


# ============================================================
# DRIVER
# ============================================================

def create_or_update_driver(
    driver_id,
    driver_name,
    license_number
):

    driver_id = clean_value(
        driver_id
    )

    driver_name = clean_value(
        driver_name
    )

    license_number = clean_value(
        license_number
    )

    # --------------------------------------------------------
    # Driver ID alone is NOT enough to create Driver row
    # because Driver.full_name is required.
    # --------------------------------------------------------

    if not driver_name:

        # If driver already exists, return it.
        if driver_id:

            existing_driver = Driver.query.filter_by(
                driver_id=driver_id
            ).first()

            if existing_driver:
                return existing_driver

        return None

    if not driver_id:

        driver_id = (
            "DRV-"
            + str(uuid.uuid4())[:8].upper()
        )

    if not license_number:

        license_number = (
            "PENDING-"
            + driver_id
        )

    driver = Driver.query.filter_by(
        driver_id=driver_id
    ).first()

    if driver:

        driver.full_name = driver_name

        driver.license_number = (
            license_number
        )

        return driver

    existing_license = Driver.query.filter_by(
        license_number=license_number
    ).first()

    if existing_license:
        return existing_license

    driver = Driver(

        driver_id=driver_id,

        full_name=driver_name,

        license_number=license_number,

        is_active=True
    )

    db.session.add(
        driver
    )

    return driver


# ============================================================
# PARKING AREA FINDER
# ============================================================

def find_parking_area(
    parking_area_value
):

    value = clean_value(
        parking_area_value
    )

    if not value:
        return None

    area = ParkingArea.query.filter_by(
        area_id=value
    ).first()

    if area:
        return area

    area = ParkingArea.query.filter(
        db.func.lower(
            ParkingArea.area_id
        ) == value.lower()
    ).first()

    if area:
        return area

    number_match = re.search(
        r"(\d+)",
        value
    )

    if number_match:

        number = int(
            number_match.group(1)
        )

        candidates = [

            f"AREA_{number:02d}",
            f"AREA_{number}",
            f"AREA-{number:02d}",
            f"AREA-{number}",
            f"Area {number}",
            f"AREA{number}"
        ]

        for candidate in candidates:

            area = ParkingArea.query.filter(
                db.func.lower(
                    ParkingArea.area_id
                ) == candidate.lower()
            ).first()

            if area:
                return area

        all_areas = ParkingArea.query.all()

        for item in all_areas:

            item_number_match = re.search(
                r"(\d+)",
                item.name or ""
            )

            if item_number_match:

                if int(
                    item_number_match.group(1)
                ) == number:

                    return item

    area = ParkingArea.query.filter(
        db.func.lower(
            ParkingArea.name
        ) == value.lower()
    ).first()

    if area:
        return area

    return None


# ============================================================
# MOVEMENT STATUS
# ============================================================

def get_vehicle_status(movement):

    movement = clean_value(
        movement
    ).lower()

    if movement == "gate arrival":
        return "EXPECTED"

    if movement == "parked":
        return "PARKED"

    if movement == "shifted":
        return "SHIFTED"

    if movement == "ready for dispatch":
        return "READY_FOR_DISPATCH"

    return "EXPECTED"


# ============================================================
# SAVE VEHICLE ENTRY
# ============================================================

def save_vehicle_entry(
    data,
    source="MANUAL",
    require_vin=True,
    commit=True
):

    data = data or {}

    vehicle_id = clean_value(
        data.get("vehicle_id")
    ).upper()

    rfid_tag = clean_value(
        data.get("rfid_tag")
    ).upper()

    vin = clean_value(
        data.get("vin")
    ).upper()

    vehicle_class = normalize_vehicle_class(
        data.get("vehicle_class")
    )

    driver_id = clean_value(
        data.get("driver_id")
    )

    driver_name = clean_value(
        data.get("driver_name")
    )

    license_number = clean_value(
        data.get("license_number")
    )

    parking_area_value = clean_value(
        data.get("parking_area_id")
        or
        data.get("parking_area")
    )

    source = clean_value(
        source
    ).upper()

    if not vehicle_id:
        raise ValueError("Vehicle ID is required")

    if not rfid_tag:
        raise ValueError(
            f"RFID Tag is required for {vehicle_id}"
        )

    if not vehicle_class:
        raise ValueError(
            f"Vehicle Class is required for {vehicle_id}"
        )

    if require_vin:

        if not vin:
            raise ValueError(
                f"VIN is required for {vehicle_id}"
            )

        if len(vin) != 17:
            raise ValueError(
                f"VIN must contain exactly 17 characters "
                f"for {vehicle_id}"
            )

        if not re.fullmatch(
            r"[A-HJ-NPR-Z0-9]{17}",
            vin
        ):
            raise ValueError(
                f"Invalid VIN format for {vehicle_id}. "
                "VIN must contain 17 valid characters."
            )

    else:

        if not vin:
            vin = None

    vehicle = Vehicle.query.filter_by(
        vehicle_id=vehicle_id
    ).first()

    rfid_vehicle = Vehicle.query.filter_by(
        rfid_tag=rfid_tag
    ).first()

    if (
        rfid_vehicle
        and
        rfid_vehicle.vehicle_id != vehicle_id
    ):

        raise ValueError(
            f"RFID {rfid_tag} is already assigned "
            f"to vehicle {rfid_vehicle.vehicle_id}"
        )

    vin_vehicle = None

    if vin:

        vin_vehicle = Vehicle.query.filter_by(
            vin=vin
        ).first()

    if (
        vin_vehicle
        and
        vin_vehicle.vehicle_id != vehicle_id
    ):

        raise ValueError(
            f"VIN {vin} is already assigned "
            f"to vehicle {vin_vehicle.vehicle_id}"
        )

    parking_area = None

    if parking_area_value:

        parking_area = find_parking_area(
            parking_area_value
        )

        if not parking_area:
            raise ValueError(
                f"Parking area '{parking_area_value}' "
                f"was not found in database"
            )

        if not parking_area.is_active:
            raise ValueError(
                f"Parking area '{parking_area.name}' "
                f"is inactive"
            )

        if (
            vehicle
            and
            vehicle.current_area_id
            and
            vehicle.current_area_id != parking_area.area_id
        ):

            if (
                parking_area.current_occupancy
                >= parking_area.capacity
            ):

                raise ValueError(
                    f"Parking area '{parking_area.name}' "
                    f"is full"
                )

        elif (
            vehicle
            and
            not vehicle.current_area_id
        ):

            if (
                parking_area.current_occupancy
                >= parking_area.capacity
            ):

                raise ValueError(
                    f"Parking area '{parking_area.name}' "
                    f"is full"
                )

        elif not vehicle:

            if (
                parking_area.current_occupancy
                >= parking_area.capacity
            ):

                raise ValueError(
                    f"Parking area '{parking_area.name}' "
                    f"is full"
                )

    old_area = None

    if (
        vehicle
        and
        vehicle.current_area_id
    ):

        old_area = ParkingArea.query.filter_by(
            area_id=vehicle.current_area_id
        ).first()

    if vehicle:

        vehicle.rfid_tag = rfid_tag

        vehicle.vehicle_class = (
            vehicle_class
        )

        if vin:
            vehicle.vin = vin

    else:

        if not vin:

            raise ValueError(
                f"VIN is required when creating "
                f"new vehicle {vehicle_id}"
            )

        vehicle = Vehicle(

            vehicle_id=vehicle_id,

            rfid_tag=rfid_tag,

            vin=vin,

            vehicle_class=vehicle_class,

            current_status="EXPECTED",

            current_area_id=None
        )

        db.session.add(
            vehicle
        )

    # --------------------------------------------------------
    # DRIVER RESOLUTION
    # --------------------------------------------------------

    driver_info = resolve_driver_details(
        driver_id,
        driver_name,
        license_number
    )

    driver = driver_info["driver"]

    resolved_driver_id = (
        driver_info["driver_id"]
    )

    resolved_driver_name = (
        driver_info["driver_name"]
    )

    resolved_license_number = (
        driver_info["license_number"]
    )

    # --------------------------------------------------------
    # MOVEMENT / SAP
    # --------------------------------------------------------

    movement = clean_value(
        data.get("movement")
    )

    sap_status = clean_value(
        data.get("sap_status")
    )

    vehicle.current_status = (
        get_vehicle_status(
            movement
        )
    )

    if parking_area:

        new_area = parking_area

        if (
            old_area
            and
            old_area.area_id
            != new_area.area_id
        ):

            if old_area.current_occupancy > 0:
                old_area.current_occupancy -= 1

            new_area.current_occupancy += 1

        elif not old_area:

            new_area.current_occupancy += 1

        vehicle.current_area_id = (
            new_area.area_id
        )

    record_no = clean_value(
        data.get("record_no")
    )

    original_notes = clean_value(
        data.get("notes")
    )

    note_parts = []

    if original_notes:
        note_parts.append(
            original_notes
        )

    if record_no:
        note_parts.append(
            f"PDF_RECORD_NO:{record_no}"
        )

    date_value = normalize_date_value(
        data.get("date")
    )

    if date_value:
        note_parts.append(
            f"DATE:{date_value}"
        )

    time_value = clean_value(
        data.get("time")
    )

    if time_value:
        note_parts.append(
            f"TIME:{time_value}"
        )

    if movement:
        note_parts.append(
            f"Movement:{movement}"
        )

    if sap_status:
        note_parts.append(
            f"SAP:{sap_status}"
        )

    if not vin:
        note_parts.append(
            "VIN:NOT_AVAILABLE"
        )

    final_notes = " | ".join(
        note_parts
    )

    entry = VehicleEntry(

        vehicle_id=vehicle_id,

        rfid_tag=rfid_tag,

        vin=vin,

        vehicle_class=vehicle_class,

        driver_id=(
            resolved_driver_id
            if resolved_driver_id
            else None
        ),

        driver_name=(
            resolved_driver_name
            if resolved_driver_name
            else None
        ),

        license_number=(
            resolved_license_number
            if resolved_license_number
            else None
        ),

        parking_area_id=(
            parking_area.area_id
            if parking_area
            else None
        ),

        entry_source=(
            source
            if source
            else "MANUAL"
        ),

        entry_time=get_record_datetime(
            data
        ),

        notes=final_notes
    )

    db.session.add(
        entry
    )

    if parking_area:

        history = VehicleLocationHistory(

            vehicle_id=vehicle_id,

            from_area_id=(
                old_area.area_id
                if old_area
                else None
            ),

            to_area_id=(
                parking_area.area_id
            ),

            movement_type=(
                movement
                if movement
                else "ENTRY"
            ),

            updated_by=(
                source
                if source
                else "SYSTEM"
            ),

            gps_lat=None,

            gps_lng=None,

            recorded_at=get_record_datetime(
                data
            )
        )

        db.session.add(
            history
        )

    if commit:
        db.session.commit()

    return {

        "entry":
            entry.to_dict(),

        "vehicle":
            vehicle.to_dict(),

        "driver": (
            driver.to_dict()
            if driver
            else {
                "driver_id":
                    resolved_driver_id,

                "driver_name":
                    resolved_driver_name,

                "license_number":
                    resolved_license_number
            }
        ),

        "parking_area": (
            parking_area.to_dict()
            if parking_area
            else None
        )
    }


# ============================================================
# EXCEL EXPORT
# ============================================================

def export_entries_to_excel():

    try:

        from openpyxl import Workbook

    except ImportError:

        return {
            "success": False,
            "message": (
                "openpyxl not installed. "
                "Database saved successfully."
            )
        }

    try:

        entries = VehicleEntry.query.order_by(
            VehicleEntry.entry_id.asc()
        ).all()

        excel_path = os.path.join(

            os.path.dirname(
                os.path.abspath(__file__)
            ),

            "vehicle_entries.xlsx"
        )

        workbook = Workbook()

        worksheet = workbook.active

        worksheet.title = (
            "Vehicle Entries"
        )

        headers = [

            "Entry ID",
            "Vehicle ID",
            "RFID Tag",
            "VIN",
            "Vehicle Class",
            "Driver ID",
            "Driver Name",
            "License Number",
            "Parking Area",
            "Entry Source",
            "Entry Time",
            "Notes"
        ]

        worksheet.append(
            headers
        )

        for entry in entries:

            worksheet.append([

                entry.entry_id,
                entry.vehicle_id,
                entry.rfid_tag,
                entry.vin or "",
                entry.vehicle_class,
                entry.driver_id or "",
                entry.driver_name or "",
                entry.license_number or "",
                entry.parking_area_id or "",
                entry.entry_source,
                (
                    entry.entry_time.isoformat()
                    if entry.entry_time
                    else ""
                ),
                entry.notes or ""
            ])

        widths = {

            "A": 10,
            "B": 15,
            "C": 25,
            "D": 20,
            "E": 20,
            "F": 15,
            "G": 20,
            "H": 20,
            "I": 15,
            "J": 15,
            "K": 25,
            "L": 70
        }

        for column, width in widths.items():

            worksheet.column_dimensions[
                column
            ].width = width

        workbook.save(
            excel_path
        )

        return {

            "success": True,

            "path":
                excel_path,

            "record_count":
                len(entries)
        }

    except PermissionError:

        return {

            "success": False,

            "message": (
                "vehicle_entries.xlsx is open. "
                "Close the Excel file and try again."
            )
        }

    except Exception as e:

        return {

            "success": False,

            "message":
                str(e)
        }


# ============================================================
# GET ALL VEHICLE ENTRY RECORDS
# ============================================================

@entry_bp.route(
    "/entries",
    methods=["GET"]
)
def get_vehicle_entries():

    try:

        limit_value = request.args.get(
            "limit",
            default=500,
            type=int
        )

        if limit_value <= 0:
            limit_value = 500

        if limit_value > 1000:
            limit_value = 1000

        entries = VehicleEntry.query.order_by(
            VehicleEntry.entry_id.desc()
        ).limit(
            limit_value
        ).all()

        records = [
            entry.to_dict()
            for entry in entries
        ]

        return jsonify({

            "status":
                "SUCCESS",

            "message":
                "Vehicle entry records loaded successfully",

            "record_count":
                len(records),

            "records":
                records,

            "data":
                records

        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "status":
                "ERROR",

            "message":
                str(e),

            "record_count":
                0,

            "records":
                [],

            "data":
                []

        }), 500


# ============================================================
# RECENT VEHICLE ENTRY RECORDS
# ============================================================

@entry_bp.route(
    "/recent",
    methods=["GET"]
)
def get_recent_vehicle_entries():

    try:

        limit_value = request.args.get(
            "limit",
            default=50,
            type=int
        )

        if limit_value <= 0:
            limit_value = 50

        if limit_value > 500:
            limit_value = 500

        entries = VehicleEntry.query.order_by(
            VehicleEntry.entry_id.desc()
        ).limit(
            limit_value
        ).all()

        records = [
            entry.to_dict()
            for entry in entries
        ]

        return jsonify({

            "status":
                "SUCCESS",

            "message":
                "Recent vehicle entries loaded successfully",

            "record_count":
                len(records),

            "records":
                records,

            "data":
                records

        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "status":
                "ERROR",

            "message":
                str(e),

            "record_count":
                0,

            "records":
                [],

            "data":
                []

        }), 500


# ============================================================
# GET SINGLE VEHICLE ENTRY
# ============================================================

@entry_bp.route(
    "/entries/<int:entry_id>",
    methods=["GET"]
)
def get_vehicle_entry(entry_id):

    try:

        entry = VehicleEntry.query.get(
            entry_id
        )

        if not entry:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    f"Vehicle entry {entry_id} not found"

            }), 404

        return jsonify({

            "status":
                "SUCCESS",

            "message":
                "Vehicle entry loaded successfully",

            "data":
                entry.to_dict()

        }), 200

    except Exception as e:

        return jsonify({

            "status":
                "ERROR",

            "message":
                str(e)

        }), 500


# ============================================================
# MANUAL VEHICLE ENTRY
# ============================================================

@entry_bp.route(
    "/manual",
    methods=["POST"]
)
def manual_entry():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    "JSON data is required"

            }), 400

        result = save_vehicle_entry(

            data,

            source="MANUAL",

            require_vin=True,

            commit=True
        )

        excel_result = (
            export_entries_to_excel()
        )

        return jsonify({

            "status":
                "SUCCESS",

            "message":
                "Vehicle entry saved successfully",

            "data":
                result,

            "excel":
                excel_result

        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "status":
                "ERROR",

            "message":
                str(e)

        }), 400


# ============================================================
# PDF / EXCEL UPLOAD
# ============================================================

@entry_bp.route(
    "/pdf",
    methods=["POST"]
)
def upload_operational_file():

    try:

        if "file" not in request.files:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    "No file received",

                "automatic_save":
                    False,

                "database_saved":
                    False

            }), 400

        file = request.files["file"]

        if not file or not file.filename:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    "No file selected",

                "automatic_save":
                    False,

                "database_saved":
                    False

            }), 400

        if not allowed_file(
            file.filename
        ):

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    (
                        "Only PDF, XLSX and XLS "
                        "files are allowed"
                    ),

                "automatic_save":
                    False,

                "database_saved":
                    False

            }), 400

        filename = secure_filename(
            file.filename
        )

        unique_filename = (
            uuid.uuid4().hex[:8]
            + "_"
            + filename
        )

        file_path = os.path.join(
            UPLOAD_FOLDER,
            unique_filename
        )

        file.save(
            file_path
        )

        extension = filename.rsplit(
            ".",
            1
        )[1].lower()

        print()
        print("=" * 70)
        print("FILE UPLOAD / EXTRACTION STARTED")
        print("=" * 70)
        print("File:", filename)
        print("Extension:", extension)
        print("DATABASE SAVE: NO")
        print("=" * 70)

        if extension == "pdf":

            text = extract_pdf_text(
                file_path
            )

            if not text:

                return jsonify({

                    "status":
                        "ERROR",

                    "message":
                        "No readable text found in PDF",

                    "file_name":
                        filename,

                    "record_count":
                        0,

                    "records":
                        [],

                    "data":
                        [],

                    "automatic_save":
                        False,

                    "database_saved":
                        False

                }), 400

            operational_pdf = (
                is_operational_pdf(
                    text
                )
            )

            records = (
                extract_operational_records(
                    text
                )
            )

            if operational_pdf:

                if len(records) != 300:

                    return jsonify({

                        "status":
                            "ERROR",

                        "message":
                            (
                                "Operational PDF detected, "
                                f"but only {len(records)} "
                                "of 300 records were extracted."
                            ),

                        "record_count":
                            len(records),

                        "expected_records":
                            300,

                        "saved_count":
                            0,

                        "skipped_count":
                            0,

                        "failed_count":
                            0,

                        "records":
                            records,

                        "data":
                            records,

                        "saved_records":
                            [],

                        "skipped_records":
                            [],

                        "failed_records":
                            [],

                        "file_name":
                            filename,

                        "file_path":
                            file_path,

                        "automatic_save":
                            False,

                        "database_saved":
                            False

                    }), 400

                return jsonify({

                    "status":
                        "SUCCESS",

                    "message":
                        (
                            "300 operational vehicle "
                            "records extracted successfully. "
                            "No records were saved to "
                            "the database."
                        ),

                    "record_count":
                        len(records),

                    "total_records":
                        len(records),

                    "saved_count":
                        0,

                    "skipped_count":
                        0,

                    "failed_count":
                        0,

                    "records":
                        records,

                    "data":
                        records,

                    "saved_records":
                        [],

                    "skipped_records":
                        [],

                    "failed_records":
                        [],

                    "file_name":
                        filename,

                    "file_path":
                        file_path,

                    "automatic_save":
                        False,

                    "database_saved":
                        False

                }), 200

            if records:

                return jsonify({

                    "status":
                        "SUCCESS",

                    "message":
                        (
                            f"{len(records)} records "
                            "extracted successfully. "
                            "No records were saved."
                        ),

                    "record_count":
                        len(records),

                    "total_records":
                        len(records),

                    "saved_count":
                        0,

                    "skipped_count":
                        0,

                    "failed_count":
                        0,

                    "records":
                        records,

                    "data":
                        records,

                    "saved_records":
                        [],

                    "skipped_records":
                        [],

                    "failed_records":
                        [],

                    "file_name":
                        filename,

                    "file_path":
                        file_path,

                    "automatic_save":
                        False,

                    "database_saved":
                        False

                }), 200

            vehicle_data = (
                extract_vehicle_data(
                    text
                )
            )

            if (
                vehicle_data.get(
                    "vehicle_id"
                )
                or
                vehicle_data.get(
                    "rfid_tag"
                )
            ):

                return jsonify({

                    "status":
                        "SUCCESS",

                    "message":
                        (
                            "Vehicle information "
                            "extracted. "
                            "Review and save manually."
                        ),

                    "record_count":
                        1,

                    "records":
                        [
                            vehicle_data
                        ],

                    "data":
                        [
                            vehicle_data
                        ],

                    "file_name":
                        filename,

                    "file_path":
                        file_path,

                    "automatic_save":
                        False,

                    "database_saved":
                        False

                }), 200

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    (
                        "No vehicle records could be "
                        "extracted from the PDF"
                    ),

                "file_name":
                    filename,

                "file_path":
                    file_path,

                "record_count":
                    0,

                "records":
                    [],

                "data":
                    [],

                "automatic_save":
                    False,

                "database_saved":
                    False

            }), 400

        records = extract_excel_records(
            file_path
        )

        if not records:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    "No records found in Excel file",

                "record_count":
                    0,

                "records":
                    [],

                "data":
                    [],

                "automatic_save":
                    False,

                "database_saved":
                    False

            }), 400

        return jsonify({

            "status":
                "SUCCESS",

            "message":
                (
                    f"{len(records)} operational "
                    "records extracted successfully. "
                    "No records were saved to "
                    "the database."
                ),

            "record_count":
                len(records),

            "total_records":
                len(records),

            "saved_count":
                0,

            "skipped_count":
                0,

            "failed_count":
                0,

            "records":
                records,

            "data":
                records,

            "saved_records":
                [],

            "skipped_records":
                [],

            "failed_records":
                [],

            "file_name":
                filename,

            "file_path":
                file_path,

            "automatic_save":
                False,

            "database_saved":
                False

        }), 200

    except Exception as e:

        db.session.rollback()

        print()
        print("=" * 70)
        print("UPLOAD / EXTRACTION ERROR")
        print("=" * 70)
        print(str(e))
        print("=" * 70)

        return jsonify({

            "status":
                "ERROR",

            "message":
                str(e),

            "record_count":
                0,

            "records":
                [],

            "data":
                [],

            "automatic_save":
                False,

            "database_saved":
                False

        }), 500


# ============================================================
# OPTIONAL OPERATIONAL BULK SAVE
# ============================================================

def save_operational_records(records):

    saved_records = []
    skipped_records = []
    failed_records = []

    for record in records:

        try:

            record_no = record.get(
                "record_no"
            )

            vehicle_id = clean_value(
                record.get("vehicle_id")
            ).upper()

            rfid_tag = clean_value(
                record.get("rfid_tag")
            ).upper()

            vehicle_class = normalize_vehicle_class(
                record.get("vehicle_class")
            )

            driver_id = clean_value(
                record.get("driver_id")
            )

            # ------------------------------------------------
            # Driver information from record
            # ------------------------------------------------

            driver_name = clean_value(
                record.get("driver_name")
            )

            license_number = clean_value(
                record.get("license_number")
            )

            # ------------------------------------------------
            # IMPORTANT DRIVER FIX
            #
            # If Driver ID exists in Driver table,
            # get actual Name + License.
            # ------------------------------------------------

            driver_info = resolve_driver_details(
                driver_id,
                driver_name,
                license_number
            )

            resolved_driver_id = (
                driver_info["driver_id"]
            )

            resolved_driver_name = (
                driver_info["driver_name"]
            )

            resolved_license_number = (
                driver_info["license_number"]
            )

            parking_area_value = clean_value(
                record.get("parking_area_id")
                or
                record.get("parking_area")
            )

            movement = clean_value(
                record.get("movement")
            )

            sap_status = clean_value(
                record.get("sap_status")
            )

            if not vehicle_id:

                failed_records.append({

                    "record_no":
                        record_no,

                    "reason":
                        "Vehicle ID is missing"
                })

                continue

            if not rfid_tag:

                failed_records.append({

                    "record_no":
                        record_no,

                    "vehicle_id":
                        vehicle_id,

                    "reason":
                        "RFID Tag is missing"
                })

                continue

            if not vehicle_class:

                failed_records.append({

                    "record_no":
                        record_no,

                    "vehicle_id":
                        vehicle_id,

                    "reason":
                        "Vehicle Class is missing"
                })

                continue

            duplicate = VehicleEntry.query.filter(

                VehicleEntry.entry_source == "PDF",

                VehicleEntry.vehicle_id == vehicle_id,

                VehicleEntry.notes.like(
                    f"%PDF_RECORD_NO:{record_no}%"
                )

            ).first()

            if duplicate:

                skipped_records.append({

                    "record_no":
                        record_no,

                    "vehicle_id":
                        vehicle_id,

                    "reason":
                        "Already saved"
                })

                continue

            parking_area = find_parking_area(
                parking_area_value
            )

            if (
                parking_area_value
                and
                not parking_area
            ):

                failed_records.append({

                    "record_no":
                        record_no,

                    "vehicle_id":
                        vehicle_id,

                    "reason":
                        (
                            f"Parking area "
                            f"'{parking_area_value}' "
                            "was not found"
                        )
                })

                continue

            existing_vehicle = Vehicle.query.filter_by(
                rfid_tag=rfid_tag
            ).first()

            if existing_vehicle:

                if (
                    existing_vehicle.vehicle_id
                    != vehicle_id
                ):

                    failed_records.append({

                        "record_no":
                            record_no,

                        "vehicle_id":
                            vehicle_id,

                        "reason":
                            (
                                f"RFID {rfid_tag} "
                                "is already assigned "
                                "to "
                                f"{existing_vehicle.vehicle_id}"
                            )
                    })

                    continue

            notes = (

                f"Operational PDF Record #{record_no} | "

                f"PDF_RECORD_NO:{record_no} | "

                f"Movement:{movement} | "

                f"SAP:{sap_status} | "

                "VIN:NOT_AVAILABLE"
            )

            entry = VehicleEntry(

                vehicle_id=vehicle_id,

                rfid_tag=rfid_tag,

                vin=None,

                vehicle_class=vehicle_class,

                driver_id=(
                    resolved_driver_id
                    if resolved_driver_id
                    else None
                ),

                driver_name=(
                    resolved_driver_name
                    if resolved_driver_name
                    else None
                ),

                license_number=(
                    resolved_license_number
                    if resolved_license_number
                    else None
                ),

                parking_area_id=(

                    parking_area.area_id

                    if parking_area

                    else None
                ),

                entry_source="PDF",

                entry_time=get_record_datetime(
                    record
                ),

                notes=notes
            )

            db.session.add(
                entry
            )

            saved_records.append({

                "record_no":
                    record_no,

                "vehicle_id":
                    vehicle_id,

                "rfid_tag":
                    rfid_tag,

                "vehicle_class":
                    vehicle_class,

                "driver_id":
                    resolved_driver_id,

                "driver_name":
                    resolved_driver_name,

                "license_number":
                    resolved_license_number,

                "parking_area": (

                    parking_area.area_id

                    if parking_area

                    else None
                ),

                "movement":
                    movement,

                "sap_status":
                    sap_status
            })

        except Exception as record_error:

            failed_records.append({

                "record_no":
                    record.get("record_no"),

                "vehicle_id":
                    record.get("vehicle_id"),

                "reason":
                    str(record_error)
            })

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        raise

    return {

        "saved_records":
            saved_records,

        "skipped_records":
            skipped_records,

        "failed_records":
            failed_records,

        "saved_count":
            len(saved_records),

        "skipped_count":
            len(skipped_records),

        "failed_count":
            len(failed_records)
    }


# ============================================================
# PDF BULK SAVE
# ============================================================

@entry_bp.route(
    "/pdf/save-bulk",
    methods=["POST"]
)
def save_pdf_bulk():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        records = (
            data.get("records")
            or data.get("data")
            or []
        )

        if not isinstance(
            records,
            list
        ):

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    "records must be an array"

            }), 400

        if not records:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    "No records received"

            }), 400

        result = save_operational_records(
            records
        )

        excel_result = (
            export_entries_to_excel()
        )

        return jsonify({

            "status":
                "SUCCESS",

            "message":
                "Operational records processed successfully",

            "saved_count":
                result["saved_count"],

            "skipped_count":
                result["skipped_count"],

            "failed_count":
                result["failed_count"],

            "saved_records":
                result["saved_records"],

            "skipped_records":
                result["skipped_records"],

            "failed_records":
                result["failed_records"],

            "database_saved":
                True,

            "automatic_save":
                True,

            "excel":
                excel_result

        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "status":
                "ERROR",

            "message":
                str(e)

        }), 500


# ============================================================
# PDF SAVE COMPATIBILITY ROUTE
# ============================================================

@entry_bp.route(
    "/pdf/save",
    methods=["POST"]
)
def save_pdf_records():

    return save_pdf_bulk()


# ============================================================
# QR CODE VEHICLE LOOKUP
#
# IMPORTANT DRIVER FIX
# ============================================================

@entry_bp.route(
    "/qr/vehicle/<vehicle_id>",
    methods=["GET"]
)
def qr_vehicle_lookup(vehicle_id):

    try:

        vehicle_id = clean_value(
            vehicle_id
        ).upper()

        if not vehicle_id:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    "Vehicle ID is required"

            }), 400

        vehicle = Vehicle.query.filter_by(
            vehicle_id=vehicle_id
        ).first()

        if not vehicle:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    f"Vehicle {vehicle_id} was not found",

                "vehicle":
                    None

            }), 404

        # ----------------------------------------------------
        # DRIVER FIX
        #
        # Do NOT simply use latest VehicleEntry.
        # Find valid Driver ID first and then Driver table.
        # ----------------------------------------------------

        driver_info = get_vehicle_driver(
            vehicle.vehicle_id
        )

        driver_data = {

            "driver_id":
                driver_info["driver_id"],

            "driver_name":
                driver_info["driver_name"],

            "license_number":
                driver_info["license_number"]
        }

        parking_area_data = None

        if vehicle.current_area_id:

            parking_area = ParkingArea.query.filter_by(
                area_id=vehicle.current_area_id
            ).first()

            if parking_area:

                parking_area_data = (
                    parking_area.to_dict()
                )

        return jsonify({

            "status":
                "SUCCESS",

            "message":
                "Vehicle found successfully",

            "vehicle": {

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
                    vehicle.current_area_id,

                "last_updated_at":
                    (
                        vehicle.last_updated_at.isoformat()
                        if vehicle.last_updated_at
                        else None
                    )
            },

            "driver":
                driver_data,

            "parking_area":
                parking_area_data

        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "status":
                "ERROR",

            "message":
                str(e)

        }), 500


# ============================================================
# QR CODE VEHICLE ENTRY
# ============================================================

@entry_bp.route(
    "/qr/entry",
    methods=["POST"]
)
def qr_vehicle_entry():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        vehicle_id = clean_value(
            data.get("vehicle_id")
        ).upper()

        if not vehicle_id:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    "Vehicle ID is required"

            }), 400

        vehicle = Vehicle.query.filter_by(
            vehicle_id=vehicle_id
        ).first()

        if not vehicle:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    (
                        f"Vehicle {vehicle_id} "
                        "does not exist in the database"
                    )

            }), 404

        # ----------------------------------------------------
        # PREVENT DUPLICATE ENTRY
        # ----------------------------------------------------

        if vehicle.current_area_id:

            current_area = ParkingArea.query.filter_by(
                area_id=vehicle.current_area_id
            ).first()

            area_name = (
                current_area.name
                if current_area
                else vehicle.current_area_id
            )

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    (
                        f"Vehicle {vehicle_id} is already "
                        f"inside the yard at {area_name}. "
                        "Please perform Vehicle Exit first."
                    ),

                "already_inside":
                    True,

                "current_area_id":
                    vehicle.current_area_id

            }), 400

        parking_area_id = clean_value(

            data.get(
                "parking_area_id"
            )

            or

            data.get(
                "parking_area"
            )
        )

        if not parking_area_id:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    "Parking Area is required"

            }), 400

        parking_area = find_parking_area(
            parking_area_id
        )

        if not parking_area:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    (
                        f"Parking area "
                        f"'{parking_area_id}' "
                        "was not found"
                    )

            }), 404

        if not parking_area.is_active:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    (
                        f"Parking area "
                        f"'{parking_area.name}' "
                        "is inactive"
                    )

            }), 400

        if (
            parking_area.current_occupancy
            >= parking_area.capacity
        ):

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    (
                        f"Parking area "
                        f"'{parking_area.name}' "
                        "is full"
                    )

            }), 400

        movement = clean_value(
            data.get("movement")
        )

        if not movement:
            movement = "Parked"

        # ----------------------------------------------------
        # DRIVER RESOLUTION
        # ----------------------------------------------------

        driver_id = clean_value(
            data.get("driver_id")
        )

        driver_name = clean_value(
            data.get("driver_name")
        )

        license_number = clean_value(
            data.get("license_number")
        )

        # ----------------------------------------------------
        # If frontend didn't send driver,
        # find existing vehicle driver.
        # ----------------------------------------------------

        if not driver_id:

            driver_info = get_vehicle_driver(
                vehicle.vehicle_id
            )

            driver_id = (
                driver_info["driver_id"]
                or ""
            )

            driver_name = (
                driver_info["driver_name"]
                or ""
            )

            license_number = (
                driver_info["license_number"]
                or ""
            )

        else:

            # If Driver ID supplied, resolve actual Driver table.
            driver_info = resolve_driver_details(
                driver_id,
                driver_name,
                license_number
            )

            driver_id = (
                driver_info["driver_id"]
                or ""
            )

            driver_name = (
                driver_info["driver_name"]
                or ""
            )

            license_number = (
                driver_info["license_number"]
                or ""
            )

        entry_data = {

            "vehicle_id":
                vehicle.vehicle_id,

            "rfid_tag":
                vehicle.rfid_tag,

            "vin":
                None,

            "vehicle_class":
                vehicle.vehicle_class,

            "driver_id":
                driver_id,

            "driver_name":
                driver_name,

            "license_number":
                license_number,

            "parking_area_id":
                parking_area.area_id,

            "movement":
                movement,

            "sap_status":
                "Pending",

            "notes":
                "Vehicle entry through QR Code scan"
        }

        result = save_vehicle_entry(

            entry_data,

            source="QR",

            require_vin=False,

            commit=True
        )

        excel_result = (
            export_entries_to_excel()
        )

        return jsonify({

            "status":
                "SUCCESS",

            "message":
                (
                    f"Vehicle {vehicle_id} "
                    "entered successfully through QR Code"
                ),

            "vin_available":
                False,

            "data":
                result,

            "excel":
                excel_result

        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "status":
                "ERROR",

            "message":
                str(e)

        }), 400


# ============================================================
# QR CODE VEHICLE EXIT
#
# QR
#  ↓
# Vehicle ID
#  ↓
# Existing Vehicle
#  ↓
# Check Current Parking Area
#  ↓
# Decrease Occupancy
#  ↓
# Remove Current Area
#  ↓
# Status = EXITED
#  ↓
# Location History
#  ↓
# SAP Outbound Event
# ============================================================

@entry_bp.route(
    "/qr/exit",
    methods=["POST"]
)
def qr_vehicle_exit():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        # ====================================================
        # VEHICLE ID
        # ====================================================

        vehicle_id = clean_value(
            data.get("vehicle_id")
        ).upper()

        if not vehicle_id:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    "Vehicle ID is required"

            }), 400

        # ====================================================
        # FIND VEHICLE
        # ====================================================

        vehicle = Vehicle.query.filter_by(
            vehicle_id=vehicle_id
        ).first()

        if not vehicle:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    (
                        f"Vehicle {vehicle_id} "
                        "does not exist in the database"
                    )

            }), 404

        # ====================================================
        # CHECK VEHICLE IS INSIDE YARD
        # ====================================================

        if not vehicle.current_area_id:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    (
                        f"Vehicle {vehicle_id} "
                        "is not currently parked inside the yard. "
                        "Exit cannot be completed."
                    ),

                "already_exited":
                    True

            }), 400

        # ====================================================
        # CURRENT PARKING AREA
        # ====================================================

        current_area_id = (
            vehicle.current_area_id
        )

        current_area = ParkingArea.query.filter_by(
            area_id=current_area_id
        ).first()

        if not current_area:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    (
                        f"Current parking area "
                        f"{current_area_id} "
                        "was not found."
                    )

            }), 404

        # ====================================================
        # NOTES
        # ====================================================

        notes = clean_value(
            data.get("notes")
        )

        if not notes:

            notes = (
                "Vehicle exit through QR Code scan"
            )

        # ====================================================
        # EXIT TIME
        # ====================================================

        exit_time = datetime.utcnow()

        # ====================================================
        # OCCUPANCY UPDATE
        # ====================================================

        if current_area.current_occupancy > 0:

            current_area.current_occupancy -= 1

        else:

            current_area.current_occupancy = 0

        # ====================================================
        # LOCATION HISTORY
        # ====================================================

        history = VehicleLocationHistory(

            vehicle_id=vehicle.vehicle_id,

            from_area_id=current_area_id,

            to_area_id=None,

            movement_type="Exited Yard",

            updated_by="QR",

            gps_lat=None,

            gps_lng=None,

            recorded_at=exit_time
        )

        db.session.add(
            history
        )

        # ====================================================
        # VEHICLE MASTER UPDATE
        # ====================================================

        vehicle.current_area_id = None

        vehicle.current_status = "EXITED"

        vehicle.last_updated_at = exit_time

        # ====================================================
        # SAP OUTBOUND EVENT
        # ====================================================

        sap_payload = {

            "vehicle_id":
                vehicle.vehicle_id,

            "vehicle_class":
                vehicle.vehicle_class,

            "event_type":
                "Vehicle Exited Yard",

            "event_source":
                "QR Code",

            "previous_parking_area":
                current_area_id,

            "parking_area_name":
                current_area.name,

            "updated_by":
                "QR",

            "timestamp":
                exit_time.isoformat(),

            "sap_status":
                "Pending",

            "notes":
                notes
        }

        sap_event = SAPOutboundEvent(

            event_type=
                "VEHICLE_EXITED_YARD",

            vehicle_id=
                vehicle.vehicle_id,

            payload=
                json.dumps(
                    sap_payload
                ),

            sync_status=
                "PENDING",

            retry_count=
                0,

            sap_response=
                None,

            created_at=
                exit_time,

            processed_at=
                None
        )

        db.session.add(
            sap_event
        )

        # ====================================================
        # COMMIT
        # ====================================================

        db.session.commit()

        # ====================================================
        # EXCEL
        # ====================================================

        excel_result = (
            export_entries_to_excel()
        )

        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "status":
                "SUCCESS",

            "message":
                (
                    f"Vehicle {vehicle_id} "
                    "exited the yard successfully "
                    "through QR Code"
                ),

            "vehicle_id":
                vehicle.vehicle_id,

            "previous_parking_area":
                current_area_id,

            "parking_area":
                current_area.to_dict(),

            "vehicle":
                vehicle.to_dict(),

            "movement":
                "Exited Yard",

            "sap_event":
                {

                    "event_id":
                        sap_event.event_id,

                    "event_type":
                        sap_event.event_type,

                    "sync_status":
                        sap_event.sync_status

                },

            "excel":
                excel_result

        }), 200

    except Exception as e:

        db.session.rollback()

        print()
        print("=" * 70)
        print("QR VEHICLE EXIT ERROR")
        print("=" * 70)
        print(str(e))
        print("=" * 70)

        return jsonify({

            "status":
                "ERROR",

            "message":
                str(e)

        }), 400