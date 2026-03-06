"""Shared hint cache and generator singletons.

Both the REST practice endpoint (src/routes/practice.py) and the Telegram
webhook (src/routes/webhook.py) import from here so a hint generated via
either interface is served from the same in-memory cache on the next request.
"""

from src.services.hint_cache import HintCache
from src.services.hint_generator import HintGenerator

hint_cache = HintCache()
hint_generator = HintGenerator(cache=hint_cache)
