from django.core.management.base import BaseCommand
from apps.ai.ollama_client import ollama_generate, OllamaError


class Command(BaseCommand):
    help = "Healthcheck for Ollama help assistant"

    def handle(self, *args, **options):
        try:
            ans = ollama_generate("Dis 'ok' en un mot.")
            self.stdout.write(self.style.SUCCESS(f"OK: {ans}"))
        except OllamaError as e:
            self.stderr.write(self.style.ERROR(f"KO: {e}"))
            raise SystemExit(1)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"KO: {e}"))
            raise SystemExit(1)
