"""
WSGI config for thebyte_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os
import logging

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'thebyte_project.settings')

application = get_wsgi_application()

logger = logging.getLogger(__name__)


def _sync_render_database_on_startup():
    """
    Ensure migrations and menu seed data are applied when WSGI starts on Render,
    even if the Render Dashboard Build Command was not set to run build.sh.
    """
    if os.environ.get('SKIP_WSGI_AUTO_SYNC', '').lower() in ('true', '1', 'yes'):
        return
    try:
        from django.core.management import call_command
        call_command('migrate', interactive=False, verbosity=0)
        call_command('seed_data', verbosity=0)
    except Exception as exc:
        logger.warning("WSGI startup database sync warning: %s", exc)


_sync_render_database_on_startup()
