from django.core.management.base import BaseCommand
from otomoto.parsers import sync_all_active_otomoto_adverts

class Command(BaseCommand):
    help = "Sync all active Otomoto adverts (pairs and singles)"

    def handle(self, *args, **options):
        updated_count = 0

        # Call the function that handles both pairs and singles
        sync_all_active_otomoto_adverts()
        self.stdout.write(self.style.SUCCESS("Otomoto adverts synced successfully"))