from django.shortcuts import render, get_object_or_404
from django.http import Http404
from ally.product_service import product_service


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

    context = {
        'product': product
    }
    return render(request, 'ally/recommendations.html', context)


def summary(request, product_id):
    """View to display the summary after accepting recommendations."""
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise Http404("Product not found")

    context = {
        'product': product
    }
    return render(request, 'ally/summary.html', context)
