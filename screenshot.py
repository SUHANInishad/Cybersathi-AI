
"""
CyberSathi-AI - OCR Reader
Extracts text from uploaded screenshots and images.
Supports Hindi, English, and Roman-script Hinglish OCR.
Requires Tesseract OCR with eng and hin language data.
"""

import io
import os
import shutil

import pytesseract
from PIL import (
    Image,
    ImageOps,
    ImageFilter,
    ImageEnhance,
    UnidentifiedImageError,
)


# --------------------------------------------------
# TESSERACT CONFIGURATION
# --------------------------------------------------

WINDOWS_TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

if os.name == "nt" and not shutil.which("tesseract"):
    if os.path.isfile(WINDOWS_TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = (
            WINDOWS_TESSERACT_PATH
        )


DEFAULT_OCR_LANGUAGE = "eng+hin"


# --------------------------------------------------
# CUSTOM OCR ERROR
# --------------------------------------------------

class OCRReaderError(Exception):
    """Raised when OCR cannot process an image."""
    pass


# --------------------------------------------------
# CHECK OCR INSTALLATION
# --------------------------------------------------

def check_ocr_installation():
    """Return Tesseract status and available language data."""
    try:
        version = str(pytesseract.get_tesseract_version())
        languages = pytesseract.get_languages(config="")

        missing = [
            lang for lang in ("eng", "hin")
            if lang not in languages
        ]

        if missing:
            message = (
                "Tesseract is installed, but language data is missing: "
                + ", ".join(missing)
                + ". Hindi-English OCR requires both eng and hin."
            )
        else:
            message = (
                "Tesseract OCR is ready for Hindi and English. "
                "Roman-script Hinglish can be read using English OCR."
            )

        return {
            "available": True,
            "version": version,
            "languages": languages,
            "missing_languages": missing,
            "message": message,
        }

    except Exception as exc:
        return {
            "available": False,
            "version": None,
            "languages": [],
            "missing_languages": ["eng", "hin"],
            "message": (
                "Tesseract OCR could not be started. "
                "Check the installation and executable path. "
                f"Details: {exc}"
            ),
        }


# --------------------------------------------------
# VALIDATE OCR LANGUAGE
# --------------------------------------------------

def _validate_language(language):
    """Check that all requested Tesseract languages are installed."""
    if not isinstance(language, str) or not language.strip():
        raise OCRReaderError(
            "Invalid OCR language. Use 'eng', 'hin', or 'eng+hin'."
        )

    requested = [
        item.strip()
        for item in language.split("+")
        if item.strip()
    ]

    if not requested:
        raise OCRReaderError("No OCR language was specified.")

    try:
        available = pytesseract.get_languages(config="")
    except Exception as exc:
        raise OCRReaderError(
            "Could not access Tesseract OCR. "
            "Check that Tesseract is installed correctly."
        ) from exc

    missing = [
        lang for lang in requested
        if lang not in available
    ]

    if missing:
        raise OCRReaderError(
            "Required OCR language data is missing: "
            + ", ".join(missing)
            + ". For Hindi-English OCR, install eng and hin "
              "in the Tesseract tessdata folder."
        )

    return "+".join(requested)


# --------------------------------------------------
# PREPROCESS IMAGE
# --------------------------------------------------

def preprocess_image(image):
    """Improve screenshot readability before text extraction."""
    if not isinstance(image, Image.Image):
        raise OCRReaderError("Invalid image supplied for preprocessing.")

    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    image = ImageOps.grayscale(image)

    image = ImageEnhance.Contrast(image).enhance(1.8)
    image = image.filter(ImageFilter.SHARPEN)

    width, height = image.size
    largest_dimension = max(width, height)

    # Enlarge small images without excessively enlarging large images.
    if largest_dimension < 1600:
        scale = min(2.0, 1600 / largest_dimension)
        new_size = (
            max(1, int(width * scale)),
            max(1, int(height * scale)),
        )

        image = image.resize(
            new_size,
            Image.Resampling.LANCZOS,
        )

    return image


# --------------------------------------------------
# EXTRACT TEXT FROM PIL IMAGE
# --------------------------------------------------

def extract_text_from_image(
    image,
    language=DEFAULT_OCR_LANGUAGE,
    preprocess=True,
):
    """
    Extract Hindi, English, or mixed-script text from a PIL image.

    language='eng+hin': Hindi and English together.
    language='eng': English and Roman-script Hinglish.
    language='hin': Hindi in Devanagari script.
    """
    if not isinstance(image, Image.Image):
        raise OCRReaderError(
            "Invalid image input. Please provide a valid image."
        )

    if image.width <= 0 or image.height <= 0:
        raise OCRReaderError("The uploaded image is empty.")

    try:
        language = _validate_language(language)

        image = ImageOps.exif_transpose(image)

        if preprocess:
            image = preprocess_image(image)
        else:
            image = image.convert("RGB")

        extracted_text = pytesseract.image_to_string(
            image,
            lang=language,
            config="--oem 3 --psm 6",
            timeout=30,
        )

        lines = [
            line.strip()
            for line in extracted_text.splitlines()
            if line.strip()
        ]

        cleaned_text = "\n".join(lines)

        if not cleaned_text:
            raise OCRReaderError(
                "No readable text was found in this image. "
                "Try a clearer screenshot with larger, sharper text."
            )

        return cleaned_text

    except OCRReaderError:
        raise

    except pytesseract.TesseractNotFoundError as exc:
        raise OCRReaderError(
            "Tesseract OCR was not found. Check its installation path."
        ) from exc

    except RuntimeError as exc:
        raise OCRReaderError(
            "OCR timed out or could not process this image. "
            "Try a smaller or clearer screenshot."
        ) from exc

    except Exception as exc:
        raise OCRReaderError(
            f"Could not extract text from this image: {exc}"
        ) from exc


# --------------------------------------------------
# EXTRACT TEXT FROM FILE OR STREAMLIT UPLOAD
# --------------------------------------------------

def extract_text_from_file(
    file,
    language=DEFAULT_OCR_LANGUAGE,
    preprocess=True,
):
    """
    Supported inputs:
      - File path
      - Streamlit UploadedFile
      - Binary file-like object

    Supported image formats depend on the installed Pillow libraries.
    """
    if file is None:
        raise OCRReaderError("No image was provided.")

    try:
        if isinstance(file, (str, os.PathLike)):
            with Image.open(file) as opened_image:
                opened_image.load()
                image = opened_image.copy()

        elif hasattr(file, "getvalue"):
            file_bytes = file.getvalue()

            if not file_bytes:
                raise OCRReaderError("The uploaded file is empty.")

            with Image.open(io.BytesIO(file_bytes)) as opened_image:
                opened_image.load()
                image = opened_image.copy()

        elif hasattr(file, "read"):
            if hasattr(file, "seek"):
                file.seek(0)

            file_bytes = file.read()

            if not file_bytes:
                raise OCRReaderError("The uploaded file is empty.")

            with Image.open(io.BytesIO(file_bytes)) as opened_image:
                opened_image.load()
                image = opened_image.copy()

        else:
            raise OCRReaderError(
                "Unsupported input. Provide an image path "
                "or a supported uploaded image."
            )

        return extract_text_from_image(
            image,
            language=language,
            preprocess=preprocess,
        )

    except OCRReaderError:
        raise

    except UnidentifiedImageError as exc:
        raise OCRReaderError(
            "This file is not a valid supported image or is corrupted. "
            "Please upload a valid PNG, JPG, JPEG, or WEBP image."
        ) from exc

    except FileNotFoundError as exc:
        raise OCRReaderError(
            "The specified image file could not be found."
        ) from exc

    except Exception as exc:
        raise OCRReaderError(
            f"Unable to read the uploaded image: {exc}"
        ) from exc


# --------------------------------------------------
# MAIN FUNCTION FOR CYBERSATHI-AI
# --------------------------------------------------

def read_screenshot(file, language=DEFAULT_OCR_LANGUAGE):
    """
    Extract text from a screenshot uploaded to CyberSathi AI.

    Example:
        text = read_screenshot(uploaded_file)
    """
    return extract_text_from_file(
        file,
        language=language,
        preprocess=True,
    )


# --------------------------------------------------
# LOCAL TEST
# --------------------------------------------------

if __name__ == "__main__":
    status = check_ocr_installation()

    print("\nCyberSathi-AI OCR Status")
    print("------------------------")
    print("Available:", status["available"])
    print("Version:", status["version"])
    print("Languages:", status["languages"])
    print("Missing:", status["missing_languages"])
    print("Message:", status["message"])

    if status["available"] and not status["missing_languages"]:
        print("\nHindi-English OCR is ready to test.")

        image_path = input(
            "Optional: Enter an image path to test, "
            "or press Enter to skip: "
        ).strip()

        if image_path:
            try:
                result = read_screenshot(image_path)
                print("\nExtracted text:")
                print("----------------")
                print(result)
            except OCRReaderError as exc:
                print("\nOCR Error:", exc)
    else:
        print("\nPlease fix the missing OCR installation first.")
