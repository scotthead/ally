import logging
import asyncio

from django.core.management.base import BaseCommand

from ally.product_service import product_service
from ally.services import AgentService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate a competitor report for a product using the competitor report agent'

    def add_arguments(self, parser):
        parser.add_argument(
            'product_id',
            type=str,
            help='The product ID (ASIN) to generate a competitor report for'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Optional output file path to save the report (default: print to stdout)'
        )
        parser.add_argument(
            '--user-id',
            type=str,
            default='default_user',
            help='User ID for the session (default: default_user)'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Timeout in seconds (default: 300 / 5 minutes)'
        )

    def handle(self, *args, **options):
        product_id = options['product_id']
        output_file = options['output']
        user_id = options['user_id']
        timeout = options['timeout']

        logger.info(f'Generating competitor report for product: {product_id}')
        self.stdout.write(self.style.SUCCESS(
            f'Generating competitor report for product: {product_id}'
        ))

        # Verify the product exists
        product = product_service.get_product_by_id(product_id)
        if not product:
            self.stderr.write(
                self.style.ERROR(f'Product {product_id} not found in product service')
            )
            return

        self.stdout.write(f'Found product: {product.title}')
        self.stdout.write('Running competitor report agent...')

        # Run the agent using AgentService
        try:
            report = asyncio.run(
                AgentService.run_competitor_report(
                    product_id=product_id,
                    user_id=user_id,
                    timeout_seconds=timeout
                )
            )

            # Output the report
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                self.stdout.write(
                    self.style.SUCCESS(f'Report saved to {output_file}')
                )
                logger.info(f'Report saved to {output_file}')
            else:
                self.stdout.write('\n' + '='*80)
                self.stdout.write('COMPETITOR REPORT')
                self.stdout.write('='*80 + '\n')
                self.stdout.write(report)
                self.stdout.write('\n' + '='*80 + '\n')

            logger.info('Competitor report generated successfully')
            self.stdout.write(self.style.SUCCESS('Report generated successfully'))

        except Exception as e:
            logger.error(f'Error generating competitor report: {str(e)}', exc_info=True)
            self.stderr.write(
                self.style.ERROR(f'Error generating report: {str(e)}')
            )
            raise
