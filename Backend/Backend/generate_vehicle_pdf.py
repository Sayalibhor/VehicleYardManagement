from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib.enums import TA_CENTER
from datetime import datetime, timedelta
import random
import os


# ============================================================
# SETTINGS
# ============================================================

TOTAL_RECORDS = 300

OUTPUT_FILE = "vehicle_yard_operational_records_300.pdf"

random.seed(42)


# ============================================================
# PROJECT DATA
# ============================================================

VEHICLE_CLASSES = [
    "Container",
    "Tanker",
    "Flatbed",
    "Box Truck",
    "Van",
    "Chassis",
    "Heavy Rig",
    "Trailer"
]

PARKING_AREAS = [
    "Area 1",
    "Area 2",
    "Area 3",
    "Area 4",
    "Area 5",
    "Area 6",
    "Area 7",
    "Area 8",
    "Area 9",
    "Area 10"
]

MOVEMENTS = [
    "Gate Arrival",
    "Parked",
    "Shifted",
    "Ready for Dispatch"
]

SAP_STATUSES = [
    "Synced",
    "Synced",
    "Synced",
    "Synced",
    "Pending"
]


# ============================================================
# GENERATE 300 RECORDS
# ============================================================

records = []

start_datetime = datetime(
    2026,
    7,
    28,
    6,
    0,
    0
)


for i in range(1, TOTAL_RECORDS + 1):

    vehicle_number = 1000 + i

    driver_number = random.randint(
        1001,
        1050
    )

    rfid_number = random.randint(
        1000,
        9999
    )

    rfid_letter = chr(
        65 + ((i - 1) % 26)
    )

    rfid_suffix = random.randint(
        1,
        9
    )

    vehicle_class = VEHICLE_CLASSES[
        (i - 1) % len(VEHICLE_CLASSES)
    ]

    date_value = (
        start_datetime +
        timedelta(
            days=(i - 1) // 50
        )
    ).strftime(
        "%m/%d/%Y"
    )

    time_value = (
        start_datetime +
        timedelta(
            minutes=(i - 1) * 4,
            seconds=random.randint(0, 59)
        )
    ).strftime(
        "%H:%M:%S"
    )

    parking_area = PARKING_AREAS[
        (i - 1) % len(PARKING_AREAS)
    ]

    movement = MOVEMENTS[
        (i - 1) % len(MOVEMENTS)
    ]

    # Keep most records Synced and some Pending
    if i % 20 == 0:
        sap_status = "Pending"
    else:
        sap_status = "Synced"


    record = [
        i,
        f"DRV-{driver_number}",
        f"V{vehicle_number}",
        f"RF-{rfid_number}-{rfid_letter}{rfid_suffix}",
        vehicle_class,
        date_value,
        time_value,
        parking_area,
        movement,
        sap_status
    ]

    records.append(record)


# ============================================================
# CREATE PDF
# ============================================================

pdf_path = os.path.abspath(
    OUTPUT_FILE
)


doc = SimpleDocTemplate(

    pdf_path,

    pagesize=landscape(A4),

    rightMargin=8 * mm,
    leftMargin=8 * mm,
    topMargin=8 * mm,
    bottomMargin=8 * mm
)


styles = getSampleStyleSheet()


title_style = styles["Title"]

title_style.alignment = TA_CENTER

title_style.fontSize = 17


normal_style = styles["Normal"]

normal_style.alignment = TA_CENTER

normal_style.fontSize = 8


story = []


# ============================================================
# TITLE
# ============================================================

story.append(

    Paragraph(
        "Vehicle Yard Management System",
        title_style
    )

)


story.append(
    Spacer(
        1,
        3 * mm
    )
)


story.append(

    Paragraph(
        "Operational Vehicle Entry Records - 300 Records",
        normal_style
    )

)


story.append(
    Spacer(
        1,
        5 * mm
    )
)


# ============================================================
# TABLE HEADER
# ============================================================

headers = [

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


table_data = [
    headers
] + records


# ============================================================
# COLUMN WIDTHS
# ============================================================

column_widths = [

    11 * mm,   # Rec #

    25 * mm,   # Driver ID

    22 * mm,   # Vehicle ID

    31 * mm,   # RFID Tag

    27 * mm,   # Class

    23 * mm,   # Date

    25 * mm,   # Time

    28 * mm,   # Parking Area

    42 * mm,   # Movement

    20 * mm    # SAP

]


# ============================================================
# TABLE
# ============================================================

table = Table(

    table_data,

    colWidths=column_widths,

    repeatRows=1

)


table.setStyle(

    TableStyle([

        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#1f4e78")
        ),

        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white
        ),

        (
            "FONTNAME",
            (0, 0),
            (-1, 0),
            "Helvetica-Bold"
        ),

        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            6.5
        ),

        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            colors.grey
        ),

        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "CENTER"
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            3
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            3
        ),

        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [
                colors.white,
                colors.HexColor("#f3f6f9")
            ]
        )

    ])

)


story.append(table)


story.append(
    Spacer(
        1,
        4 * mm
    )
)


story.append(

    Paragraph(

        "Format: Rec # | Driver ID | Vehicle ID | RFID Tag | Class | Date | Time (UTC) | Parking Area | Movement | SAP",

        normal_style

    )

)


# ============================================================
# BUILD
# ============================================================

doc.build(story)


print()
print("=" * 60)
print("PDF CREATED SUCCESSFULLY")
print("=" * 60)
print()
print(f"File: {pdf_path}")
print(f"Records: {TOTAL_RECORDS}")
print()
print("Upload this PDF from your Vehicle Entry page.")
print("=" * 60)