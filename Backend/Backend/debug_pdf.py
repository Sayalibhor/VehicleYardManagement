from pypdf import PdfReader

pdf_path = r"C:\VehicleYardManagement\Backend\backend\entry_uploads"

import os

files = [
    f for f in os.listdir(pdf_path)
    if f.lower().endswith(".pdf")
]

print("=" * 70)
print("PDF FILES FOUND")
print("=" * 70)

for i, f in enumerate(files, start=1):
    print(i, f)

if not files:
    print("No PDF found.")
    exit()

selected_file = os.path.join(pdf_path, files[-1])

print()
print("Reading:")
print(selected_file)
print()

reader = PdfReader(selected_file)

print("Total pages:", len(reader.pages))

for page_number, page in enumerate(reader.pages[:2], start=1):

    print()
    print("=" * 70)
    print(f"PAGE {page_number}")
    print("=" * 70)

    text = page.extract_text() or ""

    print(text[:10000])