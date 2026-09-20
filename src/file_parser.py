import base64
import os
import io
import re
import zipfile
import xml.etree.ElementTree as ET

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


def format_bytes(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def parse_uploaded_file(filename: str, base64_data: str = None, raw_text: str = None) -> dict:
    """
    Parses an uploaded file from base64 data or raw text.
    Extracts structured text from PDF, DOCX, Code, CSV, Markdown, JSON, Text, etc.
    """
    filename = filename or "uploaded_document.txt"
    ext = os.path.splitext(filename)[1].lower()

    file_bytes = b""
    if base64_data:
        # Handle data URL prefix if present e.g. "data:application/pdf;base64,..."
        if "," in base64_data:
            base64_data = base64_data.split(",", 1)[1]
        try:
            file_bytes = base64.b64decode(base64_data)
        except Exception:
            file_bytes = b""
    elif raw_text is not None:
        file_bytes = raw_text.encode("utf-8")

    size_bytes = len(file_bytes)
    formatted_size = format_bytes(size_bytes)
    extracted_text = ""
    page_count = None

    # 1. PDF Parsing with PyMuPDF
    if ext == ".pdf":
        if HAS_FITZ and file_bytes:
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                page_count = len(doc)
                pages_text = []
                for i in range(page_count):
                    page = doc[i]
                    p_text = page.get_text("text").strip()
                    if p_text:
                        pages_text.append(f"--- Page {i + 1} ---\n{p_text}")
                extracted_text = "\n\n".join(pages_text)
                doc.close()
            except Exception as e:
                extracted_text = f"[Error parsing PDF stream: {e}]"
        else:
            extracted_text = "[PDF file attached. PDF parser unavailable in this environment.]"

    # 2. DOCX Parsing with zipfile + XML
    elif ext in [".docx", ".doc"]:
        if file_bytes:
            try:
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                    xml_content = z.read("word/document.xml")
                    tree = ET.fromstring(xml_content)
                    # Extract text elements
                    paragraphs = []
                    for p in tree.iter():
                        if p.tag.endswith("p"):
                            texts = [elem.text for elem in p.iter() if elem.text]
                            if texts:
                                paragraphs.append("".join(texts))
                    extracted_text = "\n".join(paragraphs).strip()
            except Exception as e:
                extracted_text = f"[Error parsing Word Document: {e}]"

    # 3. Text / Code / CSV / JSON / Markdown / Config / Scripts / etc.
    else:
        if raw_text is not None and not extracted_text:
            extracted_text = raw_text
        elif file_bytes:
            # Try standard UTF-8, then fallback to latin-1
            try:
                extracted_text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    extracted_text = file_bytes.decode("latin-1")
                except Exception:
                    extracted_text = f"[{filename} attached ({formatted_size}) - Binary file]"

    # Fallback if empty
    if not extracted_text and size_bytes > 0:
        extracted_text = f"[{filename} ({formatted_size}) - File loaded with empty text]"

    # Calculate word and line counts
    lines = extracted_text.splitlines()
    words = re.findall(r'\b\w+\b', extracted_text)
    word_count = len(words)
    line_count = len(lines)

    # Truncate if document exceeds context budget (e.g. 60,000 characters ~ 12,000 words)
    MAX_CHARS = 60000
    truncated = False
    if len(extracted_text) > MAX_CHARS:
        extracted_text = (
            extracted_text[:MAX_CHARS] +
            f"\n\n[... Document truncated to first {MAX_CHARS} characters for optimal AI reasoning. Total size: {formatted_size}]"
        )
        truncated = True

    # Determine display badge type
    badge_type = "FILE"
    if ext in [".pdf"]:
        badge_type = "PDF"
    elif ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".cpp", ".c", ".java", ".rs", ".go", ".php", ".rb", ".swift", ".sql", ".sh"]:
        badge_type = "CODE"
    elif ext in [".csv", ".json", ".xml", ".yaml", ".yml", ".xlsx"]:
        badge_type = "DATA"
    elif ext in [".md", ".txt", ".docx", ".doc", ".rtf"]:
        badge_type = "DOC"
    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"]:
        badge_type = "IMG"

    return {
        "success": True,
        "filename": filename,
        "extension": ext,
        "badge_type": badge_type,
        "size_bytes": size_bytes,
        "formatted_size": formatted_size,
        "word_count": word_count,
        "line_count": line_count,
        "page_count": page_count,
        "truncated": truncated,
        "text": extracted_text,
        "preview": extracted_text[:180].replace("\n", " ") if extracted_text else ""
    }
