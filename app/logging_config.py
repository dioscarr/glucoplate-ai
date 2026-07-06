"""
Logging configuration for GlucoPlate AI.

Uses loguru for all application logging.
Stdlib `logging` (used by Uvicorn, FastAPI, SQLAlchemy, etc.) is intercepted
and forwarded to loguru so everything flows through a single sink.

Usage anywhere in the app:
    from loguru import logger
    logger.info("Something happened")
    logger.warning("Fallback triggered: {}", reason)
    logger.exception("Unhandled error")   # includes traceback automatically
"""

import logging
import sys

from loguru import logger


class _InterceptHandler(logging.Handler):
    """Forward all stdlib logging records to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        # Find the matching loguru level name if possible
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Walk up the call stack to find the originating frame outside loguru
        frame, depth = logging.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure loguru and intercept stdlib logging.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR).
        json_logs:  When True, emit newline-delimited JSON (useful for log
                    aggregators like Loki, Datadog, or CloudWatch).
    """
    # Remove the default loguru handler so we can customise it
    logger.remove()

    if json_logs:
        logger.add(
            sys.stdout,
            level=log_level,
            serialize=True,          # loguru built-in JSON serialisation
            enqueue=True,            # async-safe
        )
    else:
        logger.add(
            sys.stdout,
            level=log_level,
            colorize=True,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
                "<level>{message}</level>"
            ),
            enqueue=True,
        )

    # Intercept everything coming from stdlib logging
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    # Silence noisy third-party loggers at WARNING level
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logger.info("Logging initialised — level={}, json={}", log_level, json_logs)
