import os
from typing import Any, Callable, Optional


def get_env(
        key: str,
        default: Optional[Any] = None,
        required: bool = False,
        cast: Optional[Callable[[str], Any]] = None
) -> Any:
    value = os.environ.get(key, default)
    if required and (value is None or value == ""):
        raise RuntimeError(f"Missing required environment variable: {key}")
    if value is not None and cast is not None:
        try:
            return cast(value)
        except Exception as e:
            raise ValueError(f"Could not cast env var {key} to {cast}: {e}")
    return value
