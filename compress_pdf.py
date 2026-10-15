import gc
import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pymupdf

CONFIG_FILE = "app_config.json"


def load_config() -> dict:
    """Loads saved directory settings from a local config file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(config_data: dict):
    """Saves directory settings to a local config file."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f)
    except Exception as e:
        print(f"Failed to save config: {e}")


def select_input_folder(root: tk.Tk, initial_dir: str = "") -> str:
    """Opens a folder dialog to select a folder containing PDFs to scan."""
    return filedialog.askdirectory(
        parent=root,
        title="Select Input Folder Containing PDFs to Scan",
        initialdir=initial_dir,
    )


def select_destination_folder(root: tk.Tk, initial_dir: str = "") -> str:
    """Opens a folder dialog to select where compressed files will be saved."""
    return filedialog.askdirectory(
        parent=root,
        title="Select Destination Folder for Compressed PDFs",
        initialdir=initial_dir,
    )


def show_info(title: str, message: str, parent_window=None):
    """Displays a pop-up information box safely."""
    if parent_window:
        parent_window.deiconify()  # Ensure window is visible if parented
    messagebox.showinfo(title, message, parent=parent_window)
    if parent_window:
        parent_window.withdraw()   # Hide it again if needed


def prompt_compression_options(root: tk.Tk) -> dict | None:
    """Displays a GUI dialog allowing the user to configure batch scan and compression options."""
    dialog = tk.Toplevel(root)
    dialog.title("PDF Batch Optimization Settings")
    dialog.geometry("450x480")
    dialog.resizable(False, False)
    dialog.attributes("-topmost", True)

    # Center window on screen reliably
    dialog.update_idletasks()
    width = 450
    height = 480
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f"{width}x{height}+{x}+{y}")

    var_stream = tk.BooleanVar(value=True)
    var_dedup = tk.BooleanVar(value=True)
    var_image = tk.BooleanVar(value=True)
    var_quality = tk.IntVar(value=40)
    var_dpi = tk.IntVar(value=72)
    var_threshold = tk.DoubleVar(value=10.0)  # File size threshold in MB

    selection_result = {}

    frame = ttk.Frame(dialog, padding="15")
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
        frame, text="Configure Batch Scan & Compression Options:", font=("Helvetica", 10, "bold")
    ).pack(anchor="w", pady=(0, 10))

    # File Size Threshold Slider
    threshold_frame = ttk.Frame(frame)
    threshold_frame.pack(fill=tk.X, pady=(0, 10))
    lbl_threshold = ttk.Label(
        threshold_frame, text=f"Minimum File Size Threshold ({var_threshold.get():.1f} MB):"
    )
    lbl_threshold.pack(anchor="w")

    def update_threshold_label(val):
        lbl_threshold.config(
            text=f"Minimum File Size Threshold ({float(val):.1f} MB):"
        )

    slider_threshold = ttk.Scale(
        threshold_frame,
        from_=1.0,
        to=100.0,
        variable=var_threshold,
        command=update_threshold_label,
    )
    slider_threshold.pack(fill=tk.X, pady=2)

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

        selection_result["threshold_mb"] = var_threshold.get()
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
    btn_frame.pack(fill=tk.X, pady=(15, 0))
    ttk.Button(btn_frame, text="Start Batch Scan", command=on_confirm).pack(
        side=tk.RIGHT, padx=(5, 0)
    )
    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(
        side=tk.RIGHT
    )

    dialog.grab_set()
    root.wait_window(dialog)

    return selection_result if selection_result else None


