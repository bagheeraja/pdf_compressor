import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pymupdf

CONFIG_FILE = "app_config.json"


def load_last_dir() -> str:
    """Loads the last used directory from a local config file if it exists."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("last_destination", "")
        except Exception:
            return ""
    return ""


def save_last_dir(folder_path: str):
    """Saves the chosen destination folder to a local config file."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"last_destination": folder_path}, f)
    except Exception as e:
        print(f"Failed to save config: {e}")


def select_input_pdf(root: tk.Tk, initial_dir: str = "") -> str:
    """Opens a native GUI file dialog to select a PDF file."""
    return filedialog.askopenfilename(
        parent=root,
        title="Select a PDF File to Compress",
        initialdir=initial_dir,
        filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
    )


def select_destination_folder(root: tk.Tk, initial_dir: str = "") -> str:
    """Opens a folder dialog to select where the compressed file will be saved."""
    return filedialog.askdirectory(
        parent=root,
        title="Select Destination Folder for Compressed PDF",
        initialdir=initial_dir,
    )


def show_info(title: str, message: str, parent_window):
    """Displays a pop-up information box."""
    messagebox.showinfo(title, message, parent=parent_window)


def prompt_compression_options(root: tk.Tk) -> dict | None:
    """Displays a GUI dialog allowing the user to configure PyMuPDF compression options."""
    dialog = tk.Toplevel(root)
    dialog.title("PDF Optimization Settings")
    dialog.geometry("425x380")
    dialog.resizable(False, False)
    dialog.attributes("-topmost", True)

    # Center window on screen reliably
    dialog.update_idletasks()
    width = 425
    height = 380
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f"{width}x{height}+{x}+{y}")

    var_stream = tk.BooleanVar(value=True)
    var_dedup = tk.BooleanVar(value=True)
    var_image = tk.BooleanVar(value=True)
    var_quality = tk.IntVar(value=40)
    var_dpi = tk.IntVar(value=72)

    selection_result = {}

    frame = ttk.Frame(dialog, padding="15")
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
        frame, text="Configure Compression Options:", font=("Helvetica", 10, "bold")
    ).pack(anchor="w", pady=(0, 10))

    # Feature 1: Stream Compression
    f1_frame = ttk.Frame(frame)
    f1_frame.pack(fill=tk.X, pady=2)
    ttk.Checkbutton(
        f1_frame, text="Stream Compression & Object Streams", variable=var_stream
    ).pack(side=tk.LEFT)
    ttk.Button(
        f1_frame,
        text="?",
        width=2,
        command=lambda: show_info(
            "Stream Compression Info",
            "Stream & Object Stream Compression:\n\n"
            "Compresses text, vector instructions, and packages metadata objects into efficient zlib streams (deflate=True).",
            dialog,
        ),
    ).pack(side=tk.LEFT, padx=(5, 0))

    # Feature 2: Object Deduplication & Garbage Collection
    f2_frame = ttk.Frame(frame)
    f2_frame.pack(fill=tk.X, pady=2)
    ttk.Checkbutton(
        f2_frame, text="Object Deduplication & Garbage Collection", variable=var_dedup
    ).pack(side=tk.LEFT)
    ttk.Button(
        f2_frame,
        text="?",
        width=2,
        command=lambda: show_info(
            "Deduplication Info",
            "Garbage Collection & Deduplication:\n\n"
            "Deep scrubs unreferenced ghost objects, orphan streams, and merges identical assets (garbage=3).",
            dialog,
        ),
    ).pack(side=tk.LEFT, padx=(5, 0))

    # Feature 3: Image Resampling & Downscaling
    f3_frame = ttk.Frame(frame)
    f3_frame.pack(fill=tk.X, pady=2)
    ttk.Checkbutton(
        f3_frame, text="Image Resampling & Downscaling", variable=var_image
    ).pack(side=tk.LEFT)
    ttk.Button(
        f3_frame,
        text="?",
        width=2,
        command=lambda: show_info(
            "Image Resampling Info",
            "Image Resampling:\n\n"
            "Downsamples high-resolution embedded images down to a target DPI and re-encodes via lossy JPEG compression.",
            dialog,
        ),
    ).pack(side=tk.LEFT, padx=(5, 0))

    # Quality Slider
    quality_frame = ttk.Frame(frame)
    quality_frame.pack(fill=tk.X, pady=(10, 5))
    lbl_quality = ttk.Label(
        quality_frame, text=f"JPEG Image Quality ({var_quality.get()}%):"
    )
    lbl_quality.pack(anchor="w")

    def update_quality_label(val):
        lbl_quality.config(text=f"JPEG Image Quality ({int(float(val))}%):")

    slider_quality = ttk.Scale(
        quality_frame,
        from_=10,
        to=90,
        variable=var_quality,
        command=update_quality_label,
    )
    slider_quality.pack(fill=tk.X, pady=2)

    # Target DPI Slider
    dpi_frame = ttk.Frame(frame)
    dpi_frame.pack(fill=tk.X, pady=(5, 10))
    lbl_dpi = ttk.Label(dpi_frame, text=f"Target Image Resolution ({var_dpi.get()} DPI):")
    lbl_dpi.pack(anchor="w")

    def update_dpi_label(val):
        lbl_dpi.config(text=f"Target Image Resolution ({int(float(val))} DPI):")

    slider_dpi = ttk.Scale(
        dpi_frame,
        from_=72,
        to=150,
        variable=var_dpi,
        command=update_dpi_label,
    )
    slider_dpi.pack(fill=tk.X, pady=2)

    def toggle_sliders(*args):
        state = "normal" if var_image.get() else "disabled"
        slider_quality.config(state=state)
        slider_dpi.config(state=state)

    var_image.trace_add("write", toggle_sliders)

    def on_confirm():
        if not (var_stream.get() or var_dedup.get() or var_image.get()):
            messagebox.showwarning(
                "No Options Selected",
                "Please select at least one optimization option.",
                parent=dialog,
            )
            return

        selection_result["do_stream"] = var_stream.get()
        selection_result["do_dedup"] = var_dedup.get()
        selection_result["do_image"] = var_image.get()
        selection_result["image_quality"] = var_quality.get()
        selection_result["target_dpi"] = var_dpi.get()
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill=tk.X, pady=(10, 0))
    ttk.Button(btn_frame, text="Compress", command=on_confirm).pack(
        side=tk.RIGHT, padx=(5, 0)
    )
    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(
        side=tk.RIGHT
    )

    dialog.grab_set()
    root.wait_window(dialog)

    return selection_result if selection_result else None


