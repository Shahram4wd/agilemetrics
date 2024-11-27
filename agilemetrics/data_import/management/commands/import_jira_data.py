from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Imports Jira data into the database'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting Jira data import...")
        # Add your Jira data import logic here
        self.stdout.write("Jira data import completed.")
