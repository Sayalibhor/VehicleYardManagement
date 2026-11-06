import cv2
import os
from datetime import datetime


# =========================================================
# CAMERA SETTINGS
# =========================================================

CAMERA_INDEX = 0

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

IMAGE_FOLDER = os.path.join(
    BASE_DIR,
    "captured_images"
)

os.makedirs(
    IMAGE_FOLDER,
    exist_ok=True
)


# =========================================================
# OPEN CAMERA
# =========================================================

def open_camera():

    camera = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not camera.isOpened():

        print(
            "ERROR: Camera could not be opened."
        )

        return None

    print(
        "Camera opened successfully."
    )

    return camera


# =========================================================
# CAPTURE ONE IMAGE
# =========================================================

def capture_image(camera):

    success, frame = camera.read()

    if not success:

        print(
            "ERROR: Could not capture frame."
        )

        return None

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        "patrol_"
        + timestamp
        + ".jpg"
    )

    image_path = os.path.join(
        IMAGE_FOLDER,
        filename
    )

    cv2.imwrite(
        image_path,
        frame
    )

    print(
        f"Image saved: {image_path}"
    )

    return image_path


# =========================================================
# LIVE CAMERA TEST
# =========================================================

def run_camera_test():

    camera = open_camera()

    if camera is None:
        return

    print()
    print("===================================")
    print(" CAMERA TEST STARTED")
    print("===================================")
    print()
    print("Press SPACE to capture image")
    print("Press Q to quit")
    print()

    while True:

        success, frame = camera.read()

        if not success:

            print(
                "ERROR: Failed to read camera."
            )

            break

        cv2.imshow(
            "Parking Camera Test",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        # SPACE = capture
        if key == 32:

            capture_image(
                camera
            )

        # Q = quit
        elif key == ord("q"):

            break

    camera.release()

    cv2.destroyAllWindows()

    print(
        "Camera test stopped."
    )


# =========================================================
# RUN TEST
# =========================================================

if __name__ == "__main__":

    run_camera_test()