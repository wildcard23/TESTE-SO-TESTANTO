from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
	class Role(models.TextChoices):
		CUSTOMER = "customer", "Cliente"
		MANAGER = "manager", "Gerente"

	role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)

	@property
	def can_manage_orders(self):
		return self.is_superuser or self.role == self.Role.MANAGER


class Product(models.Model):
	title = models.CharField(max_length=120)
	slug = models.SlugField(unique=True)
	category = models.CharField(max_length=40)
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=8, decimal_places=2)
	previous_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
	cover_url = models.URLField(blank=True)
	featured = models.BooleanField(default=False)
	active = models.BooleanField(default=True)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ("-featured", "title")

	def __str__(self):
		return self.title


class Order(models.Model):
	class Status(models.TextChoices):
		NEW = "new", "Novo pedido"
		PROCESSING = "processing", "Em separação"
		COMPLETED = "completed", "Concluído"
		CANCELLED = "cancelled", "Cancelado"

	class PaymentMethod(models.TextChoices):
		PIX = "pix", "Pix"
		CARD = "card", "Cartão"
		WALLET = "wallet", "Carteira"

	class PaymentStatus(models.TextChoices):
		PENDING = "pending", "Pendente"
		PAID = "paid", "Pago"
		CANCELLED = "cancelled", "Cancelado"

	customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
	payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.PIX)
	payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
	pix_code = models.CharField(max_length=64, blank=True, default="")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("-created_at",)

	def save(self, *args, **kwargs):
		if self.payment_method == self.PaymentMethod.PIX and not self.pix_code:
			if self.pk:
				self.pix_code = f"GREENROOM-{self.pk}"
			super().save(*args, **kwargs)
			if not self.pix_code:
				self.pix_code = f"GREENROOM-{self.pk}"
				super().save(update_fields=["pix_code"])
			return
		super().save(*args, **kwargs)

	def __str__(self):
		return f"Pedido #{self.pk} — {self.customer} ({self.get_payment_method_display()})"

	@property
	def total(self):
		return sum((item.unit_price * item.quantity for item in self.items.all()), start=0)


class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
	product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
	unit_price = models.DecimalField(max_digits=8, decimal_places=2)
	quantity = models.PositiveIntegerField(default=1)

	def __str__(self):
		return f"{self.quantity} × {self.product.title}"
