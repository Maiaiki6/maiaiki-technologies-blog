from django.core.management.base import BaseCommand

from blog.models import Category, Post


class Command(BaseCommand):
    help = "Create the starter posts for the Day 3 launch blog"

    def handle(self, *args, **options):
        categories = {
            "battery-care": Category.objects.get_or_create(name="Battery Care", defaults={"slug": "battery-care"})[0],
            "water-damage": Category.objects.get_or_create(name="Water Damage", defaults={"slug": "water-damage"})[0],
            "screen-repair": Category.objects.get_or_create(name="Screen Repair", defaults={"slug": "screen-repair"})[0],
        }

        starter_posts = [
            {
                "title": "5 signs your phone battery needs replacing",
                "category": categories["battery-care"],
                "excerpt": "A battery that drains quickly or gets hot may be failing and needs a proper check.",
                "body": "If your phone dies before lunch, shuts off suddenly, or seems unusually warm while charging, your battery may be wearing out. A weak battery can also slow down performance, especially on older devices. It is usually best to test the battery and replace it before the phone becomes unreliable.\n\nA quick diagnosis can tell you whether the issue is software-related or a genuine battery failure. If the battery health is poor, replacement is often the safest option.",
                "status": Post.STATUS_PUBLISHED,
            },
            {
                "title": "What to do if your phone gets wet",
                "category": categories["water-damage"],
                "excerpt": "Act fast and avoid charging a wet phone while you assess the damage.",
                "body": "The first step is to power the phone off immediately and disconnect any cable. Keep it away from heat sources, as a hairdryer can make the damage worse by pushing moisture deeper.\n\nAfter drying the outside, place the phone in a cool, dry area with airflow. Avoid pressing buttons or turning it back on until it is fully dry. If the device has already been damaged, a trained technician can inspect the board and confirm what needs repair.",
                "status": Post.STATUS_PUBLISHED,
            },
            {
                "title": "Cracked screen: repair or replace?",
                "category": categories["screen-repair"],
                "excerpt": "A cracked display is not always just cosmetic, and the right fix depends on the damage.",
                "body": "A crack can affect touch response, the display image, and the protective layer of the glass. If the phone still works, some customers choose a simple screen replacement. If there is internal damage or deeper display issues, a full panel replacement may be a better long-term option.\n\nThe best answer depends on the exact damage and the model of the phone. A repair specialist can check whether your device needs glass repair, display replacement, or a more complete fix.",
                "status": Post.STATUS_PUBLISHED,
            },
        ]

        created_count = 0
        for data in starter_posts:
            post, created = Post.objects.get_or_create(
                title=data["title"],
                defaults={
                    "category": data["category"],
                    "excerpt": data["excerpt"],
                    "body": data["body"],
                    "status": data["status"],
                },
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created_count} starter posts."))
