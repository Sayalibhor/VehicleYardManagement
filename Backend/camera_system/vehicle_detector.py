from ultralytics import YOLO
import os


# ============================================================
# VEHICLE DETECTOR
# ============================================================

MODEL_NAME = "yolo11n.pt"

# YOLO model load
model = YOLO(MODEL_NAME)


# ============================================================
# STANDARD YOLO VEHICLE CLASSES
# ============================================================
# COCO dataset class IDs
#
# 2 = car
# 3 = motorcycle
# 5 = bus
# 7 = truck
#
# Later we will replace this with our custom
# 8-class yard vehicle model.
# ============================================================

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}


# ============================================================
# VEHICLE DETECTION FUNCTION
# ============================================================

def detect_vehicles(image_path):
    """
    Detect multiple vehicles from one image.

    Parameters:
        image_path (str):
            Full path of input image.

    Returns:
        list:
            One dictionary for every detected vehicle.
    """

    # --------------------------------------------------------
    # Check image
    # --------------------------------------------------------

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # --------------------------------------------------------
    # Run YOLO
    # --------------------------------------------------------

    results = model.predict(
        source=image_path,
        conf=0.40,
        verbose=False
    )

    detected_vehicles = []

    # --------------------------------------------------------
    # Process every detection
    # --------------------------------------------------------

    for result in results:

        if result.boxes is None:
            continue

        for box in result.boxes:

            # Class ID
            class_id = int(box.cls[0])

            # Confidence
            confidence = float(box.conf[0])

            # Ignore non-vehicle objects
            if class_id not in VEHICLE_CLASSES:
                continue

            # ------------------------------------------------
            # Bounding box
            # ------------------------------------------------

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            # ------------------------------------------------
            # Vehicle record
            # ------------------------------------------------

            vehicle = {
                "detection_index": len(detected_vehicles) + 1,

                "class_id": class_id,

                "vehicle_type": VEHICLE_CLASSES[class_id],

                "confidence": round(confidence, 4),

                "bounding_box": {
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "x2": round(x2, 2),
                    "y2": round(y2, 2)
                },

                # These fields will be filled later
                # by number plate / OCR module.
                "vehicle_number": None,
                "vehicle_id": None,
                "rfid_tag": None,
                "parking_area": None,
                "slot_number": None
            }

            detected_vehicles.append(vehicle)

    return detected_vehicles


# ============================================================
# PRINT DETECTION RESULTS
# ============================================================

def print_detection_results(vehicles):

    print("\n===================================")
    print(" DETECTION RESULT")
    print("===================================")

    if not vehicles:

        print("No supported vehicle detected.")
        return

    print(
        f"Total vehicles detected: {len(vehicles)}"
    )

    print("-----------------------------------")

    for vehicle in vehicles:

        print(
            f"Vehicle {vehicle['detection_index']}"
        )

        print(
            f"Type       : {vehicle['vehicle_type']}"
        )

        print(
            f"Confidence : {vehicle['confidence']}"
        )

        print(
            f"Bounding Box: "
            f"{vehicle['bounding_box']}"
        )

        print(
            f"Vehicle No : "
            f"{vehicle['vehicle_number']}"
        )

        print(
            f"Vehicle ID : "
            f"{vehicle['vehicle_id']}"
        )

        print(
            f"RFID Tag   : "
            f"{vehicle['rfid_tag']}"
        )

        print(
            f"Parking    : "
            f"{vehicle['parking_area']}"
        )

        print(
            f"Slot       : "
            f"{vehicle['slot_number']}"
        )

        print("-----------------------------------")


# ============================================================
# TEST IMAGE
# ============================================================

if __name__ == "__main__":

    print("===================================")
    print(" MULTIPLE VEHICLE DETECTION TEST")
    print("===================================")

    # --------------------------------------------------------
    # Current test image
    # --------------------------------------------------------
    # This is only a test image.
    # Later this path will come from the USB camera.
    # --------------------------------------------------------

    image_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "Test_image",
        "sony car.png"
    )

    print(
        f"Image: {image_path}"
    )

    try:

        # ----------------------------------------------------
        # Detect all vehicles
        # ----------------------------------------------------

        vehicles = detect_vehicles(
            image_path
        )

        # ----------------------------------------------------
        # Display results
        # ----------------------------------------------------

        print_detection_results(
            vehicles
        )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        print("\n===================================")
        print(" SUMMARY")
        print("===================================")

        print(
            f"Total detected vehicles: "
            f"{len(vehicles)}"
        )

        print(
            "Vehicle numbers: "
            "Not available yet"
        )

        print(
            "RFID matching: "
            "Not available yet"
        )

        print(
            "Parking slot detection: "
            "Not available yet"
        )

        print(
            "==================================="
        )

    except FileNotFoundError as error:

        print("\nERROR:")
        print(error)

    except Exception as error:

        print("\nUNEXPECTED ERROR:")
        print(error)