import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Service for extracting text and tables from PDF files."""

    @staticmethod
    def extract_from_file(pdf_path: str) -> Dict[str, Any]:
        """
        Extract all content from a PDF file including text and tables.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing:
                - text: Full text content of the PDF
                - pages: List of page contents with text and tables
                - metadata: PDF metadata (title, author, etc.)

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not pdf_file.suffix.lower() == '.pdf':
            raise ValueError(f"File must be a PDF: {pdf_path}")

        logger.info(f"Extracting content from PDF: {pdf_path}")

        try:
            # Open the PDF
            doc = fitz.open(pdf_path)

            # Extract metadata
            metadata = PDFExtractor._extract_metadata(doc)

            # Extract content from all pages
            pages = []
            all_text = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_content = PDFExtractor._extract_page_content(page, page_num + 1)
                pages.append(page_content)
                all_text.append(page_content['text'])

            doc.close()

            result = {
                'text': '\n\n'.join(all_text),
                'pages': pages,
                'metadata': metadata,
                'num_pages': len(pages)
            }

            logger.info(f"Successfully extracted content from {len(pages)} pages")
            return result

        except Exception as e:
            logger.error(f"Error extracting PDF content: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to extract PDF content: {str(e)}")

    @staticmethod
    def _extract_metadata(doc: fitz.Document) -> Dict[str, Any]:
        """
        Extract metadata from the PDF document.

        Args:
            doc: PyMuPDF document object

        Returns:
            Dictionary containing metadata
        """
        metadata = doc.metadata or {}
        return {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'subject': metadata.get('subject', ''),
            'keywords': metadata.get('keywords', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'creation_date': metadata.get('creationDate', ''),
            'modification_date': metadata.get('modDate', ''),
        }

    @staticmethod
    def _extract_page_content(page: fitz.Page, page_num: int) -> Dict[str, Any]:
        """
        Extract content from a single PDF page including text and tables.

        Args:
            page: PyMuPDF page object
            page_num: Page number (1-indexed)

        Returns:
            Dictionary containing page content
        """
        # Extract text with layout preservation
        text = page.get_text("text")

        # Try to extract tables
        tables = PDFExtractor._extract_tables(page)

        # Get page dimensions
        rect = page.rect
        page_info = {
            'width': rect.width,
            'height': rect.height
        }

        return {
            'page_number': page_num,
            'text': text,
            'tables': tables,
            'page_info': page_info
        }

    @staticmethod
    def _extract_tables(page: fitz.Page) -> List[Dict[str, Any]]:
        """
        Extract tables from a PDF page and format them as markdown.

        Args:
            page: PyMuPDF page object

        Returns:
            List of dictionaries containing table data and markdown representation
        """
        tables = []

        try:
            # Find tables in the page using PyMuPDF's table detection
            tabs = page.find_tables()

            if not tabs:
                return tables

            for table_index, tab in enumerate(tabs):
                # Extract table data
                table_data = tab.extract()

                if not table_data or len(table_data) == 0:
                    continue

                # Convert table to markdown
                markdown = PDFExtractor._table_to_markdown(table_data)

                tables.append({
                    'table_index': table_index,
                    'rows': len(table_data),
                    'cols': len(table_data[0]) if table_data else 0,
                    'data': table_data,
                    'markdown': markdown,
                    'bbox': tab.bbox  # Bounding box coordinates
                })

        except Exception as e:
            logger.warning(f"Error extracting tables: {str(e)}")

        return tables

    @staticmethod
    def _table_to_markdown(table_data: List[List[str]]) -> str:
        """
        Convert a table (2D list) to markdown format.

        Args:
            table_data: 2D list representing table rows and columns

        Returns:
            Markdown formatted table string
        """
        if not table_data or len(table_data) == 0:
            return ""

        # Clean up cell data
        cleaned_data = []
        for row in table_data:
            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
            cleaned_data.append(cleaned_row)

        # Determine column widths for alignment
        num_cols = len(cleaned_data[0]) if cleaned_data else 0
        col_widths = [0] * num_cols

        for row in cleaned_data:
            for i, cell in enumerate(row):
                if i < num_cols:
                    col_widths[i] = max(col_widths[i], len(cell))

        # Build markdown table
        markdown_lines = []

        # Header row (first row)
        if cleaned_data:
            header = cleaned_data[0]
            header_line = "| " + " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(header)) + " |"
            markdown_lines.append(header_line)

            # Separator line
            separator = "| " + " | ".join("-" * col_widths[i] for i in range(num_cols)) + " |"
            markdown_lines.append(separator)

            # Data rows
            for row in cleaned_data[1:]:
                row_line = "| " + " | ".join(
                    cell.ljust(col_widths[i]) if i < len(row) else " " * col_widths[i]
                    for i, cell in enumerate(row)
                ) + " |"
                markdown_lines.append(row_line)

        return "\n".join(markdown_lines)

    @staticmethod
    def extract_text_only(pdf_path: str) -> str:
        """
        Extract only text content from a PDF file (no tables).

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Full text content as a string

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        result = PDFExtractor.extract_from_file(pdf_path)
        return result['text']

    @staticmethod
    def extract_with_markdown_tables(pdf_path: str) -> str:
        """
        Extract text and tables, with tables formatted as markdown.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Full content with markdown-formatted tables

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        result = PDFExtractor.extract_from_file(pdf_path)

        content_parts = []

        for page in result['pages']:
            # Add page text
            if page['text']:
                content_parts.append(f"## Page {page['page_number']}\n")
                content_parts.append(page['text'])

            # Add tables in markdown format
            if page['tables']:
                for table in page['tables']:
                    content_parts.append(f"\n### Table {table['table_index'] + 1} on Page {page['page_number']}\n")
                    content_parts.append(table['markdown'])
                    content_parts.append("\n")

        return "\n".join(content_parts)
