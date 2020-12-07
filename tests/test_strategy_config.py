from pathlib import Path

from trader.strategy.grid.grid_strategy import GridStrategyConfig
from trader.spot.api.exchange import Exchange
from trader.strategy.grid.grid_generators import ConfigGridGenerator
from trader.spot.types import CoinPair


def test_load_config():
    sample_config_dict = {
        "exchange": "BINANCE",
        "generator": "/path/grid.json",
        "coin_pair": "BTC$USDT"
    }

    config = GridStrategyConfig.load_from_dict(sample_config_dict)
    assert config.exchange == Exchange.BINANCE
    assert isinstance(config.generator, ConfigGridGenerator)
    assert isinstance(config.coin_pair, CoinPair)
