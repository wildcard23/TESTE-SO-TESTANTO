from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F, Sum
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import RegistrationForm
from .models import Order, OrderItem, Product


def home(request):
	products = Product.objects.filter(active=True)
	query = request.GET.get("q", "").strip()
	category = request.GET.get("category", "")
	if query:
		products = products.filter(title__icontains=query)
	if category:
		products = products.filter(category__iexact=category)
	categories = Product.objects.filter(active=True).values_list("category", flat=True).distinct().order_by("category")
	featured_product = Product.objects.filter(active=True, featured=True).first() or Product.objects.filter(active=True).first()
	return render(request, "store/storefront.html", {
		"page": "home", "products": products, "categories": categories,
		"query": query, "category": category, "featured_product": featured_product,
	})


def login_view(request):
	if request.user.is_authenticated:
		return redirect("store:account")
	error = ""
	if request.method == "POST":
		user = authenticate(request, username=request.POST.get("username", ""), password=request.POST.get("password", ""))
		if user is not None:
			next_url = request.POST.get("next") or request.GET.get("next") or ""
			if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
				next_url = ""
			login(request, user)
			return redirect(next_url or "store:account")
		error = "Usuário ou senha inválidos."
	elif request.method != "GET":
		return HttpResponseNotAllowed(["GET", "POST"])
	return render(request, "store/storefront.html", {"page": "login", "error": error})


def register(request):
	if request.user.is_authenticated:
		return redirect("store:account")
	form = RegistrationForm(request.POST or None)
	if request.method == "POST" and form.is_valid():
		user = form.save(commit=False)
		user.role = user.Role.CUSTOMER
		user.save()
		login(request, user)
		messages.success(request, "Sua conta foi criada. Boas-vindas à Greenroom!")
		return redirect("store:account")
	return render(request, "store/storefront.html", {"page": "register", "form": form})


@require_POST
def buy_product(request, product_id):
	if not request.user.is_authenticated:
		messages.info(request, "Entre na sua conta para registrar uma compra.")
		return redirect("store:login")
	product = get_object_or_404(Product, pk=product_id, active=True)
	with transaction.atomic():
		order = Order.objects.create(customer=request.user)
		OrderItem.objects.create(order=order, product=product, unit_price=product.price)
	messages.success(request, f"Pedido #{order.pk} registrado. Acompanhe o status nesta página.")
	return redirect("store:my_orders")


@login_required
def account(request):
	user_orders = Order.objects.filter(customer=request.user)
	total_spent = OrderItem.objects.filter(order__customer=request.user).exclude(
		order__status=Order.Status.CANCELLED
	).aggregate(total=Sum(F("unit_price") * F("quantity")))["total"] or Decimal("0.00")
	return render(request, "store/storefront.html", {
		"page": "account",
		"recent_orders": user_orders.prefetch_related("items__product")[:5],
		"order_count": user_orders.count(),
		"open_order_count": user_orders.filter(status__in=(Order.Status.NEW, Order.Status.PROCESSING)).count(),
		"total_spent": total_spent,
	})


@login_required
def my_orders(request):
	orders = Order.objects.filter(customer=request.user).prefetch_related("items__product")
	return render(request, "store/storefront.html", {"page": "my_orders", "orders": orders})


def manager_required(view):
	@wraps(view)
	@login_required
	def wrapped(request, *args, **kwargs):
		if not request.user.can_manage_orders:
			raise PermissionDenied
		return view(request, *args, **kwargs)
	return wrapped


@manager_required
def manager_orders(request):
	orders = Order.objects.select_related("customer").prefetch_related("items__product")
	status = request.GET.get("status", "")
	if status in Order.Status.values:
		orders = orders.filter(status=status)
	return render(request, "store/storefront.html", {
		"page": "manager_orders", "orders": orders, "statuses": Order.Status.choices,
		"selected_status": status, "order_count": Order.objects.count(),
		"customer_count": Order.objects.values("customer_id").distinct().count(),
	})


@require_POST
@manager_required
def update_order_status(request, order_id):
	order = get_object_or_404(Order, pk=order_id)
	new_status = request.POST.get("status")
	if new_status not in Order.Status.values:
		raise PermissionDenied
	order.status = new_status
	order.save(update_fields=("status",))
	messages.success(request, f"Pedido #{order.pk} atualizado para {order.get_status_display()}.")
	return redirect("store:manager_orders")


def logout_view(request):
	if request.method != "POST":
		return HttpResponseNotAllowed(["POST"])
	logout(request)
	return redirect("store:home")
