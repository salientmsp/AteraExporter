"""
Request Queue Module
Manages concurrent API requests with rate limiting and worker pool
"""

import threading
import time
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple token bucket rate limiter"""

    def __init__(self, max_requests_per_second: int = 10):
        """
        Initialize rate limiter

        Args:
            max_requests_per_second: Maximum requests allowed per second
        """
        self.max_requests = max_requests_per_second
        self.tokens = max_requests_per_second
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self, blocking: bool = True) -> bool:
        """
        Acquire a token to make a request

        Args:
            blocking: If True, wait until token is available

        Returns:
            True if token acquired, False otherwise
        """
        while True:
            with self.lock:
                now = time.time()
                # Refill tokens based on time passed
                time_passed = now - self.last_update
                self.tokens = min(
                    self.max_requests,
                    self.tokens + time_passed * self.max_requests
                )
                self.last_update = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                elif not blocking:
                    return False

            # Wait a bit before trying again
            if blocking:
                time.sleep(0.1)
            else:
                break

        return False


class RequestQueue:
    """
    Manages a queue of API requests with concurrent execution and rate limiting
    """

    def __init__(
        self,
        max_workers: int = 5,
        max_requests_per_second: int = 10,
        enable_rate_limiting: bool = True
    ):
        """
        Initialize request queue

        Args:
            max_workers: Maximum number of concurrent worker threads
            max_requests_per_second: Rate limit for API requests
            enable_rate_limiting: Whether to enable rate limiting
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.rate_limiter = RateLimiter(max_requests_per_second) if enable_rate_limiting else None

        logger.info(
            f"Initialized RequestQueue with {max_workers} workers, "
            f"rate limit: {max_requests_per_second if enable_rate_limiting else 'disabled'} req/s"
        )

    def execute_batch(
        self,
        tasks: List[Tuple[Callable, tuple, dict]],
        show_progress: bool = False
    ) -> List[Tuple[bool, Any]]:
        """
        Execute a batch of tasks concurrently

        Args:
            tasks: List of (function, args, kwargs) tuples
            show_progress: Whether to log progress

        Returns:
            List of (success, result) tuples in same order as input tasks
        """
        if not tasks:
            return []

        total_tasks = len(tasks)
        logger.info(f"Starting batch execution of {total_tasks} tasks with {self.max_workers} workers")

        # Submit all tasks
        future_to_index = {}
        for idx, (func, args, kwargs) in enumerate(tasks):
            future = self.executor.submit(self._execute_with_rate_limit, func, args, kwargs)
            future_to_index[future] = idx

        # Collect results in order
        results = [None] * total_tasks
        completed = 0

        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                success, result = future.result()
                results[idx] = (success, result)
                completed += 1

                if show_progress and completed % 10 == 0:
                    logger.info(f"Progress: {completed}/{total_tasks} tasks completed ({completed*100//total_tasks}%)")
            except Exception as e:
                logger.error(f"Task {idx} raised exception: {str(e)}")
                results[idx] = (False, None)
                completed += 1

        logger.info(f"Batch execution complete: {total_tasks} tasks finished")
        return results

    def _execute_with_rate_limit(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict
    ) -> Tuple[bool, Any]:
        """
        Execute a function with rate limiting

        Args:
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            (success, result) tuple
        """
        # Acquire rate limit token if enabled
        if self.rate_limiter:
            self.rate_limiter.acquire(blocking=True)

        # Execute the function
        try:
            result = func(*args, **kwargs)
            return (True, result)
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            return (False, None)

    def map(
        self,
        func: Callable,
        items: List[Any],
        show_progress: bool = False
    ) -> List[Any]:
        """
        Map a function over a list of items concurrently

        Args:
            func: Function that takes one item and returns a result
            items: List of items to process
            show_progress: Whether to log progress

        Returns:
            List of results in same order as input items
        """
        tasks = [(func, (item,), {}) for item in items]
        results = self.execute_batch(tasks, show_progress=show_progress)
        return [result for success, result in results]

    def shutdown(self, wait: bool = True):
        """
        Shutdown the executor and wait for pending tasks

        Args:
            wait: If True, wait for all pending tasks to complete
        """
        logger.info("Shutting down RequestQueue")
        self.executor.shutdown(wait=wait)

    def __enter__(self):
        """Support for context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting context manager"""
        self.shutdown(wait=True)
        return False
