"""
PDF ingestion module
Extracts text from PDFs with page-aware processing using pdfplumber
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import pdfplumber
from datetime import datetime
import uuid

from app.core.models import Document, Page

logger = logging.getLogger(__name__)


class PDFIngestionModule:
    """Handles PDF document ingestion and text extraction"""

    def __init__(self):
        """Initialize PDF ingestion module"""
        pass

    async def ingest_pdf(
        self,
        file_path: Path,
        filename: str,
        doc_type: Optional[str] = None,
        form_number: Optional[str] = None,
        effective_date: Optional[str] = None,
        state: Optional[str] = None
    ) -> Document:
        """
        Ingest a PDF file and extract structured content

        Args:
            file_path: Path to PDF file
            filename: Original filename
            doc_type: Document type (e.g., "policy", "endorsement")
            form_number: Insurance form number
            effective_date: Effective date
            state: State jurisdiction

        Returns:
            Document object with extracted pages
        """
        logger.info(f"Ingesting PDF: {filename}")

        try:
            # Generate document ID
            doc_id = str(uuid.uuid4())

            # Extract pages from PDF
            pages = await self._extract_pages(file_path)

            # Extract metadata from content if not provided
            if not form_number or not doc_type:
                extracted_meta = self._extract_metadata(pages)
                form_number = form_number or extracted_meta.get("form_number")
                doc_type = doc_type or extracted_meta.get("doc_type")
                state = state or extracted_meta.get("state")
                effective_date = effective_date or extracted_meta.get("effective_date")

            # Create Document object
            document = Document(
                doc_id=doc_id,
                filename=filename,
                doc_type=doc_type,
                form_number=form_number,
                effective_date=effective_date,
                state=state,
                pages=pages,
                metadata={
                    "total_pages": len(pages),
                    "total_chars": sum(page.char_count for page in pages),
                    "file_path": str(file_path)
                },
                created_at=datetime.now()
            )

            logger.info(f"PDF ingested successfully: {doc_id}, {len(pages)} pages")
            return document

        except Exception as e:
            logger.error(f"Error ingesting PDF {filename}: {e}")
            raise

    async def _extract_pages(self, file_path: Path) -> List[Page]:
        """
        Extract text from PDF pages

        Args:
            file_path: Path to PDF file

        Returns:
            List of Page objects
        """
        pages = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, pdf_page in enumerate(pdf.pages, start=1):
                    # Extract text from page
                    text = pdf_page.extract_text() or ""

                    # Clean up text
                    text = self._clean_text(text)

                    # Create Page object
                    page = Page(
                        page_no=page_num,
                        text=text,
                        char_count=len(text),
                        metadata={
                            "width": pdf_page.width,
                            "height": pdf_page.height,
                        }
                    )
                    pages.append(page)

            logger.info(f"Extracted {len(pages)} pages from PDF")
            return pages

        except Exception as e:
            logger.error(f"Error extracting pages: {e}")
            # Return empty list if extraction fails
            return []

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove leading/trailing whitespace
        text = text.strip()

        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    def _extract_metadata(self, pages: List[Page]) -> Dict[str, Any]:
        """
        Extract metadata from page content using pattern matching

        Args:
            pages: List of extracted pages

        Returns:
            Dictionary of extracted metadata
        """
        metadata = {}

        # Combine first few pages for metadata extraction
        combined_text = " ".join([page.text for page in pages[:3]])

        # Extract form number (common patterns)
        form_patterns = [
            r'Form\s+Number[:\s]+([A-Z0-9-]+)',
            r'Form[:\s]+([A-Z0-9-]+)',
            r'Policy\s+Form[:\s]+([A-Z0-9-]+)',
        ]
        for pattern in form_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                metadata["form_number"] = match.group(1).strip()
                break

        # Extract document type
        if re.search(r'\bpolicy\b', combined_text, re.IGNORECASE):
            metadata["doc_type"] = "policy"
        elif re.search(r'\bendorsement\b', combined_text, re.IGNORECASE):
            metadata["doc_type"] = "endorsement"
        elif re.search(r'\bexclusion\b', combined_text, re.IGNORECASE):
            metadata["doc_type"] = "exclusion"

        # Extract state (2-letter state codes)
        state_match = re.search(r'\b([A-Z]{2})\b', combined_text)
        if state_match:
            potential_state = state_match.group(1)
            # List of common US state codes
            valid_states = [
                'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
            ]
            if potential_state in valid_states:
                metadata["state"] = potential_state

        # Extract effective date (common date patterns)
        date_patterns = [
            r'Effective\s+Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'Effective[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                metadata["effective_date"] = match.group(1).strip()
                break

        return metadata

    async def validate_pdf(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate PDF file

        Args:
            file_path: Path to PDF file

        Returns:
            Validation results
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {}
        }

        # Check file exists
        if not file_path.exists():
            validation["valid"] = False
            validation["errors"].append("File does not exist")
            return validation

        # Check file size
        file_size = file_path.stat().st_size
        max_size = 50 * 1024 * 1024  # 50 MB
        if file_size > max_size:
            validation["valid"] = False
            validation["errors"].append(f"File too large: {file_size} bytes (max {max_size})")
            return validation

        validation["info"]["file_size"] = file_size

        # Try to open and validate PDF
        try:
            with pdfplumber.open(file_path) as pdf:
                num_pages = len(pdf.pages)
                validation["info"]["num_pages"] = num_pages

                if num_pages == 0:
                    validation["valid"] = False
                    validation["errors"].append("PDF has no pages")

                if num_pages > 500:
                    validation["warnings"].append(f"Large PDF with {num_pages} pages")

        except Exception as e:
            validation["valid"] = False
            validation["errors"].append(f"Failed to open PDF: {str(e)}")

        return validation
