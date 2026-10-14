from django.core.management.base import BaseCommand

from store.models import Product


PRODUCTS = [
    ("Cyberpunk 2077", "cyberpunk-2077", "RPG", "Uma jornada futurista por Night City.", "99.90", "199.90", "1091500", True),
    ("Elden Ring", "elden-ring", "Ação", "Explore as Terras Intermédias e enfrente seus desafios.", "169.90", None, "1245620", False),
    ("Hades II", "hades-ii", "Indie", "Enfrente o submundo em uma aventura roguelike.", "88.99", None, "1145350", False),
    ("Balatro", "balatro", "Estratégia", "Poker e construção de baralho em partidas irresistíveis.", "42.99", "59.99", "2379780", False),
    ("Baldur's Gate 3", "baldurs-gate-3", "RPG", "Uma aventura épica de RPG para jogar do seu jeito.", "179.90", None, "1086940", False),
    ("Hollow Knight", "hollow-knight", "Indie", "Explore um reino subterrâneo feito à mão.", "27.99", "46.99", "367520", False),
]


class Command(BaseCommand):
    help = "Adiciona jogos de demonstração ao catálogo."

    def handle(self, *args, **options):
        for title, slug, category, description, price, previous_price, steam_id, featured in PRODUCTS:
            Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "category": category,
                    "description": description,
                    "price": price,
                    "previous_price": previous_price,
                    "cover_url": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{steam_id}/header.jpg",
                    "featured": featured,
                    "active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS(f"{len(PRODUCTS)} jogos prontos no catálogo."))