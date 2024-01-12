from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Avg

from .models import Product, Category, Review
from checkout.models import Order
from .forms import ReviewForm


class ProductListView(ListView):
    """A Class Based View to show all products, including search queries,
    to calculate and save to DB average product rating
    """
    model = Product    
    template_name = 'products/products.html'
    context_object_name = 'products'

    for product in Product.objects.all():        
        approved_reviews = Review.objects.filter(product_id=product.id,approved=True)
        avg = approved_reviews.aggregate(Avg('rate'))['rate__avg']              
        if avg is not None:
            rounded_avg = 0.5 * round(avg/0.5)
            product.rating = rounded_avg
            product.save()    
    
    def get_queryset(self):
        queryset = super(ProductListView, self).get_queryset()
        # category_id = self.kwargs.get('category_id')
        # if category_id:
        #     queryset = queryset.filter(category_id=category_id)           
        q = self.request.GET.get('q') 
        if q:
            queryset = self.model.objects.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
                )                    
        return queryset
        
    def get_context_data(self, object_list=None, **kwargs):
        context = super(ProductListView, self).get_context_data()
        context['categories'] = Category.objects.all()
        # context['category_id'] = self.kwargs.get('category_id')        
        context['q'] = self.request.GET.get('q')                               
        return context

  
def CategoryView(request, slug):
    """A view to get all product categories and
    products by current category
    """
    try:
        current_category = Category.objects.get(name=slug)
        category_products = Product.objects.filter(category=current_category)
        all_categories = Category.objects.all()
        context = {
        'category_products': category_products,
        'slug': slug,
        'categories': all_categories
        }
        return render(request, 'products/products.html', context)
    except:
        messages.error(request, "That category doesn't exist")
        return redirect('products:products')
    
    
def product_detail(request, product_id):
    """A view to show individual product details"""

    product = get_object_or_404(Product, pk=product_id)
    # print(product)
    category = Category.objects.filter(product=product)
    # print(category)
    context = {
        "product": product,
        "category": category,        
    }
    return render(request, "products/product_detail.html", context)


class ReviewView(SuccessMessageMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'products/review_product.html'
    success_message = "Your review was created! It will be shown after admin approval"
    extra_tags = 'flag'
    success_url = '/order_details/'

    def get_success_url(self):
        return reverse('profile:order_details', kwargs={
                       'order_id': self.kwargs['order_id']})   
   
    def form_valid(self, form):
        form.instance.user = self.request.user.userprofile
        form.instance.product_id = self.kwargs['product_id']
        success_message = self.get_success_message(form.cleaned_data)
        if success_message:
            messages.success(self.request, success_message, extra_tags=self.extra_tags)        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, pk=self.kwargs['product_id'])
        context['order_id'] = get_object_or_404(Order, id=self.kwargs['order_id'])        
        return context

