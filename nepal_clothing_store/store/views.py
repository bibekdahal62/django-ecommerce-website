# store/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Product, Category, Order, OrderItem, Customer
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from decimal import Decimal
from django.contrib.auth import logout as auth_logout

def index(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(available=True)[:8]
    return render(request, 'index.html', {
        'featured_products': featured_products,
        'categories': categories
    })

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    return render(request, 'product_list.html', {
        'category': category,
        'categories': categories,
        'products': products
    })

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    return render(request, 'product_detail.html', {'product': product})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create customer profile
            Customer.objects.create(user=user)
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = Decimal('0.00')
    
    for product_id, item_data in cart.items():
        product = Product.objects.get(id=product_id)
        quantity = item_data['quantity']
        item_total = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total': item_total
        })
        total_price += item_total
    
    tax_rate = Decimal('0.13')
    shipping = Decimal('100.00')
    tax_amount = total_price * tax_rate
    grand_total = total_price + shipping + tax_amount
    
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'tax_amount': tax_amount,
        'shipping': shipping,
        'grand_total': grand_total
    })

@login_required
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product = get_object_or_404(Product, id=product_id)
    
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {'quantity': 1, 'name': product.name, 'price': str(product.price)}
    
    request.session['cart'] = cart
    return redirect('cart_view')

@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
    
    return redirect('cart_view')

@login_required
def update_cart(request, product_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        
        if str(product_id) in cart:
            if quantity > 0:
                cart[str(product_id)]['quantity'] = quantity
            else:
                del cart[str(product_id)]
            
            request.session['cart'] = cart
    
    return redirect('cart_view')


@login_required
def checkout(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('cart_view')
        
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip')
        phone = request.POST.get('phone')
        notes = request.POST.get('notes', '')
        payment_method = request.POST.get('payment_method', 'cod')
        
        # Create order with shipping information
        customer, created = Customer.objects.get_or_create(user=request.user)
        
        # Update customer information if provided
        if first_name and last_name and address and phone:
            customer.phone = phone
            customer.address = f"{first_name} {last_name}\n{address}\n{city}, {state} {zip_code}\nPhone: {phone}"
            customer.save()
        
        # Create order
        order = Order.objects.create(
            customer=customer, 
            paid=True,  # For COD, we mark as paid since payment will be collected on delivery
            shipping_address=f"{first_name} {last_name}\n{address}\n{city}, {state} {zip_code}",
            shipping_phone=phone,
            notes=notes,
            payment_method=payment_method
        )
        
        for product_id, item_data in cart.items():
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,
                quantity=item_data['quantity']
            )
        
        # Clear the cart
        request.session['cart'] = {}
        return render(request, 'order_confirmation.html', {'order': order})
    
    # Calculate cart totals for display (existing code)
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = Decimal('0.00')
    
    for product_id, item_data in cart.items():
        product = Product.objects.get(id=product_id)
        quantity = item_data['quantity']
        item_total = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total': item_total
        })
        total_price += item_total
    
    tax_rate = Decimal('0.13')
    shipping = Decimal('100.00')
    tax_amount = total_price * tax_rate
    grand_total = total_price + shipping + tax_amount
    
    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'tax_amount': tax_amount,
        'shipping': shipping,
        'grand_total': grand_total
    })


def custom_logout(request):
    auth_logout(request)
    return redirect('index')

@login_required
def about_us(request):
    return render(request, 'about_us.html')