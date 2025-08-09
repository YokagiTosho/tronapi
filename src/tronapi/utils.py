from collections.abc import Callable
from functools import wraps
from typing import Optional, Any


def cache(f: Callable[[], Any]):
    cached: Optional[Any] = None

    @wraps(f)
    def wrapper(*args, **kwargs) -> Any:
        nonlocal cached

        if cached is None:
            cached = f(*args, **kwargs)

        return cached

    return wrapper
