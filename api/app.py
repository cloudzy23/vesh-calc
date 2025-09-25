from __future__ import annotations

"""Serverless entrypoint for Vercel.

This module imports the Flask WSGI `app` from the project root and exposes an
ASGI handler via Mangum so Vercel's Python runtime can invoke it. Keep this
file minimal — Vercel will call the exposed `handler` callable.
"""

import os
import sys
from importlib import import_module

# Ensure project root is on path so we can import `app` directly.
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    # Import the Flask app (WSGI) from the project root `app.py`.
    mod = import_module('app')
    flask_app = getattr(mod, 'app')
except Exception as e:
    raise RuntimeError(f'Could not import Flask app: {e}')

# Wrap WSGI app with ASGI adapter and Mangum handler for serverless platforms.
try:
    from asgiref.wsgi import WsgiToAsgi
    from mangum import Mangum

    asgi_app = WsgiToAsgi(flask_app)
    handler = Mangum(asgi_app)
except Exception as e:
    # If the environment doesn't have mangum/asgiref, expose None and allow
    # Vercel's build to fail loudly. During local runs, the original
    # `app.run(...)` in `app.py` can still be used.
    raise
