import cv2
import os
import re
import pytesseract


# ============================================================
# TESSERACT
# ============================================================

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_vehicle_number(text):

    text = text.upper()

    # Remove spaces and special characters
    text = re.sub(
        r"[^A-Z0-9]",
        "",
        text
    )

    return text


# ============================================================
# OCR FROM PLATE IMAGE
# ============================================================

def read_number_plate(plate_image_path):

    if not os.path.exists(plate_image_path):
        raise FileNotFoundError(
            f"Plate image not found: {plate_image_path}"
        )

    image = cv2.imread(
        plate_image_path
    )

    if image is None:
        raise ValueError(
            "Could not read plate image."
        )

    # --------------------------------------------------------
    # Resize
    # --------------------------------------------------------

    image = cv2.resize(
        image,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )

    # --------------------------------------------------------
    # Grayscale
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------------------------
    # Threshold
    # --------------------------------------------------------

    threshold = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    config = (
        "--psm 7 "
        "-c tessedit_char_whitelist="
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )

    text = pytesseract.image_to_string(
        threshold,
        config=config
    )

    cleaned = clean_vehicle_number(
        text
    )

    return cleaned


# ============================================================
# TEST ALL CANDIDATES
# ============================================================

if __name__ == "__main__":

    print("===================================")
    print(" NUMBER PLATE OCR TEST")
    print("===================================")

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    plate_folder = os.path.join(
        base_dir,
        "plate_crops"
    )

    if not os.path.exists(plate_folder):

        print(
            "ERROR: plate_crops folder not found."
        )

        print(
            "Run number_plate_detector.py first."
        )

        exit()

    files = []

    for filename in os.listdir(
        plate_folder
    ):

        if filename.lower().endswith(
            (".jpg", ".jpeg", ".png")
        ):

            files.append(filename)

    files.sort()

    print(
        f"Plate candidates: {len(files)}"
    )

    print(
        "-----------------------------------"
    )

    for index, filename in enumerate(
        files,
        start=1
    ):

        image_path = os.path.join(
            plate_folder,
            filename
        )

        try:

            vehicle_number = (
                read_number_plate(
                    image_path
                )
            )

            print(
                f"Candidate {index}: "
                f"{filename}"
            )

            if vehicle_number:

                print(
                    f"  OCR Result: "
                    f"{vehicle_number}"
                )

            else:

                print(
                    "  OCR Result: "
                    "No readable text"
                )

        except Exception as error:

            print(
                f"  OCR Error: {error}"
            )

        print(
            "-----------------------------------"
        )

    print(
        "\n==================================="
    )

    print(
        " OCR TEST FINISHED"
    )

    print(
        "==================================="
    )