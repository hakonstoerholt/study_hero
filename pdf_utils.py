"""Extract text from an uploaded PDF. Works with either pypdf or PyPDF2."""

try:
    from pypdf import PdfReader
except ImportError:                       # older installs
    from PyPDF2 import PdfReader


def extract_text(file_stream):
    reader = PdfReader(file_stream)
    parts = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(parts).strip()
