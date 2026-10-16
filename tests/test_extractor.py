"""Unit tests for extractor module covering PDF, DOCX, TXT, and edge cases."""

import io
from pathlib import Path

import pytest
from src.extractor import (
    extract_resume_text,
    extract_text_from_docx,
    extract_text_from_pdf,
    extract_text_from_txt,
)

SAMPLE_DIR = Path(__file__).parent / "sample_data"


def test_extract_txt_file() -> None:
    txt_path = SAMPLE_DIR / "sample_resume.txt"
    assert txt_path.exists()
    text, error = extract_resume_text(txt_path)
    assert error is None
    assert "Jane Doe" in text
    assert "Software Engineer" in text
    assert "Python" in text


def test_extract_txt_stream() -> None:
    data = io.BytesIO(b"Candidate Name\nExperienced Python developer.")
    text, error = extract_text_from_txt(data)
    assert error is None
    assert "Candidate Name" in text
    assert "Python" in text


def test_extract_docx_file() -> None:
    docx_path = SAMPLE_DIR / "sample_resume.docx"
    assert docx_path.exists()
    text, error = extract_resume_text(docx_path)
    assert error is None
    assert "Jane Doe" in text
    assert "PostgreSQL" in text


def test_extract_pdf_file() -> None:
    pdf_path = SAMPLE_DIR / "sample_resume.pdf"
    assert pdf_path.exists()
    text, error = extract_resume_text(pdf_path)
    assert error is None
    assert "Jane Doe" in text
    assert "AWS" in text


def test_empty_file_handling() -> None:
    empty_stream = io.BytesIO(b"")
    text, error = extract_resume_text(empty_stream, explicit_extension=".txt")
    assert text == ""
    assert error is not None
    assert "Empty file" in error or "empty" in error.lower()


def test_corrupted_docx_handling() -> None:
    corrupt_stream = io.BytesIO(b"PK\x03\x04not a valid zip or docx content")
    text, error = extract_resume_text(corrupt_stream, explicit_extension=".docx")
    assert text == ""
    assert error is not None
    assert "Could not read DOCX" in error or "corrupted" in error.lower()


def test_corrupted_pdf_handling() -> None:
    corrupt_stream = io.BytesIO(b"%PDF-1.4 corrupt junk data")
    text, error = extract_resume_text(corrupt_stream, explicit_extension=".pdf")
    assert text == ""
    assert error is not None
    assert "Could not read PDF" in error or "damaged" in error.lower()


def test_unsupported_file_type() -> None:
    fake_stream = io.BytesIO(b"binary data")
    text, error = extract_resume_text(fake_stream, explicit_extension=".exe")
    assert text == ""
    assert error is not None
    assert "Unsupported file type" in error
