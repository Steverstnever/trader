import logging
from datetime import timedelta
from decimal import Decimal

from trader.spot.api.exchange import Exchange
from trader.spot.types import CoinPair
from trader.strategy.grid import GridStrategyConfig
from trader.strategy.grid.grid_generators import ArithmeticGridGenerator
from trader.strategy.grid.grid_strategy import GridStrategyApp
from trader.utils import load_dev_credentials

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )

credentials = load_dev_credentials()
logging.info(f"当前 credentials: {credentials}")

# 设置网格生成器
grid_generator = ArithmeticGridGenerator(
    support_price=Decimal("20"),
    resistance_price=Decimal("29"),
    number_of_levels=60,
    max_position_per_level=Decimal("0.33"))

# 设置策略配置
config = GridStrategyConfig(
    exchange=Exchange.BINANCE,
    coin_pair=CoinPair("BNB", "USDT"),
    generator=grid_generator,
    enter_trigger_price=Decimal(),  # Decimal("30.60"),
    stop_on_exit=False,
    level_min_profit=Decimal(0.005),
    order_query_interval=timedelta(seconds=1),
    order_cancel_timeout=timedelta(seconds=5))

app = GridStrategyApp(config, credentials=credentials)
app.run()
