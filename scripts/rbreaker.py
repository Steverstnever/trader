import logging
import sys

from pathlib import Path
from trader.strategy.rbreaker.rbreaker_strategy import RBreakerStrategyApp, RBreakerConfig
from trader.utils import load_dev_credentials

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )

credentials = load_dev_credentials()
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    config_path = sys.argv[1]
    config = RBreakerConfig.load_from_json(Path(config_path))
    app = RBreakerStrategyApp(config, credentials=credentials)
    app.run()
