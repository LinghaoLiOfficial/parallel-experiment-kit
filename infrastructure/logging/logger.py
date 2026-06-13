import logging
import logging.config
import os
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def setup_logging(root_path: str | Path | None = None):
    root = Path(root_path or Path.cwd())
    log_dir = root / os.getenv("LOG_FILE_PATH", "logs")
    log_to_file = _bool_env("LOG_TO_FILE", True)
    log_level = os.getenv("LOG_LEVEL", "INFO")
    env = os.getenv("ENV", "dev")
    max_size_mb = int(os.getenv("LOG_MAX_SIZE_MB", "10"))
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "default",
            "stream": "ext://sys.stdout",
        }
    }
    root_handlers = ["console"]

    if log_to_file:
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "file",
            "maxBytes": max_size_mb * 1024 * 1024,
            "backupCount": backup_count,
            "filename": str(log_dir / ("app.log" if env != "dev" else "app.info.log")),
            "encoding": "utf-8",
        }
        handlers["error_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "file",
            "maxBytes": max_size_mb * 1024 * 1024,
            "backupCount": backup_count,
            "filename": str(log_dir / ("error.log" if env != "dev" else "app.warning.log")),
            "encoding": "utf-8",
        }
        root_handlers.extend(["file", "error_file"])

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "file": {
                    "format": "%(asctime)s | %(name)-20s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": handlers,
            "loggers": {
                "": {"level": log_level, "handlers": root_handlers},
                "app": {"level": log_level, "handlers": root_handlers, "propagate": False},
            },
        }
    )


def get_logger(name: str = "app") -> logging.Logger:
    if name is None or name == "app":
        return logging.getLogger("app")
    if name.startswith("app."):
        return logging.getLogger(name)
    return logging.getLogger(f"app.{name}")
