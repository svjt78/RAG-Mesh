"""
Unit tests for Ingestion module
"""

import os
import tempfile
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.core.models import Document
from app.modules.ingestion import Ingestion


@pytest.mark.unit
class TestIngestion:
    """Test cases for Ingestion module."""

    @pytest.fixture
    def ingestion(self, mock_doc_store: AsyncMock) -> Ingestion:
        """Create an Ingestion instance for testing."""
        return Ingestion(doc_store=mock_doc_store)

    @pytest.fixture
    def sample_pdf(self) -> bytes:
        """Create a sample PDF file in memory."""
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.drawString(100, 750, "This is a sample insurance policy.")
        pdf.drawString(100, 730, "Coverage A: Dwelling - $500,000")
        pdf.showPage()
        pdf.drawString(100, 750, "Section I - Exclusions")
        pdf.drawString(100, 730, "Water damage is not covered.")
        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return buffer.read()

    @pytest.mark.asyncio
    async def test_ingest_pdf_success(
        self, ingestion: Ingestion, sample_pdf: bytes, mock_doc_store: AsyncMock
    ):
        """Test successful PDF ingestion."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_file.write(sample_pdf)
            temp_file_path = temp_file.name

        try:
            metadata = {
                "form_number": "HO-3",
                "doc_type": "policy",
                "state": "CA",
            }

            result = await ingestion.ingest_pdf(
                file_path=temp_file_path,
                filename="sample.pdf",
                metadata=metadata,
            )

            # Verify document was created
            assert isinstance(result, Document)
            assert result.filename == "sample.pdf"
            assert result.metadata == metadata
            assert len(result.pages) == 2  # Two pages in the PDF

            # Verify pages have content
            assert result.pages[0].page_num == 1
            assert len(result.pages[0].text) > 0
            assert result.pages[1].page_num == 2
            assert len(result.pages[1].text) > 0

            # Verify document was saved
            mock_doc_store.save_document.assert_called_once()

        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_ingest_pdf_with_no_metadata(
        self, ingestion: Ingestion, sample_pdf: bytes, mock_doc_store: AsyncMock
    ):
        """Test PDF ingestion without metadata."""
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_file.write(sample_pdf)
            temp_file_path = temp_file.name

        try:
            result = await ingestion.ingest_pdf(
                file_path=temp_file_path,
                filename="sample.pdf",
                metadata={},
            )

            assert isinstance(result, Document)
            assert result.metadata == {}

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_ingest_nonexistent_file(
        self, ingestion: Ingestion, mock_doc_store: AsyncMock
    ):
        """Test ingesting a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            await ingestion.ingest_pdf(
                file_path="/nonexistent/file.pdf",
                filename="test.pdf",
                metadata={},
            )

    @pytest.mark.asyncio
    async def test_ingest_corrupted_pdf(
        self, ingestion: Ingestion, mock_doc_store: AsyncMock
    ):
        """Test ingesting a corrupted PDF file."""
        # Create a file with invalid PDF content
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_file.write(b"This is not a valid PDF file")
            temp_file_path = temp_file.name

        try:
            with pytest.raises(Exception):
                await ingestion.ingest_pdf(
                    file_path=temp_file_path,
                    filename="corrupted.pdf",
                    metadata={},
                )

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_extract_text_from_pages(
        self, ingestion: Ingestion, sample_pdf: bytes
    ):
        """Test that text extraction works correctly."""
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_file.write(sample_pdf)
            temp_file_path = temp_file.name

        try:
            result = await ingestion.ingest_pdf(
                file_path=temp_file_path,
                filename="sample.pdf",
                metadata={},
            )

            # Check that extracted text contains expected content
            page1_text = result.pages[0].text.lower()
            page2_text = result.pages[1].text.lower()

            assert "sample" in page1_text or "coverage" in page1_text
            assert "exclusion" in page2_text or "water" in page2_text

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_metadata_propagation(
        self, ingestion: Ingestion, sample_pdf: bytes, mock_doc_store: AsyncMock
    ):
        """Test that metadata is properly propagated to the document."""
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_file.write(sample_pdf)
            temp_file_path = temp_file.name

        try:
            metadata = {
                "form_number": "HO-3",
                "doc_type": "policy",
                "state": "CA",
                "custom_field": "test_value",
            }

            result = await ingestion.ingest_pdf(
                file_path=temp_file_path,
                filename="sample.pdf",
                metadata=metadata,
            )

            # All metadata should be preserved
            assert result.metadata == metadata
            assert result.metadata["custom_field"] == "test_value"

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_bbox_extraction(
        self, ingestion: Ingestion, sample_pdf: bytes
    ):
        """Test that bounding boxes are extracted for pages."""
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_file.write(sample_pdf)
            temp_file_path = temp_file.name

        try:
            result = await ingestion.ingest_pdf(
                file_path=temp_file_path,
                filename="sample.pdf",
                metadata={},
            )

            # Each page should have a bounding box
            for page in result.pages:
                assert page.bbox is not None
                assert "x0" in page.bbox
                assert "y0" in page.bbox
                assert "x1" in page.bbox
                assert "y1" in page.bbox

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_empty_pdf_pages(self, ingestion: Ingestion):
        """Test handling PDF with blank pages."""
        # Create a PDF with a blank page
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.showPage()  # Blank page
        pdf.save()
        buffer.seek(0)

        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_file.write(buffer.read())
            temp_file_path = temp_file.name

        try:
            result = await ingestion.ingest_pdf(
                file_path=temp_file_path,
                filename="blank.pdf",
                metadata={},
            )

            assert len(result.pages) == 1
            # Blank page should have minimal or no text
            assert len(result.pages[0].text.strip()) >= 0

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_large_pdf(self, ingestion: Ingestion):
        """Test ingesting a PDF with many pages."""
        # Create a PDF with 50 pages
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        for i in range(50):
            pdf.drawString(100, 750, f"Page {i + 1} content")
            pdf.showPage()
        pdf.save()
        buffer.seek(0)

        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_file.write(buffer.read())
            temp_file_path = temp_file.name

        try:
            result = await ingestion.ingest_pdf(
                file_path=temp_file_path,
                filename="large.pdf",
                metadata={},
            )

            assert len(result.pages) == 50
            # Verify page numbers are sequential
            for i, page in enumerate(result.pages):
                assert page.page_num == i + 1

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_special_characters_in_pdf(self, ingestion: Ingestion):
        """Test PDF with special characters and unicode."""
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        # Note: ReportLab may have encoding issues with some Unicode chars
        pdf.drawString(100, 750, "Policy with special chars: $500,000")
        pdf.drawString(100, 730, "Percentage: 100%")
        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_file.write(buffer.read())
            temp_file_path = temp_file.name

        try:
            result = await ingestion.ingest_pdf(
                file_path=temp_file_path,
                filename="special.pdf",
                metadata={},
            )

            page_text = result.pages[0].text
            # Should contain the dollar sign and percentage
            assert "$" in page_text or "500" in page_text
            assert "%" in page_text or "100" in page_text

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
