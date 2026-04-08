import os
import warnings

# slowapi 0.1.9 uses the deprecated asyncio.iscoroutinefunction.
# Suppress until slowapi releases a fix.
warnings.filterwarnings(
    "ignore",
    message=r"'asyncio\.iscoroutinefunction'",
    category=DeprecationWarning,
)

from slowapi import Limiter  # noqa: E402
from slowapi.util import get_remote_address  # noqa: E402

limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.environ.get("DISABLE_RATE_LIMIT") != "1",
)
