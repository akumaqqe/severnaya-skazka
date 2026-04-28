import os

from django.apps import AppConfig
from django.core.management import call_command
from django.db.utils import OperationalError, ProgrammingError


_render_bootstrap_attempted = False


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        import core.signals  # noqa: F401

        self.bootstrap_render_demo_content()

    def bootstrap_render_demo_content(self):
        global _render_bootstrap_attempted

        if _render_bootstrap_attempted:
            return

        if os.environ.get("RENDER", "").lower() != "true":
            return

        _render_bootstrap_attempted = True
        try:
            call_command("bootstrap_demo_site", verbosity=0)
        except (OperationalError, ProgrammingError):
            # During collectstatic/migrate the DB might be unavailable or incomplete.
            return