def compress_pdf_batch(root: tk.Tk, input_folder: str, output_folder: str, options: dict):
    """Scans an input folder for PDFs exceeding the size threshold and compresses them."""
    threshold_mb = options.get("threshold_mb", 10.0)
    threshold_bytes = threshold_mb * 1024 * 1024

   # Gather PDFs, but automatically ignore files that are already compressed outputs
    pdf_files = [
        f for f in os.listdir(input_folder) 
        if f.lower().endswith(".pdf") and not f.lower().endswith("_comp.pdf")
    ]
    
    if not pdf_files:
        print(f"\nNo PDF files found in '{input_folder}'.")
        show_info("Batch Scan Result", f"No PDF files found in:\n{input_folder}", root)
        return

    print(f"\nScanning '{input_folder}' for PDFs larger than {threshold_mb:.1f} MB...")

    processed_count = 0
    skipped_count = 0
    total_original_bytes = 0
    total_compressed_bytes = 0

    for filename in pdf_files:
        input_path = os.path.join(input_folder, filename)
        file_size = os.path.getsize(input_path)

        if file_size >= threshold_bytes:
            print(f"\n[Processing] '{filename}' ({file_size / (1024*1024):.2f} MB)")
            file_stem, ext = os.path.splitext(filename)
            output_filename = f"{file_stem}_comp{ext}"
            output_path = os.path.join(output_folder, output_filename)

            try:
                doc = pymupdf.open(input_path)

                # 1. Image Resampling / Downscaling
                if options.get("do_image"):
                    quality = options.get("image_quality", 40)
                    target_dpi = options.get("target_dpi", 72)
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

                doc.save(
                    output_path,
                    garbage=garbage_level,
                    deflate=deflate_val,
                    use_objstms=objstms_val,
                )
                doc.close()
                gc.collect() # Force immediate memory reclamation for large PDFs
                
                # Calculate space metrics for summary
                compressed_size = os.path.getsize(output_path)
                total_original_bytes += file_size
                total_compressed_bytes += compressed_size

                print(f" -> Saved to: {output_path} ({compressed_size / (1024*1024):.2f} MB)")
                processed_count += 1
            except Exception as e:
                print(f" -> Error processing '{filename}': {e}")
        else:
            print(f"[Skipped] '{filename}' ({file_size / (1024*1024):.2f} MB is below {threshold_mb:.1f} MB threshold)")
            skipped_count += 1

    # Calculate final batch savings
    saved_bytes = total_original_bytes - total_compressed_bytes
    saved_mb = saved_bytes / (1024 * 1024)
    orig_mb = total_original_bytes / (1024 * 1024)
    comp_mb = total_compressed_bytes / (1024 * 1024)
    percent_saved = (saved_bytes / total_original_bytes * 100) if total_original_bytes > 0 else 0

    summary_msg = (
        f"Batch Compression Complete!\n\n"
        f"• Files Processed: {processed_count}\n"
        f"• Files Skipped: {skipped_count}\n"
        f"• Original Size: {orig_mb:.2f} MB\n"
        f"• Compressed Size: {comp_mb:.2f} MB\n"
        f"• Total Space Saved: {saved_mb:.2f} MB ({percent_saved:.1f}%)"
    )

    print(f"\n{summary_msg}")
    show_info("Batch Summary", summary_msg, root)


if __name__ == "__main__":
    root = None
    try:
        root = tk.Tk()
        root.withdraw()

        config = load_config()
        last_input_dir = config.get("last_input_dir", "")

        # 1. Select input folder to scan
        input_folder = select_input_folder(root, initial_dir=last_input_dir)

        if input_folder:
            # 2. Prompt options & threshold slider
            options = prompt_compression_options(root)

            if options:
                last_dest_dir = config.get("last_destination", input_folder)
                # 3. Select destination folder for compressed output
                dest_folder = select_destination_folder(root, initial_dir=last_dest_dir)

                if dest_folder:
                    # Save directories to config for next run
                    save_config({
                        "last_input_dir": input_folder,
                        "last_destination": dest_folder
                    })
                    # 4. Run batch processor with summary dialog
                    compress_pdf_batch(root, input_folder, dest_folder, options)
                else:
                    print("No destination folder selected. Exiting.")
            else:
                print("Batch optimization cancelled.")
        else:
            print("No input folder selected. Exiting.")

    except KeyboardInterrupt:
        print("\nProcess canceled by user. Exiting.")
    finally:
        if root:
            try:
                root.destroy()
            except Exception:
                pass