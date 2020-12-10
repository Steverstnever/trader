from decimal import Decimal

from pandas import DataFrame
import matplotlib.pyplot as plt

from trader.spot.api.binance_spot_api import BinanceSpotApi
from trader.spot.types.coin_pair import CoinPair
from trader.spot.types.kline import KlinePeriod
from trader.strategy.grid.grid_generators import VolumeGridGenerator, VolumeProfile

api = BinanceSpotApi()

k_line = api.get_kline(CoinPair("BTC", "USDT"), KlinePeriod.HOUR1)
vp = VolumeProfile.create_volume_profile(k_line)

g = VolumeGridGenerator(support_price=Decimal("17633.52"),
                        resistance_price=Decimal('19300'),
                        number_of_levels=20,
                        max_position_per_level=Decimal("200"), volume_profile=vp)
levels = g.generate()

df = DataFrame({"c_diff": [float(i.high_price - i.low_price) for i in levels]},
               index=[f"{i.low_price}-{i.high_price}" for i in levels])
print(df)
df.plot.bar()
plt.show()
