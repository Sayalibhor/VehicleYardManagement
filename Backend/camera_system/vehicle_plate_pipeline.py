
import cv2
import os
import re
import pytesseract
from ultralytics import YOLO


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IMAGE_PATH = os.path.join(
    BASE_DIR,
    "Test_image",
    "car_plate_test.jpg"
)

MODEL_NAME = "yolo11n.pt"

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# OUTPUT FOLDER
# ============================================================

PLATE_FOLDER = os.path.join(
    BASE_DIR,
    "plate_crops"
)

os.makedirs(
    PLATE_FOLDER,
    exist_ok=True
)


# ============================================================
# YOLO MODEL
# ============================================================

print("Loading YOLO model...")

model = YOLO(MODEL_NAME)


# ============================================================
# VEHICLE CLASSES
# ============================================================

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}


# ============================================================
# CLEAN OCR TEXT
# ============================================================

def clean_text(text):

    text = text.upper()

    text = re.sub(
        r"[^A-Z0-9]",
        "",
        text
    )

    return text


# ============================================================
# CHECK WHETHER OCR RESULT LOOKS VALID
# ============================================================

def is_valid_plate_text(text):

    if not text:
        return False

    # Typical Indian plate length
    if len(text) < 5:
        return False

    if len(text) > 12:
        return False

    # Must contain letters and numbers
    has_letter = any(
        char.isalpha()
        for char in text
    )

    has_number = any(
        char.isdigit()
        for char in text
    )

    if not has_letter:
        return False

    if not has_number:
        return False

    return True


# ============================================================
# OCR FUNCTION
# ============================================================

def run_ocr(image, method_name):

    config = (
        "--psm 7 "
        "-c tessedit_char_whitelist="
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )

    raw_text = pytesseract.image_to_string(
        image,
        config=config
    )

    text = clean_text(raw_text)

    return {
        "method": method_name,
        "text": text
    }


# ============================================================
# PREPROCESS PLATE
# ============================================================

def preprocess_plate(plate):

    # --------------------------------------------------------
    # Resize
    # --------------------------------------------------------

    enlarged = cv2.resize(
        plate,
        None,
        fx=6,
        fy=6,
        interpolation=cv2.INTER_CUBIC
    )


    # --------------------------------------------------------
    # Grayscale
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        enlarged,
        cv2.COLOR_BGR2GRAY
    )


    # --------------------------------------------------------
    # Light blur
    # --------------------------------------------------------

    gray_blur = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )


    # ========================================================
    # METHOD 1 - OTSU
    # ========================================================

    otsu = cv2.threshold(
        gray_blur,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]


    # ========================================================
    # METHOD 2 - ADAPTIVE
    # ========================================================

    adaptive = cv2.adaptiveThreshold(
        gray_blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        5
    )


    # ========================================================
    # METHOD 3 - CLAHE
    # ========================================================

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(
        gray
    )


    clahe_threshold = cv2.threshold(
        enhanced,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]


    # ========================================================
    # METHOD 4 - NORMAL GRAYSCALE
    # ========================================================

    normal = gray


    return {
        "normal": normal,
        "otsu": otsu,
        "adaptive": adaptive,
        "clahe": clahe_threshold
    }


# ============================================================
# FIND PLATE CANDIDATES
# ============================================================

def find_plate_candidates(vehicle_crop):

    gray = cv2.cvtColor(
        vehicle_crop,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )


    # --------------------------------------------------------
    # Edge detection
    # --------------------------------------------------------

    edges = cv2.Canny(
        gray,
        80,
        180
    )


    # --------------------------------------------------------
    # Dilate
    # --------------------------------------------------------

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (3, 3)
    )

    edges = cv2.dilate(
        edges,
        kernel,
        iterations=1
    )


    # --------------------------------------------------------
    # Contours
    # --------------------------------------------------------

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )


    candidates = []

    height, width = gray.shape


    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        if h <= 0:
            continue

        ratio = w / float(h)

        area = w * h


        # ----------------------------------------------------
        # Plate shape filters
        # ----------------------------------------------------

        if ratio < 2.0:
            continue

        if ratio > 6.5:
            continue

        if w < 40:
            continue

        if h < 10:
            continue

        if area < 400:
            continue


        if x < 0 or y < 0:
            continue

        if x + w > width:
            continue

        if y + h > height:
            continue


        candidates.append({
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "area": area,
            "ratio": ratio
        })


    # --------------------------------------------------------
    # Largest candidates first
    # --------------------------------------------------------

    candidates.sort(
        key=lambda item: item["area"],
        reverse=True
    )


    return candidates


