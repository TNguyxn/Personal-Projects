import pytesseract
from pdf2image import convert_from_path

def main():
    # Path to your PDF
    pdf_path = "Class-2 Axioms of Probability.pdf"

    # Convert PDF pages to images
    pages = convert_from_path(pdf_path)

    # Open a text file to save all extracted text
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        for i, page in enumerate(pages):
            text = pytesseract.image_to_string(page)
            f.write(f"--- Page {i+1} ---\n{text}\n\n")
            print(f"Page {i+1} done.")

main()