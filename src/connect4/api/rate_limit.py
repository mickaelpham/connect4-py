import asyncio
import inspect

# slowapi 0.1.9 uses the deprecated asyncio.iscoroutinefunction
# (removed in Python 3.16). Apply the recommended replacement.
asyncio.iscoroutinefunction = inspect.iscoroutinefunction  # type: ignore[assignment]

from slowapi import Limiter  # noqa: E402
from slowapi.util import get_remote_address  # noqa: E402

limiter = Limiter(key_func=get_remote_address)