# ============================================================
# OCR ONE PLATE
# ============================================================

def analyze_plate(plate):

    processed = preprocess_plate(
        plate
    )


    results = []


    # --------------------------------------------------------
    # Normal
    # --------------------------------------------------------

    results.append(
        run_ocr(
            processed["normal"],
            "Normal"
        )
    )


    # --------------------------------------------------------
    # OTSU
    # --------------------------------------------------------

    results.append(
        run_ocr(
            processed["otsu"],
            "OTSU"
        )
    )


    # --------------------------------------------------------
    # Adaptive
    # --------------------------------------------------------

    results.append(
        run_ocr(
            processed["adaptive"],
            "Adaptive"
        )
    )


    # --------------------------------------------------------
    # CLAHE
    # --------------------------------------------------------

    results.append(
        run_ocr(
            processed["clahe"],
            "CLAHE"
        )
    )


    return results


# ============================================================
# SELECT BEST OCR RESULT
# ============================================================

def select_best_result(results):

    valid_results = []

    for result in results:

        text = result["text"]

        if is_valid_plate_text(text):

            valid_results.append(
                text
            )


    if not valid_results:

        return None


    # --------------------------------------------------------
    # Count repeated OCR results
    # --------------------------------------------------------

    counts = {}

    for text in valid_results:

        counts[text] = (
            counts.get(text, 0) + 1
        )


    # --------------------------------------------------------
    # Most repeated result
    # --------------------------------------------------------

    best_text = max(
        counts,
        key=counts.get
    )


    return {
        "text": best_text,
        "votes": counts[best_text],
        "total_valid_results": len(valid_results)
    }


# ============================================================
# PROCESS IMAGE
# ============================================================

