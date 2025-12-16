import logging
from django.core.management.base import BaseCommand
from ally.services import PDFExtractor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Extract content from a PDF file including text and tables'

    def add_arguments(self, parser):
        parser.add_argument(
            'pdf_path',
            type=str,
            help='Path to the PDF file to extract'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Optional output file path to save the extracted content'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['full', 'text', 'markdown'],
            default='markdown',
            help='Output format: full (JSON), text (text only), markdown (text + markdown tables)'
        )

    def handle(self, *args, **options):
        pdf_path = options['pdf_path']
        output_file = options['output']
        format_type = options['format']

        logger.info(f'Extracting content from PDF: {pdf_path}')
        self.stdout.write(self.style.SUCCESS(f'Extracting content from: {pdf_path}'))

        try:
            if format_type == 'text':
                # Extract text only
                content = PDFExtractor.extract_text_only(pdf_path)
                output = content

            elif format_type == 'markdown':
                # Extract text and tables with markdown formatting
                content = PDFExtractor.extract_with_markdown_tables(pdf_path)
                output = content

            else:  # full
                # Extract everything including metadata
                import json
                result = PDFExtractor.extract_from_file(pdf_path)

                # Format for display
                output = f"PDF Extraction Results\n"
                output += f"{'='*80}\n\n"
                output += f"Metadata:\n"
                for key, value in result['metadata'].items():
                    if value:
                        output += f"  {key}: {value}\n"
                output += f"\nNumber of Pages: {result['num_pages']}\n"
                output += f"\n{'='*80}\n\n"

                # Add page content
                for page in result['pages']:
                    output += f"\nPage {page['page_number']}\n"
                    output += f"{'-'*80}\n"
                    output += page['text']
                    output += "\n"

                    if page['tables']:
                        output += f"\nTables found: {len(page['tables'])}\n"
                        for table in page['tables']:
                            output += f"\nTable {table['table_index'] + 1}:\n"
                            output += table['markdown']
                            output += "\n"

            # Output results
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output)
                self.stdout.write(
                    self.style.SUCCESS(f'Content saved to {output_file}')
                )
                logger.info(f'Content saved to {output_file}')
            else:
                self.stdout.write('\n' + '='*80)
                self.stdout.write('EXTRACTED CONTENT')
                self.stdout.write('='*80 + '\n')
                self.stdout.write(output)
                self.stdout.write('\n' + '='*80 + '\n')

            self.stdout.write(self.style.SUCCESS('Extraction completed successfully'))

        except FileNotFoundError as e:
            self.stderr.write(self.style.ERROR(str(e)))
            return

        except Exception as e:
            logger.error(f'Error extracting PDF: {str(e)}', exc_info=True)
            self.stderr.write(
                self.style.ERROR(f'Error extracting PDF: {str(e)}')
            )
            raise
