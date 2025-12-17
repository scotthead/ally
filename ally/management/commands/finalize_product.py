import logging
import asyncio
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from ally.product_service import product_service
from ally.services.agent_service import AgentService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Finalize product updates by applying recommendations and creating a summary'

    def add_arguments(self, parser):
        parser.add_argument(
            'product_id',
            type=str,
            help='The product ID (ASIN) to finalize'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Optional output file path to save the summary (default: print to stdout)'
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
            default=600,
            help='Timeout in seconds (default: 600 / 10 minutes)'
        )

    def handle(self, *args, **options):
        product_id = options['product_id']
        output_file = options['output']
        user_id = options['user_id']
        timeout = options['timeout']

        logger.info(f'Finalizing product: {product_id}')
        self.stdout.write(self.style.SUCCESS(
            f'Finalizing product updates for: {product_id}'
        ))

        # Verify the product exists
        product = product_service.get_product_by_id(product_id)
        if not product:
            self.stderr.write(
                self.style.ERROR(f'Product {product_id} not found in product service')
            )
            return

        self.stdout.write(f'Found product: {product.title}')
        self.stdout.write('Running final agent workflow...')
        self.stdout.write('This will:')
        self.stdout.write('  1. Apply recommendation #1')
        self.stdout.write('  2. Apply recommendation #2')
        self.stdout.write('  3. Apply recommendation #3')
        self.stdout.write('  4. Create comprehensive summary')

        # Run the final agent using AgentService
        try:
            summary = asyncio.run(
                AgentService.run_final_agent(
                    product_id=product_id,
                    user_id=user_id,
                    timeout_seconds=timeout
                )
            )

            # Output the summary
            if not output_file:
                output_file = os.path.join(settings.BASE_DIR, 'summarization', f'summarization_{product_id}.md')
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            self.stdout.write(
                self.style.SUCCESS(f'Summary saved to {output_file}')
            )
            logger.info(f'Summary saved to {output_file}')

            self.stdout.write('\n' + '='*80)
            self.stdout.write('FINALIZATION SUMMARY')
            self.stdout.write('='*80 + '\n')
            self.stdout.write(summary)
            self.stdout.write('\n' + '='*80 + '\n')

            logger.info('Product finalization completed successfully')
            self.stdout.write(self.style.SUCCESS('Product finalization completed successfully'))

        except Exception as e:
            logger.error(f'Error finalizing product: {str(e)}', exc_info=True)
            self.stderr.write(
                self.style.ERROR(f'Error finalizing product: {str(e)}')
            )
            raise
