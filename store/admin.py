from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Order, OrderItem, Product, User


@admin.register(User)
class StoreUserAdmin(UserAdmin):
	fieldsets = UserAdmin.fieldsets + (("Loja", {"fields": ("role",)}),)
	add_fieldsets = UserAdmin.add_fieldsets + (("Loja", {"fields": ("role",)}),)
	list_display = ("username", "email", "first_name", "last_name", "role", "is_staff", "is_active")
	list_filter = ("role", "is_staff", "is_active")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ("title", "category", "price", "featured", "active")
	list_filter = ("category", "featured", "active")
	search_fields = ("title", "description")
	prepopulated_fields = {"slug": ("title",)}


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	readonly_fields = ("product", "unit_price", "quantity")
	can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("id", "customer", "created_at", "status", "display_total")
	list_filter = ("status", "created_at")
	search_fields = ("customer__username", "customer__email", "id")
	readonly_fields = ("customer", "created_at")
	inlines = (OrderItemInline,)

	@admin.display(description="Total")
	def display_total(self, order):
		return order.total
