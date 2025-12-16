import asyncio
import logging

from django.shortcuts import render, get_object_or_404
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_http_methods
from ally.product_service import product_service
from ally.services.agent_service import AgentService
from ally.services.competitor_report_service import competitor_report_service

logger = logging.getLogger(__name__)


def products_list(request):
    """View to display all products from the ProductService."""
    products = product_service.get_all_products()
    context = {
        'products': products
    }
    return render(request, 'ally/products.html', context)


def recommendations(request, product_id):
    """View to display competitive analysis and recommendations for a product."""
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise Http404("Product not found")

    # Get the report from the CompetitorReportService
    report = competitor_report_service.get_report(product_id)

    context = {
        'product': product,
        'competitor_report': report
    }
    return render(request, 'ally/recommendations.html', context)


@require_http_methods(["POST"])
def generate_competitor_report_view(request, product_id):
    """API endpoint to generate a competitor report for a product."""
    logger.info(f'Received request to generate competitor report for product: {product_id}')

    # Verify the product exists
    product = product_service.get_product_by_id(product_id)
    if not product:
        return JsonResponse({
            'status': 'error',
            'message': f'Product {product_id} not found'
        }, status=404)

    try:
        # Run the agent service (which will save the report to CompetitorReportService)
        report = asyncio.run(
            AgentService.run_competitor_report(
                product_id=product_id,
                user_id=request.session.session_key or 'anonymous',
                timeout_seconds=300  # 5 minutes
            )
        )

        logger.info(f'Successfully generated competitor report for product: {product_id}')

        return JsonResponse({
            'status': 'success',
            'message': 'Competitor report generated successfully',
            'report': report
        })

    except Exception as e:
        logger.error(f'Error generating competitor report: {str(e)}', exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to generate report: {str(e)}'
        }, status=500)


def summary(request, product_id):
    """View to display the summary after accepting recommendations."""
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise Http404("Product not found")

    context = {
        'product': product
    }
    return render(request, 'ally/summary.html', context)
