import asyncio
import selectors
import sys


def selector_loop_factory(use_subprocess: bool = False) -> asyncio.AbstractEventLoop:
    """psycopg's async driver cannot run on Windows' default ProactorEventLoop."""
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop(selectors.SelectSelector())
    return asyncio.new_event_loop()
