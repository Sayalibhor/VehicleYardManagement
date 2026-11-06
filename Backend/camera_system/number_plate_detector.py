import cv2
import os


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

INPUT_IMAGE = os.path.join(
    BASE_DIR,
    "Test_image",
    "sony car.png"
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "plate_crops"
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# NUMBER PLATE DETECTION
# ============================================================

def detect_number_plate(image_path):

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            "Could not read image."
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Reduce noise
    gray = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    # Detect edges
    edges = cv2.Canny(
        gray,
        100,
        200
    )

    # Find contours
    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        if w == 0 or h == 0:
            continue

        aspect_ratio = w / float(h)

        area = w * h

        # Typical rectangular plate shape
        if (
            2.0 <= aspect_ratio <= 6.5
            and 500 <= area <= 50000
            and w >= 60
            and h >= 15
        ):

            candidates.append(
                {
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "aspect_ratio": round(
                        aspect_ratio,
                        2
                    ),
                    "area": area
                }
            )

    # Sort largest candidates first
    candidates.sort(
        key=lambda item: item["area"],
        reverse=True
    )

    return image, candidates


# ============================================================
# SAVE PLATE CANDIDATES
# ============================================================

def save_plate_candidates(
    image,
    candidates
):

    saved_files = []

    for index, candidate in enumerate(
        candidates[:5],
        start=1
    ):

        x = candidate["x"]
        y = candidate["y"]
        w = candidate["width"]
        h = candidate["height"]

        plate = image[
            y:y + h,
            x:x + w
        ]

        filename = (
            f"plate_candidate_{index}.jpg"
        )

        output_path = os.path.join(
            OUTPUT_FOLDER,
            filename
        )

        cv2.imwrite(
            output_path,
            plate
        )

        saved_files.append(
            output_path
        )

    return saved_files


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("===================================")
    print(" NUMBER PLATE DETECTION TEST")
    print("===================================")

    print(
        f"Image: {INPUT_IMAGE}"
    )

    try:

        image, candidates = (
            detect_number_plate(
                INPUT_IMAGE
            )
        )

        print("\nCandidates found:")
        print(
            len(candidates)
        )

        if not candidates:

            print(
                "\nNo possible number plate found."
            )

            print(
                "This does NOT mean the vehicle "
                "has no plate."
            )

            print(
                "The plate detector may need "
                "adjustment."
            )

        else:

            print(
                "\n-----------------------------------"
            )

            for index, candidate in enumerate(
                candidates[:5],
                start=1
            ):

                print(
                    f"Candidate {index}"
                )

                print(
                    f"Position : "
                    f"({candidate['x']}, "
                    f"{candidate['y']})"
                )

                print(
                    f"Size     : "
                    f"{candidate['width']} x "
                    f"{candidate['height']}"
                )

                print(
                    f"Ratio    : "
                    f"{candidate['aspect_ratio']}"
                )

                print(
                    f"Area     : "
                    f"{candidate['area']}"
                )

                print(
                    "-----------------------------------"
                )

            saved_files = (
                save_plate_candidates(
                    image,
                    candidates
                )
            )

            print("\nSaved plate candidates:")

            for file_path in saved_files:
                print(file_path)

    except Exception as error:

        print("\nERROR:")
        print(error)

    print(
        "\n==================================="
    )
    print(
        " NUMBER PLATE TEST FINISHED"
    )
    print(
        "==================================="
    )
    