"""Retry utility with exponential backoff for API calls."""
import time
import logging
import functools
from typing import TypeVar, Callable, Any

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay between retries.
        exceptions: Tuple of exception types to catch and retry.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"Function {func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            raise last_exception  # type: ignore
        return wrapper  # type: ignore
    return decorator


async def async_retry_with_backoff(
    func: Callable[..., T],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
    **kwargs: Any,
) -> T:
    """
    Async retry wrapper with exponential backoff.

    Args:
        func: The async function to retry.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay between retries.
        exceptions: Tuple of exception types to catch and retry.
    """
    import asyncio

    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(
                    f"Async function {func.__name__} failed after {max_retries + 1} attempts: {e}"
                )
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(
                f"Async function {func.__name__} attempt {attempt + 1} failed: {e}. "
                f"Retrying in {delay:.1f}s..."
            )
            await asyncio.sleep(delay)
    raise last_exception  # type: ignore
