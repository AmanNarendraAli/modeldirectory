from django.shortcuts import render, get_object_or_404
from .models import ResourceArticle


def resource_list(request):
    articles = ResourceArticle.objects.filter(is_published=True)
    return render(request, "resources/resource_list.html", {"articles": articles})


def resource_detail(request, slug):
    article = get_object_or_404(ResourceArticle, slug=slug, is_published=True)
    return render(request, "resources/resource_detail.html", {"article": article})
