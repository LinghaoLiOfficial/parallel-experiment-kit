from dotenv import load_dotenv

from infrastructure.config.app_settings import get_settings
from infrastructure.logging.logger import setup_logging


def lifespan():
    settings = get_settings()
    load_dotenv(settings.ROOT_PATH / ".env", override=False)
    setup_logging(settings.ROOT_PATH)