def compress_pdf_heavy(input_path: str, output_folder: str, options: dict):
    """Optimizes and compresses PDFs using PyMuPDF based on user configuration settings."""
    base_name = os.path.basename(input_path)
    file_stem, ext = os.path.splitext(base_name)
    output_filename = f"{file_stem}_comp{ext}"
    output_path = os.path.join(output_folder, output_filename)

    print(f"\nLoading '{input_path}'...")
    doc = pymupdf.open(input_path)

    # 1. Image Resampling / Downscaling
    if options.get("do_image"):
        quality = options.get("image_quality", 40)
        target_dpi = options.get("target_dpi", 72)
        print(f"Downsampling images (Target: {target_dpi} DPI, Quality: {quality}%)...")
        doc.rewrite_images(
            dpi_threshold=target_dpi + 10,
            dpi_target=target_dpi,
            quality=quality,
            lossy=True,
        )

    # 2. Save settings (Stream compression & garbage collection)
    garbage_level = 3 if options.get("do_dedup") else 0
    deflate_val = bool(options.get("do_stream"))
    objstms_val = bool(options.get("do_stream"))

    print("Scrubbing document and writing optimized file...")
    doc.save(
        output_path,
        garbage=garbage_level,
        deflate=deflate_val,
        use_objstms=objstms_val,
    )
    doc.close()

    print(f"\nDone! Compressed PDF saved to:\n{output_path}")


if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.withdraw()

        last_known_dir = load_last_dir()
        input_file = select_input_pdf(root, initial_dir=last_known_dir)

        if input_file:
            input_dir = os.path.dirname(input_file)
            options = prompt_compression_options(root)

            if options:
                default_dest_dir = last_known_dir if last_known_dir else input_dir
                dest_folder = select_destination_folder(root, initial_dir=default_dest_dir)

                if dest_folder:
                    save_last_dir(dest_folder)
                    compress_pdf_heavy(input_file, dest_folder, options)
                else:
                    print("No destination folder selected. Exiting.")
            else:
                print("Optimization cancelled.")
        else:
            print("No input file selected. Exiting.")

    except KeyboardInterrupt:
        print("\nProcess canceled by user. Exiting.")
    finally:
        try:
            root.destroy()
        except Exception:
            pass