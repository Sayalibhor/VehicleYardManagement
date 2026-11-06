import cv2
import os


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

IMAGE_PATH = os.path.join(
    BASE_DIR,
    "Test_image",
    "car_plate_test.jpg"
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "plate_crops"
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


print("===================================")
print(" NUMBER PLATE CROP")
print("===================================")

print(f"Image: {IMAGE_PATH}")

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("ERROR: Image could not be opened.")
    exit()


height, width = image.shape[:2]

print("\nImage size:")
print(f"Width  : {width}")
print(f"Height : {height}")

print("\nEnter the number plate coordinates.")
print("x = left position")
print("y = top position")
print("w = plate width")
print("h = plate height")

print("\nExample:")
print("x = 100")
print("y = 200")
print("w = 150")
print("h = 40")


# ------------------------------------------------------------
# INPUT
# ------------------------------------------------------------

try:

    x = int(input("\nEnter x: "))
    y = int(input("Enter y: "))
    w = int(input("Enter width: "))
    h = int(input("Enter height: "))

except ValueError:

    print("\nERROR: Please enter numbers only.")
    exit()


# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

if x < 0 or y < 0 or w <= 0 or h <= 0:

    print("\nERROR: Invalid coordinates.")
    exit()


if x + w > width or y + h > height:

    print("\nERROR: Crop goes outside image.")
    exit()


# ------------------------------------------------------------
# CROP
# ------------------------------------------------------------

plate = image[
    y:y + h,
    x:x + w
]


# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

output_path = os.path.join(
    OUTPUT_FOLDER,
    "manual_plate.jpg"
)

success = cv2.imwrite(
    output_path,
    plate
)

if not success:

    print("\nERROR: Could not save plate.")
    exit()


print("\n===================================")
print(" PLATE CROP SAVED")
print("===================================")

print(
    f"Path: {output_path}"
)

print(
    f"Coordinates: x={x}, y={y}, "
    f"width={w}, height={h}"
)