def process_image():

    print("===================================")
    print(" MULTI-OCR VEHICLE PLATE TEST")
    print("===================================")

    print(
        f"Image: {IMAGE_PATH}"
    )


    # ========================================================
    # CHECK IMAGE
    # ========================================================

    if not os.path.exists(
        IMAGE_PATH
    ):

        print("\nERROR:")
        print("Image not found.")

        return


    image = cv2.imread(
        IMAGE_PATH
    )


    if image is None:

        print("\nERROR:")
        print("Could not read image.")

        return


    print(
        f"Image size: "
        f"{image.shape[1]} x "
        f"{image.shape[0]}"
    )


    # ========================================================
    # YOLO
    # ========================================================

    print("\nRunning YOLO...")

    results = model.predict(
        source=IMAGE_PATH,
        conf=0.40,
        verbose=False
    )


    vehicle_count = 0


    # ========================================================
    # VEHICLE LOOP
    # ========================================================

    for result in results:

        if result.boxes is None:
            continue


        for box in result.boxes:

            class_id = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )


            if class_id not in VEHICLE_CLASSES:
                continue


            vehicle_count += 1


            # ------------------------------------------------
            # Bounding box
            # ------------------------------------------------

            x1, y1, x2, y2 = (
                box.xyxy[0].tolist()
            )


            x1 = max(
                0,
                int(x1)
            )

            y1 = max(
                0,
                int(y1)
            )

            x2 = min(
                image.shape[1],
                int(x2)
            )

            y2 = min(
                image.shape[0],
                int(y2)
            )


            vehicle_crop = image[
                y1:y2,
                x1:x2
            ]


            print("\n-----------------------------------")

            print(
                f"Vehicle {vehicle_count}"
            )

            print(
                f"Type       : "
                f"{VEHICLE_CLASSES[class_id]}"
            )

            print(
                f"Confidence : "
                f"{confidence:.4f}"
            )

            print(
                f"Bounding Box: "
                f"({x1}, {y1}, {x2}, {y2})"
            )


            # =================================================
            # FIND PLATES
            # =================================================

            candidates = find_plate_candidates(
                vehicle_crop
            )


            print(
                f"Plate candidates: "
                f"{len(candidates)}"
            )


            if not candidates:

                print(
                    "Number Plate: "
                    "Not detected"
                )

                continue


            # =================================================
            # TEST CANDIDATES
            # =================================================

            best_candidate_result = None


            max_candidates = min(
                len(candidates),
                10
            )


            for index in range(
                max_candidates
            ):

                candidate = candidates[index]


                px = candidate["x"]
                py = candidate["y"]
                pw = candidate["w"]
                ph = candidate["h"]


                plate = vehicle_crop[
                    py:py + ph,
                    px:px + pw
                ]


                # ------------------------------------------------
                # Save crop
                # ------------------------------------------------

                crop_filename = (
                    f"vehicle_{vehicle_count}"
                    f"_candidate_{index + 1}.jpg"
                )


                crop_path = os.path.join(
                    PLATE_FOLDER,
                    crop_filename
                )


                cv2.imwrite(
                    crop_path,
                    plate
                )


                # ------------------------------------------------
                # OCR
                # ------------------------------------------------

                ocr_results = analyze_plate(
                    plate
                )


                print(
                    f"\nCandidate {index + 1}"
                )

                print(
                    f"Size  : "
                    f"{pw} x {ph}"
                )

                print(
                    f"Ratio : "
                    f"{candidate['ratio']:.2f}"
                )


                for ocr_result in ocr_results:

                    text = (
                        ocr_result["text"]
                    )

                    print(
                        f"  "
                        f"{ocr_result['method']:<10}"
                        f": "
                        f"{text or 'No text'}"
                    )


                # ------------------------------------------------
                # Best result for this candidate
                # ------------------------------------------------

                candidate_best = select_best_result(
                    ocr_results
                )


                if candidate_best:

                    print(
                        f"  BEST      : "
                        f"{candidate_best['text']}"
                    )

                    print(
                        f"  VOTES     : "
                        f"{candidate_best['votes']}/"
                        f"{candidate_best['total_valid_results']}"
                    )


                    if best_candidate_result is None:

                        best_candidate_result = {
                            "text": candidate_best["text"],
                            "votes": candidate_best["votes"],
                            "candidate": index + 1,
                            "bbox": candidate
                        }


                    elif (
                        candidate_best["votes"]
                        >
                        best_candidate_result["votes"]
                    ):

                        best_candidate_result = {
                            "text": candidate_best["text"],
                            "votes": candidate_best["votes"],
                            "candidate": index + 1,
                            "bbox": candidate
                        }


            # =================================================
            # VEHICLE FINAL RESULT
            # =================================================

            print("\n-----------------------------------")


            if best_candidate_result:

                print(
                    "BEST AUTOMATIC OCR RESULT"
                )

                print(
                    f"Vehicle Number : "
                    f"{best_candidate_result['text']}"
                )

                print(
                    f"Candidate      : "
                    f"{best_candidate_result['candidate']}"
                )

                print(
                    f"Votes          : "
                    f"{best_candidate_result['votes']}"
                )

                bbox = (
                    best_candidate_result["bbox"]
                )

                print(
                    "Plate Box      : "
                    f"x={bbox['x']}, "
                    f"y={bbox['y']}, "
                    f"w={bbox['w']}, "
                    f"h={bbox['h']}"
                )

                print(
                    "Status         : "
                    "OCR candidate found"
                )

            else:

                print(
                    "Vehicle Number : "
                    "Not readable"
                )

                print(
                    "Status         : "
                    "OCR failed"
                )


    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n===================================")
    print(" FINAL SUMMARY")
    print("===================================")

    print(
        f"Vehicles detected: "
        f"{vehicle_count}"
    )

    print(
        "Automatic plate detection: Completed"
    )

    print(
        "Multi-method OCR: Completed"
    )

    print("===================================")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        process_image()

    except Exception as error:

        print("\n===================================")
        print(" ERROR")
        print("===================================")

        print(error)