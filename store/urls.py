from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("entrar/", views.login_view, name="login"),
    path("criar-conta/", views.register, name="register"),
    path("sair/", views.logout_view, name="logout"),
    path("comprar/<int:product_id>/", views.buy_product, name="buy"),
    path("minha-conta/", views.account, name="account"),
    path("minhas-compras/", views.my_orders, name="my_orders"),
    path("gerencia/compras/", views.manager_orders, name="manager_orders"),
    path("gerencia/compras/<int:order_id>/status/", views.update_order_status, name="update_order_status"),
]