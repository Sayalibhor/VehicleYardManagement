
import json
import urllib.request
import urllib.error


# ============================================================
# CAMERA PATROL SIMULATOR
# ============================================================

API_URL = "http://127.0.0.1:5000/api/camera/patrol/start"

CAMERA_ID = "PARKING_CAMERA_01"


def run_simulated_patrol():

    print("===================================")
    print(" CAMERA PATROL SIMULATOR")
    print("===================================")

    print("Physical camera: NOT CONNECTED")
    print("Mode: TEST IMAGE SIMULATION")
    print(f"Camera ID: {CAMERA_ID}")

    print("\nUsing OCR test result:")
    print("Vehicle Number: GEVS101")

    print("\nIMPORTANT:")
    print("This is an OCR_TEST record.")
    print("It is NOT a confirmed production vehicle.")

    # ========================================================
    # TEST PATROL DATA
    # ========================================================

    payload = {
        "camera_id": CAMERA_ID,
        "detections": [
            {
                "vehicle_number": "GEVS101",
                "vehicle_id": None,
                "rfid_tag": None,
                "parking_area": None,
                "slot_number": None,
                "image_path": "Test_image/car_plate_test.jpg",
                "confidence": 0.9187,
                "detection_status": "OCR_TEST"
            }
        ]
    }

    # Convert Python dictionary to JSON
    data = json.dumps(payload).encode("utf-8")

    # Create API request
    request = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    print("\nSending patrol result to backend...")

    # ========================================================
    # SEND TO FLASK BACKEND
    # ========================================================

    try:

        with urllib.request.urlopen(request, timeout=10) as response:

            response_data = response.read().decode("utf-8")

            result = json.loads(response_data)

            print("\n===================================")
            print(" PATROL RESPONSE")
            print("===================================")

            print(json.dumps(result, indent=4))

            print("\n===================================")
            print(" SIMULATED PATROL COMPLETED")
            print("===================================")

            # IMPORTANT:
            # Return the backend result to scheduler
            return result

    except urllib.error.HTTPError as error:

        print("\n===================================")
        print(" BACKEND ERROR")
        print("===================================")

        print(f"HTTP Status: {error.code}")

        try:

            error_body = error.read().decode("utf-8")

            print(error_body)

        except Exception:

            pass

        return None

    except urllib.error.URLError as error:

        print("\n===================================")
        print(" CONNECTION ERROR")
        print("===================================")

        print("Could not connect to Flask backend.")
        print("Make sure app.py is running.")

        print(f"Details: {error}")

        return None

    except Exception as error:

        print("\n===================================")
        print(" ERROR")
        print("===================================")

        print(error)

        return None


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    result = run_simulated_patrol()

    if result and result.get("success"):

        print("\nPatrol result returned successfully.")

    else:

        print("\nPatrol result failed.")