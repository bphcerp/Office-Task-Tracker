"""Application logging setup."""

from __future__ import annotations

import logging
import os


def configure_logging() -> None:
    """Configure app logging and LiteLLM loggers.

    LiteLLM attaches its own StreamHandler to the ``LiteLLM`` logger. With
    ``propagate=True`` (the default), the same record also bubbles to the root
    logger configured by ``basicConfig``, which prints every API call twice.
    """
    # Must be set before litellm is imported so its handler level is correct.
    os.environ.setdefault("LITELLM_LOG", "DEBUG")

    logging.basicConfig(level=logging.INFO)

    from litellm._logging import verbose_logger, verbose_proxy_logger, verbose_router_logger

    for litellm_logger in (verbose_logger, verbose_proxy_logger, verbose_router_logger):
        litellm_logger.propagate = False
