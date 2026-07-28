"""Shared extension instances, created here so routes and db modules can
import them without triggering circular imports with the app factory."""
from flask_caching import Cache

cache = Cache(config={"CACHE_TYPE": "simple"})
