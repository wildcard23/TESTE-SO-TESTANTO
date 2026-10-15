from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils.text import slugify

from .models import Order, OrderItem, Product, User


class ProductAdminForm(forms.ModelForm):
	slug = forms.SlugField(required=False)

	class Meta:
		model = Product
		exclude = ("created_at",)

	def clean(self):
		cleaned_data = super().clean()
		title = cleaned_data.get("title")
		slug = cleaned_data.get("slug")
		price = cleaned_data.get("price")
		previous_price = cleaned_data.get("previous_price")

		if not slug and title:
			cleaned_data["slug"] = slugify(title)

		if previous_price and price and previous_price < price:
			raise forms.ValidationError("O preço atual não pode ser maior que o preço anterior.")

		return cleaned_data


@admin.register(User)
class StoreUserAdmin(UserAdmin):
	fieldsets = UserAdmin.fieldsets + (("Loja", {"fields": ("role",)}),)
	add_fieldsets = UserAdmin.add_fieldsets + (("Loja", {"fields": ("role",)}),)
	list_display = ("username", "email", "first_name", "last_name", "role", "is_staff", "is_active")
	list_filter = ("role", "is_staff", "is_active")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	form = ProductAdminForm
	list_display = ("title", "category", "price", "previous_price", "featured", "active")
	list_filter = ("category", "featured", "active")
	search_fields = ("title", "description")
	prepopulated_fields = {"slug": ("title",)}
	fieldsets = (
		("Produto", {"fields": ("title", "slug", "category", "description")}),
		("Preço e visibilidade", {"fields": ("price", "previous_price", "cover_url", "featured", "active")}),
	)
	actions = ["mark_featured", "mark_not_featured", "activate_products", "deactivate_products"]

	def save_model(self, request, obj, form, change):
		if not obj.slug:
			obj.slug = slugify(obj.title)
		super().save_model(request, obj, form, change)

	@admin.action(description="Marcar como destaque")
	def mark_featured(self, request, queryset):
		updated = queryset.update(featured=True, active=True)
		self.message_user(request, f"{updated} produto(s) marcados como destaque.", messages.SUCCESS)

	@admin.action(description="Remover destaque")
	def mark_not_featured(self, request, queryset):
		updated = queryset.update(featured=False)
		self.message_user(request, f"{updated} produto(s) removidos dos destaques.", messages.SUCCESS)

	@admin.action(description="Ativar produtos")
	def activate_products(self, request, queryset):
		updated = queryset.update(active=True)
		self.message_user(request, f"{updated} produto(s) ativados.", messages.SUCCESS)

	@admin.action(description="Desativar produtos")
	def deactivate_products(self, request, queryset):
		updated = queryset.update(active=False)
		self.message_user(request, f"{updated} produto(s) desativados.", messages.SUCCESS)


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	readonly_fields = ("product", "unit_price", "quantity")
	can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("id", "customer", "created_at", "status", "payment_method", "payment_status", "display_total")
	list_filter = ("status", "payment_method", "payment_status", "created_at")
	search_fields = ("customer__username", "customer__email", "id", "pix_code")
	readonly_fields = ("customer", "created_at", "payment_method", "payment_status", "pix_code")
	inlines = (OrderItemInline,)

	@admin.display(description="Total")
	def display_total(self, order):
		return order.total
