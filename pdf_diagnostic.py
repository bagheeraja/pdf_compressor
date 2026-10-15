import tkinter as tk
from tkinter import filedialog
from pypdf import PdfReader


def select_pdf_file() -> str:
    """Opens a native GUI file dialog to select a PDF file."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # Bring dialog to the front

    file_path = filedialog.askopenfilename(
        title="Select a PDF File to Inspect",
        filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
    )
    return file_path


if __name__ == "__main__":
    selected_file = select_pdf_file()

    if selected_file:
        print(f"\nAnalyzing '{selected_file}'...\n")
        reader = PdfReader(selected_file)
        print(f"Total Pages: {len(reader.pages)}")

        image_count = 0
        for i, page in enumerate(reader.pages):
            image_count += len(page.images)
            for img in page.images:
                print(f"Page {i+1} Image: {img.name} ({len(img.data)} bytes)")

        print(f"\nTotal embedded images found: {image_count}")
    else:
        print("No file selected. Exiting.")