import asyncio
import logging

from django.shortcuts import render, get_object_or_404
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from ally.product_service import product_service
from ally.services.agent_service import AgentService
from ally.services.competitor_report_service import competitor_report_service
from ally.services.product_recommendation_service import product_recommendation_service

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

    # Get the recommendations from the ProductRecommendationService
    recommendations = product_recommendation_service.get_recommendations(product_id)

    context = {
        'product': product,
        'competitor_report': report,
        'product_recommendations': recommendations
    }
    return render(request, 'ally/recommendations.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def generate_competitor_report_view(request, product_id):
    """
    API endpoint to generate a competitor report and recommendations for a product.

    Args:
        request: The HTTP request
        product_id: The product ID
    """
    # Get force_regeneration from request body if present
    import json
    force_regeneration = False
    try:
        if request.body:
            body = json.loads(request.body)
            force_regeneration = body.get('force_regeneration', False)
    except json.JSONDecodeError:
        force_regeneration = False

    logger.info(f'Received request to generate competitor report for product: {product_id} (force_regeneration={force_regeneration})')

    # Verify the product exists
    product = product_service.get_product_by_id(product_id)
    if not product:
        return JsonResponse({
            'status': 'error',
            'message': f'Product {product_id} not found'
        }, status=404)

    try:
        report = None
        recommendations = None
        report_generated = False
        recommendations_generated = False

        # Check if we should use cached values
        if not force_regeneration:
            # Try to get existing report
            report = competitor_report_service.get_report(product_id)
            if report:
                logger.info(f'Using cached competitor report for product: {product_id}')

            # Try to get existing recommendations
            recommendations = product_recommendation_service.get_recommendations(product_id)
            if recommendations:
                logger.info(f'Using cached recommendations for product: {product_id}')

        # Generate competitor report if needed
        if force_regeneration or not report:
            report = asyncio.run(
                AgentService.run_competitor_report(
                    product_id=product_id,
                    user_id=request.session.session_key or 'anonymous',
                    timeout_seconds=300  # 5 minutes
                )
            )
            report_generated = True
            logger.info(f'Successfully generated new competitor report for product: {product_id}')

        # Generate recommendations if needed
        if force_regeneration or not recommendations:
            recommendations = asyncio.run(
                AgentService.run_recommendations(
                    product_id=product_id,
                    user_id=request.session.session_key or 'anonymous',
                    timeout_seconds=300  # 5 minutes
                )
            )
            recommendations_generated = True
            logger.info(f'Successfully generated new recommendations for product: {product_id}')

        # Prepare status message
        if report_generated and recommendations_generated:
            message = 'Competitor report and recommendations generated successfully'
        elif report_generated:
            message = 'Competitor report generated successfully, using cached recommendations'
        elif recommendations_generated:
            message = 'Recommendations generated successfully, using cached competitor report'
        else:
            message = 'Using cached competitor report and recommendations'

        return JsonResponse({
            'status': 'success',
            'message': message,
            'report': report,
            'recommendations': recommendations,
            'cached': {
                'report': not report_generated,
                'recommendations': not recommendations_generated
            }
        })

    except Exception as e:
        logger.error(f'Error generating competitor report: {str(e)}', exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to generate report: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def finalize_product_view(request, product_id):
    """API endpoint to finalize product by applying recommendations."""
    logger.info(f'Received request to finalize product: {product_id}')

    # Verify the product exists
    product = product_service.get_product_by_id(product_id)
    if not product:
        return JsonResponse({
            'status': 'error',
            'message': f'Product {product_id} not found'
        }, status=404)

    try:
        # Run the final agent (which will apply recommendations and create summary)
        summary = asyncio.run(
            AgentService.run_final_agent(
                product_id=product_id,
                user_id=request.session.session_key or 'anonymous',
                timeout_seconds=600  # 10 minutes
            )
        )

        logger.info(f'Successfully finalized product: {product_id}')

        return JsonResponse({
            'status': 'success',
            'message': 'Product finalized successfully',
            'summary': summary
        })

    except Exception as e:
        logger.error(f'Error finalizing product: {str(e)}', exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to finalize product: {str(e)}'
        }, status=500)


def summary(request, product_id):
    """View to display the summary after accepting recommendations."""
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise Http404("Product not found")

    # Get the summarization from the SummarizationService
    from ally.services.summarization_service import summarization_service
    summarization = summarization_service.get_summarization(product_id)

    context = {
        'product': product,
        'summarization': summarization
    }
    return render(request, 'ally/summary.html', context)
