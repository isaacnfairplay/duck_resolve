"""ASGI entrypoint with demo schemas/resolvers pre-registered."""

from .app import create_app

app = create_app(include_demo_data=True)
