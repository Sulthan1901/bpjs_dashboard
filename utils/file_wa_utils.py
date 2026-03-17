import re
import os
import mimetypes


def format_wa_number(no_hp: str) -> str:
    """Convert Indonesian phone number to WhatsApp format (62xxx)."""
    if not no_hp:
        return ""
    # Remove spaces, dashes, dots, parentheses
    clean = re.sub(r"[\s\-\.\(\)]", "", str(no_hp))
    # Remove non-numeric except leading +
    clean = re.sub(r"[^\d+]", "", clean)
    # Convert to international format
    if clean.startswith("+62"):
        clean = clean[1:]  # remove +
    elif clean.startswith("62"):
        pass  # already correct
    elif clean.startswith("0"):
        clean = "62" + clean[1:]
    elif clean.startswith("8"):
        clean = "62" + clean
    return clean


def make_wa_link(no_hp: str, pesan: str = "") -> str:
    """Generate WhatsApp chat link."""
    number = format_wa_number(no_hp)
    if not number:
        return ""
    if pesan:
        import urllib.parse
        encoded = urllib.parse.quote(pesan)
        return f"https://wa.me/{number}?text={encoded}"
    return f"https://wa.me/{number}"


def get_file_icon(filename: str) -> str:
    """Return emoji icon based on file extension."""
    if not filename:
        return "📎"
    ext = os.path.splitext(filename)[1].lower()
    icons = {
        ".pdf": "📄",
        ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️",
        ".xlsx": "📊", ".xls": "📊",
        ".docx": "📝", ".doc": "📝",
        ".zip": "🗜️",
        ".csv": "📋",
    }
    return icons.get(ext, "📎")


def get_mime_type(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def is_image(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]


def is_pdf(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() == ".pdf"
