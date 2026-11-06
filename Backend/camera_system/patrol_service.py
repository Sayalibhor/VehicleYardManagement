import os
import uuid
from datetime import datetime

from camera import open_camera, capture_image


# ============================================================
# CAMERA PATROL SERVICE
# ============================================================

CAMERA_ID = "PARKING_CAMERA_01"


def create_round_id():
    """
    Creates a unique ID for every camera patrol round.
    Example:
    ROUND-20260919-203015-a1b2c3
    """
    return (
        "ROUND-"
        + datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        + "-"
        + uuid.uuid4().hex[:6]
    )


def run_single_patrol():
    """
    Runs one camera patrol round.

    Current stage:
    1. Open camera
    2. Capture image
    3. Return round information

    Vehicle detection and number recognition
    will be added in the next stage.
    """

    round_id = create_round_id()

    print("\n===================================")
    print(" CAMERA PATROL ROUND")
    print("===================================")
    print(f"Round ID : {round_id}")
    print(f"Camera ID: {CAMERA_ID}")

    camera = open_camera()

    if camera is None:
        print("ERROR: Camera could not be opened.")
        return None

    try:
        image_path = capture_image(camera)

        if image_path is None:
            print("ERROR: Image capture failed.")
            return None

        patrol_result = {
            "round_id": round_id,
            "camera_id": CAMERA_ID,
            "captured_at": datetime.utcnow().isoformat(),
            "image_path": image_path,
            "status": "IMAGE_CAPTURED"
        }

        print("\n-----------------------------------")
        print("PATROL RESULT")
        print("-----------------------------------")
        print(f"Round ID    : {patrol_result['round_id']}")
        print(f"Camera ID   : {patrol_result['camera_id']}")
        print(f"Image Path  : {patrol_result['image_path']}")
        print(f"Status      : {patrol_result['status']}")
        print("-----------------------------------")

        return patrol_result

    finally:
        camera.release()

        try:
            import cv2
            cv2.destroyAllWindows()
        except Exception:
            pass


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    result = run_single_patrol()

    if result:
        print("\nCamera patrol test completed successfully.")
    else:
        print("\nCamera patrol test failed.")