from django.contrib.admin.sites import AdminSite
from django.test import Client, TestCase
from django.urls import reverse

from .admin import ProductAdmin, ProductAdminForm
from .models import Order, OrderItem, Product, User


class StoreAccessTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.customer = User.objects.create_user(username="cliente", password="teste-seguro-123")
		cls.other_customer = User.objects.create_user(username="outro", password="teste-seguro-123")
		cls.manager = User.objects.create_user(username="gerente", password="teste-seguro-123", role=User.Role.MANAGER)
		cls.product = Product.objects.create(title="Jogo de teste", slug="jogo-de-teste", category="Indie", price="40.00")
		cls.customer_order = Order.objects.create(customer=cls.customer)
		OrderItem.objects.create(order=cls.customer_order, product=cls.product, unit_price="40.00")
		cls.other_order = Order.objects.create(customer=cls.other_customer)
		OrderItem.objects.create(order=cls.other_order, product=cls.product, unit_price="40.00")

	def test_checkout_page_shows_summary_before_purchase(self):
		self.client.login(username="cliente", password="teste-seguro-123")
		response = self.client.get(reverse("store:checkout", args=(self.product.pk,)))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Resumo do pedido")
		self.assertContains(response, "Jogo de teste")
		self.assertContains(response, "Pix")

	def test_customer_purchase_is_saved_and_shown_to_customer(self):
		self.client.login(username="cliente", password="teste-seguro-123")
		response = self.client.post(reverse("store:buy", args=(self.product.pk,)))
		self.assertRedirects(response, reverse("store:my_orders"))
		self.assertEqual(Order.objects.filter(customer=self.customer).count(), 2)
		response = self.client.get(reverse("store:my_orders"))
		self.assertContains(response, "Jogo de teste")
		self.assertEqual(len(response.context["orders"]), 2)
		last_order = Order.objects.filter(customer=self.customer).latest("created_at")
		self.assertEqual(last_order.payment_method, Order.PaymentMethod.PIX)
		self.assertTrue(last_order.pix_code)

	def test_customer_cannot_view_manager_orders(self):
		self.client.login(username="cliente", password="teste-seguro-123")
		self.assertEqual(self.client.get(reverse("store:manager_orders")).status_code, 403)

	def test_account_shows_customer_profile_and_own_orders(self):
		self.client.login(username="cliente", password="teste-seguro-123")
		response = self.client.get(reverse("store:account"))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context["order_count"], 1)
		self.assertEqual(len(response.context["recent_orders"]), 1)
		self.assertContains(response, "Cliente")

	def test_manager_can_view_all_orders(self):
		self.client.login(username="gerente", password="teste-seguro-123")
		response = self.client.get(reverse("store:manager_orders"))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.context["orders"]), 2)

	def test_manager_can_update_order_status(self):
		self.client.login(username="gerente", password="teste-seguro-123")
		response = self.client.post(reverse("store:update_order_status", args=(self.customer_order.pk,)), {"status": Order.Status.COMPLETED})
		self.assertRedirects(response, reverse("store:manager_orders"))
		self.customer_order.refresh_from_db()
		self.assertEqual(self.customer_order.status, Order.Status.COMPLETED)

	def test_superuser_can_manage_orders_in_django_admin(self):
		admin_user = User.objects.create_superuser(username="admin-loja", password="teste-seguro-123", email="admin@example.com")
		self.client.force_login(admin_user)
		response = self.client.get(reverse("admin:store_order_changelist"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "40,00")

	def test_product_admin_form_rejects_price_higher_than_previous_price(self):
		form = ProductAdminForm(data={
			"title": "Jogo Novo",
			"slug": "",
			"category": "RPG",
			"description": "Descrição",
			"price": "60.00",
			"previous_price": "50.00",
			"cover_url": "",
			"featured": False,
			"active": True,
		})
		self.assertFalse(form.is_valid())
		self.assertIn("O preço atual não pode ser maior", str(form.non_field_errors()))

	def test_product_admin_save_model_generates_slug_when_missing(self):
		admin_instance = ProductAdmin(Product, AdminSite())
		product = Product(title="Jogo de teste admin", category="Aventura", price="39.90")
		form = ProductAdminForm(data={
			"title": "Jogo de teste admin",
			"slug": "",
			"category": "Aventura",
			"description": "",
			"price": "39.90",
			"previous_price": "",
			"cover_url": "",
			"featured": False,
			"active": True,
		})
		self.assertTrue(form.is_valid())
		admin_instance.save_model(None, product, form, change=False)
		self.assertEqual(product.slug, "jogo-de-teste-admin")

	def test_home_renders_database_catalog(self):
		response = self.client.get(reverse("store:home"))
		self.assertContains(response, "Jogo de teste")

	def test_guest_must_sign_in_before_purchase(self):
		response = self.client.post(reverse("store:buy", args=(self.product.pk,)))
		self.assertRedirects(response, reverse("store:login"))

	def test_registration_always_creates_customer_role(self):
		response = self.client.post(reverse("store:register"), {
			"username": "nova-cliente", "email": "cliente@example.com",
			"first_name": "Novo", "last_name": "Cliente",
			"password1": "Django-Testing-2026!", "password2": "Django-Testing-2026!",
		})
		self.assertRedirects(response, reverse("store:account"))
		self.assertEqual(User.objects.get(username="nova-cliente").role, User.Role.CUSTOMER)

	def test_registration_accepts_local_https_origin_with_csrf_checks(self):
		client = Client(enforce_csrf_checks=True)
		form_response = client.get(reverse("store:register"), secure=True, HTTP_HOST="localhost:8000")
		csrf_token = form_response.cookies["csrftoken"].value
		response = client.post(reverse("store:register"), {
			"username": "cliente-https", "email": "https@example.com",
			"first_name": "HTTPS", "last_name": "Cliente",
			"password1": "Django-Testing-2026!", "password2": "Django-Testing-2026!",
		}, secure=True, HTTP_HOST="localhost:8000", HTTP_ORIGIN="https://localhost:8000", HTTP_X_CSRFTOKEN=csrf_token)
		self.assertRedirects(response, reverse("store:account"), fetch_redirect_response=False)
