from django.core.management.base import BaseCommand
from insurance.seed_insurance import seed_insurance

class Command(BaseCommand):
    help = 'Seed sample insurance and pension data'

    def handle(self, *args, **options):
        seed_insurance()
