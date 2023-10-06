"""Utility function usable throughout the application"""
import re
import unicodedata


def safe_file_name(filename: str) -> str:
    """Transforms strings for safe use as filenames

    Remove non-alphanumeric characters and converts spaces to underscore.
    """
    filename_out = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode("utf-8")
    filename_out = re.sub(r"[^\w\s\#\.\\\/-]", "", filename_out).strip()
    filename_out = re.sub(r"[-\s]+", "_", filename_out)
    return filename_out
