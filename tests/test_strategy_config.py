from pathlib import Path

from trader.strategy.grid.grid_strategy import GridStrategyConfig
from trader.spot.api.exchange import Exchange
from trader.strategy.grid.grid_generators import ConfigGridGenerator
from trader.spot.types import CoinPair


def test_load_config():
    config_json = """
        {
            "exchange":"BINANCE",
            "generator":"/path/grid.json",
            "coin_pair":"BTC$USDT"
        }
    """
    config_f = Path("./fake_config.json")
    config_f.write_text(config_json)
    config = GridStrategyConfig.load_from_json(config_f)
    assert config.exchange == Exchange.BINANCE
    assert isinstance(config.generator, ConfigGridGenerator)
    assert isinstance(config.coin_pair, CoinPair)
    config_f.unlink(missing_ok=True)
