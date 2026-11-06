import cv2
import os
import pytesseract
import re


# ============================================================
# BASE PATH
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# MANUAL CROPPED NUMBER PLATE IMAGE
# ============================================================

IMAGE_PATH = os.path.join(
    BASE_DIR,
    "plate_crops",
    "manual_plate.jpg"
)


# ============================================================
# TESSERACT PATH
# ============================================================

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# CLEAN OCR TEXT
# ============================================================

def clean_text(text):

    text = text.upper()

    # Remove spaces, symbols and special characters
    text = re.sub(r"[^A-Z0-9]", "", text)

    return text


# ============================================================
# OCR FUNCTION
# ============================================================

def run_ocr(image, psm):

    config = (
        f"--psm {psm} "
        "-c tessedit_char_whitelist="
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )

    text = pytesseract.image_to_string(
        image,
        config=config
    )

    return clean_text(text)


# ============================================================
# MAIN
# ============================================================

def main():

    print("===================================")
    print(" DIRECT NUMBER PLATE OCR TEST")
    print("===================================")

    print(f"Image: {IMAGE_PATH}")

    # --------------------------------------------------------
    # Check image
    # --------------------------------------------------------

    if not os.path.exists(IMAGE_PATH):

        print("\nERROR:")
        print("Manual plate image was not found.")

        print("\nExpected path:")
        print(IMAGE_PATH)

        print("\nFirst run:")
        print("python manual_plate_crop.py")

        return


    # --------------------------------------------------------
    # Read image
    # --------------------------------------------------------

    image = cv2.imread(IMAGE_PATH)

    if image is None:

        print("\nERROR:")
        print("Could not read manual_plate.jpg")

        return


    print("\nOriginal image size:")

    height, width = image.shape[:2]

    print(f"Width  : {width}")
    print(f"Height : {height}")


    # ========================================================
    # STEP 1 - ENLARGE IMAGE
    # ========================================================

    enlarged = cv2.resize(
        image,
        None,
        fx=6,
        fy=6,
        interpolation=cv2.INTER_CUBIC
    )


    # ========================================================
    # STEP 2 - GRAYSCALE
    # ========================================================

    gray = cv2.cvtColor(
        enlarged,
        cv2.COLOR_BGR2GRAY
    )


    # ========================================================
    # STEP 3 - CONTRAST
    # ========================================================

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )


    # ========================================================
    # PREPROCESSING 1
    # OTSU THRESHOLD
    # ========================================================

    threshold_otsu = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]


    # ========================================================
    # PREPROCESSING 2
    # ADAPTIVE THRESHOLD
    # ========================================================

    threshold_adaptive = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        5
    )


    # ========================================================
    # PREPROCESSING 3
    # BLACKHAT / MORPHOLOGY
    # ========================================================

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5)
    )

    blackhat = cv2.morphologyEx(
        gray,
        cv2.MORPH_BLACKHAT,
        kernel
    )

    threshold_blackhat = cv2.threshold(
        blackhat,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]


    # ========================================================
    # SAVE PREPROCESSED IMAGES
    # ========================================================

    output_folder = os.path.join(
        BASE_DIR,
        "plate_crops"
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )


    otsu_path = os.path.join(
        output_folder,
        "ocr_otsu.jpg"
    )

    adaptive_path = os.path.join(
        output_folder,
        "ocr_adaptive.jpg"
    )

    blackhat_path = os.path.join(
        output_folder,
        "ocr_blackhat.jpg"
    )


    cv2.imwrite(
        otsu_path,
        threshold_otsu
    )

    cv2.imwrite(
        adaptive_path,
        threshold_adaptive
    )

    cv2.imwrite(
        blackhat_path,
        threshold_blackhat
    )


    # ========================================================
    # OCR TEST
    # ========================================================

    print("\n===================================")
    print(" OCR RESULTS")
    print("===================================")


    # --------------------------------------------------------
    # OTSU - PSM 7
    # --------------------------------------------------------

    result_1 = run_ocr(
        threshold_otsu,
        7
    )

    print("\nMethod 1 - OTSU / PSM 7")

    if result_1:
        print(f"Result: {result_1}")
    else:
        print("Result: No readable text")


    # --------------------------------------------------------
    # OTSU - PSM 8
    # --------------------------------------------------------

    result_2 = run_ocr(
        threshold_otsu,
        8
    )

    print("\nMethod 2 - OTSU / PSM 8")

    if result_2:
        print(f"Result: {result_2}")
    else:
        print("Result: No readable text")


    # --------------------------------------------------------
    # ADAPTIVE - PSM 7
    # --------------------------------------------------------

    result_3 = run_ocr(
        threshold_adaptive,
        7
    )

    print("\nMethod 3 - ADAPTIVE / PSM 7")

    if result_3:
        print(f"Result: {result_3}")
    else:
        print("Result: No readable text")


    # --------------------------------------------------------
    # ADAPTIVE - PSM 8
    # --------------------------------------------------------

    result_4 = run_ocr(
        threshold_adaptive,
        8
    )

    print("\nMethod 4 - ADAPTIVE / PSM 8")

    if result_4:
        print(f"Result: {result_4}")
    else:
        print("Result: No readable text")


    # --------------------------------------------------------
    # BLACKHAT - PSM 7
    # --------------------------------------------------------

    result_5 = run_ocr(
        threshold_blackhat,
        7
    )

    print("\nMethod 5 - BLACKHAT / PSM 7")

    if result_5:
        print(f"Result: {result_5}")
    else:
        print("Result: No readable text")


    # --------------------------------------------------------
    # BLACKHAT - PSM 8
    # --------------------------------------------------------

    result_6 = run_ocr(
        threshold_blackhat,
        8
    )

    print("\nMethod 6 - BLACKHAT / PSM 8")

    if result_6:
        print(f"Result: {result_6}")
    else:
        print("Result: No readable text")


    # ========================================================
    # SUMMARY
    # ========================================================

    all_results = [
        result_1,
        result_2,
        result_3,
        result_4,
        result_5,
        result_6
    ]

    valid_results = [
        result
        for result in all_results
        if result
    ]


    print("\n===================================")
    print(" OCR SUMMARY")
    print("===================================")


    if valid_results:

        print("Possible OCR results:")

        for result in valid_results:

            print(f"  {result}")

        print("\nNOTE:")
        print("These are OCR candidates.")
        print("Do NOT treat them as the real vehicle number")
        print("until the result matches the actual plate.")


    else:

        print("No readable number plate text detected.")


    # ========================================================
    # SAVED FILES
    # ========================================================

    print("\n===================================")
    print(" PREPROCESSED IMAGES")
    print("===================================")

    print(f"OTSU      : {otsu_path}")
    print(f"ADAPTIVE  : {adaptive_path}")
    print(f"BLACKHAT  : {blackhat_path}")


    print("\n===================================")
    print(" OCR TEST FINISHED")
    print("===================================")


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as error:

        print("\n===================================")
        print(" ERROR")
        print("===================================")

        print(error)