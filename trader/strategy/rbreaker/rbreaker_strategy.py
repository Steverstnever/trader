import logging
import sys
from dataclasses import dataclass
from decimal import Decimal
from dataclasses import dataclass
from datetime import timedelta, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

from trader.futures.types import ContractPair
from trader.futures.types.kline import Kline
from trader.credentials import Credentials
from trader.notifier import Notifier, LoggerNotifier
from trader.spot.api.exchange import Exchange
from trader.spot.api.spot_api import SpotApi
from trader.spot.order_executor.limit_gtc_order_executor import OrderNotCancelledError
from trader.spot.types import CoinPair
from trader.spot.types.account_snapshot import AccountSnapshot
from trader.spot.types.book_ticker import BookTicker
from trader.spot.types.order_types import Order
from trader.store import StrategyStore
from trader.store.sqlalchemy_store import SqlalchemyStrategyStore
from trader.strategy.base import Strategy, StrategyEvent, StrategyContext, StrategyApp
from trader.strategy.grid.grid_position_manager import GridPositionManager, GridGenerator
from trader.strategy.grid.grid_strategy_adapter import GridStrategyAdapter
from trader.strategy.runner.timer import TimerEvent, TimerRunner
from trader.strategy.trade_crawler import TradeCrawler


from trader.strategy.base import Strategy


LONG = 'LONG'  # 多单
SHORT = 'SHORT'  # 空单
logger = logging.getLogger('rbreak')
binance_order_not_exit = -2013


class ExchangeManager:
    def __init__(self, exchange):
        self.exchange = exchange
        self.orders = {'BUY.LONG': [], 'BUY.SHORT': [], 'SELL.LONG': [], 'SELL.SHORT': []}

    def is_empty(self):
        return not bool(any(self.orders.values()))

    def show_asset_position(self, contract_pair: ContractPair):
        account = rest.currency_futures_account(self.exchange)

        if self.exchange == binance:
            for item in account['assets']:
                if item['asset'] == symbol.cash:
                    margin_balance = item['marginBalance']
                    wallet_balance = item['walletBalance']
                    logger.info(f'交易所: {self.exchange}|合约账户|资产: {symbol.cash}|余额: {wallet_balance}| '
                                f'保证金余额 :{margin_balance}|')
                    break

    def show_position(self, symbol: Symbol):
        rv = rest.currency_futures_get_position(self.exchange, symbol.perp_value)
        if self.exchange == binance:
            for each in rv:
                amt = Decimal(each['positionAmt'])
                if amt != 0:
                    logger.info(f"|持仓: {symbol.value}|方向: {each['positionSide']}|数量: "
                                f"{amt}| 持仓未实现盈亏: {each['unRealizedProfit']}")

    def get_position(self, symbol: Symbol):
        rv = rest.currency_futures_get_position(self.exchange, symbol.perp_value)
        if self.exchange == binance:
            for each in rv:
                amt = Decimal(each['positionAmt'])
                if amt != 0:
                    return each['positionSide'], abs(amt)  # 币安做空时positionAmt是负数
            return None, 0

    def check_order_exists(self, order_id, **kwargs):
        order = rest.currency_futures_get_order(self.exchange,
                                                origClientOrderId=order_id,
                                                symbol=kwargs['symbol'])
        if self.exchange == binance:
            if order and order['status'] in ('NEW', 'PARTIALLY_FILLED', 'PARTIALLY_FILLED'):
                return True
            else:
                logger.exception(f"{self.exchange}订单{order_id}下单失败{order['status']}")
                return False

    def get_quantity(self, symbol: Symbol):
        """余额900时每次做空0.01btc，做多6*0.01btc, 用一半的余额按照这个比例开仓"""
        balance = rest.currency_futures_account_balance(self.exchange, symbol.cash)
        if balance < 900:  # todo
            return Decimal('0.01')
        return balance / Decimal('1800') * Decimal('0.01')

    def create_order(self, side, position_side, symbol: Symbol, price, quantity):
        if self.exchange == binance:
            unit = tool.get_futures_unit(self.exchange, symbol)
            quantity = tool.make_precision(quantity, unit['quantity_precision'])
            price = tool.make_precision(price, unit['price_precision'])
            if quantity > unit['max_qty'] or quantity < unit['min_qty']:
                logger.exception(f"quantity错误{quantity}, max_qty: {unit['max_qty']}, min_qty: {unit['min_qty']}, "
                                 f"{side} {position_side}")
                return
            if price > unit['max_price'] or price < unit['min_price']:
                logger.exception(f"price错误{price}, max_price: {unit['max_price']}, min_price: {unit['min_price']},"
                                 f"{side} {position_side}")
            order_id = tool.gen_order_id()
            params = {
                'newClientOrderId': order_id,
                'symbol': symbol.value,
                'side': side,
                'positionSide': position_side,
                'type': 'STOP',  # 目前都是stop类型单
                'quantity': str(quantity),
                'price': price,
                'stopPrice': price
            }
            logger.info(f'下单: {params}')
            try:
                rest.futures_create_order(binance, **params)
            except Exception as e:
                logger.exception(e)
                try:
                    if self.check_order_exists(order_id=order_id, symbol=symbol.perp_value):
                        self.orders[f"{side}.{position_side}"].append(order_id)
                    else:
                        logger.exception(f'订单{order_id}创建失败')
                except BinanceAPIException as e:
                    if e.code != binance_order_not_exit:
                        self.orders[f"{side}.{position_side}"].append(order_id)
                except Exception as e:
                    logger.exception(f'未知异常{e}')  # 未知异常，人工处理
                    sys.exit(-1)
            else:
                logger.info(f"订单: {params}创建成功, order id: {order_id}")
                self.orders[f"{side}.{position_side}"].append(order_id)

    def short(self, symbol: Symbol, price, multiplier):
        """做空"""
        quantity = multiplier * self.get_quantity(symbol)
        self.create_order('SELL', 'SHORT', symbol, price, quantity)

    def buy(self, symbol: Symbol, price, multiplier):
        """做多"""
        quantity = multiplier * self.get_quantity(symbol)
        self.create_order('BUY', 'LONG', symbol, price, quantity)

    def sell(self, symbol: Symbol, price, position):
        """平多"""
        self.create_order('SELL', 'LONG', symbol, price, position)

    def cover(self, symbol: Symbol, price, position):
        """平空"""
        self.create_order('BUY', 'SHORT', symbol, price, position)

    def cancel_all_order_with_retry(self, symbol: Symbol, retry_time=3):
        if self.is_empty():
            return
        i = 1
        while i <= retry_time:
            if not self._cancel_all(symbol):
                logger.warning(f'重试撤单第{retry_time}次')
                i += 1
            else:
                break

    def _cancel_all(self, symbol: Symbol):
        if self.exchange == binance:
            try:
                rest.futures_delete_all_order(self.exchange, symbol=symbol.value)
            except Exception as e:
                logger.exception(f"撤单失败{e}, 订单详情{self.orders}")
                return False
            else:
                logger.info(f"撤销全部订单")
                self.orders = {'BUY.LONG': [], 'BUY.SHORT': [], 'SELL.LONG': [], 'SELL.SHORT': []}
                return True


class RBreakerTimerIds(Enum):
    """
    网格策略用到的 timer-id
    """
    BOOK_TICKER = timedelta(seconds=60)  # 每个一分钟获取一次k线
    SAVE_TRADES = timedelta(seconds=5)  # 每分钟保存一次最新成交记录
    SAVE_ACCOUNT_SNAPSHOT = timedelta(hours=0.5)  # 每半小时存储一下资产情况


class RBreakerStrategyContext(StrategyContext):

    def __init__(self, notifier: Notifier, store: StrategyStore):
        self.notifier = notifier if notifier is not None else LoggerNotifier()
        self.store = store

    def get_notifier(self) -> Notifier:
        return self.notifier

    def get_store(self) -> StrategyStore:
        return self.store


@dataclass
class RBreakerConfig:
    exchange: Exchange
    contract_pair: ContractPair
    do_chain_window_size: int
    setup_coef: Decimal
    enter_coef_1: Decimal
    enter_coef_2: Decimal
    break_coef: Decimal
    multiplier: Decimal
    fixed_size: Decimal
    trailing_long: Decimal
    trailing_short: Decimal

    @classmethod
    def load_from_json(cls, path: Path):
        """"""


class RBreakerStrategy(Strategy):
    def __init__(self, conf: RBreakerConfig, context: RBreakerStrategyContext, futures_api: ):
        self.config: RBreakerConfig = conf
        self.kline = Kline(conf.do_chain_window_size)


        self.order_manager = ExchangeManager(self.config.exchange)

        self.day_open = None
        self.day_low = None
        self.day_high = None
        self.day_close = None

        self.buy_setup = None
        self.buy_break = None
        self.buy_enter = None
        self.sell_setup = None
        self.sell_break = None
        self.sell_enter = None

        self.intra_trade_low = 0
        self.intra_trade_high = 0

    def on_start(self):
        k = rest.currency_futures_klines(self.config.exchange,
                                         symbol=self.config.symbol.perp_value,
                                         interval=self.config.interval,
                                         limit=self.config.dochain_window_size)
        for item in k:
            self.kline.append(item)

        k = rest.currency_futures_klines(self.config.exchange,
                                         symbol=self.config.symbol.perp_value,
                                         interval='1d',
                                         limit=2)
        last_day_bar, today_bar = k[0], k[1]
        self.calculate(last_day_bar)
        self.day_open = today_bar.open_price
        self.day_low = today_bar.low
        self.day_high = today_bar.high
        self.day_close = today_bar.close_price

    def calculate(self, bar: KlineItem):
        self.buy_setup = bar.low - self.config.setup_coef * (bar.high - bar.close_price)  # 观察买入价
        self.sell_setup = bar.high + self.config.setup_coef * (bar.close_price - bar.low)  # 观察卖出价

        self.buy_enter = (self.config.enter_coef_1 / 2) * (
                    bar.high + bar.low) - self.config.enter_coef_2 * bar.high  # 反转买入价
        self.sell_enter = (self.config.enter_coef_1 / 2) * (
                    bar.high + bar.low) - self.config.enter_coef_2 * bar.low  # 反转卖出价

        self.buy_break = self.sell_setup + self.config.break_coef * (self.sell_setup - self.buy_setup)  # 突破买入价
        self.sell_break = self.buy_setup - self.config.break_coef * (self.sell_setup - self.buy_setup)  # 突破卖出价
        logger.info('buy_setup: ' + str(tool.make_precision(self.buy_setup, 2)) +
                    ' sell_setup: ' + str(tool.make_precision(self.sell_setup, 2)) +
                    ' buy_enter: ' + str(tool.make_precision(self.buy_enter, 2)) +
                    ' sell_enter: ' + str(tool.make_precision(self.sell_enter, 2)) +
                    ' buy_break: ' + str(tool.make_precision(self.buy_break, 2)) +
                    ' sell_break: ' + str(tool.make_precision(self.sell_break, 2)))

    def on_bar(self, item: KlineItem):
        bar = self.kline.append(item)
        if bar is None:
            return
        position_side, position_amount = self.order_manager.get_position(self.config.symbol)
        logger.info('open_time: ' + str(bar.open_time) +
                    '|open_price: ' + str(tool.make_precision(bar.open_price, 2)) +
                    '|high: ' + str(tool.make_precision(bar.high, 2)) +
                    '|low: ' + str(tool.make_precision(bar.low, 2)) +
                    '|close_price: ' + str(tool.make_precision(bar.close_price, 2))
                    )
        self.order_manager.show_position(self.config.symbol)
        self.order_manager.show_asset_position(self.config.symbol)
        self.order_manager.cancel_all_order_with_retry(self.config.symbol)
        if bar.open_time.day == item.open_time.day:
            self.day_close = item.close_price
            self.day_low = min(self.day_low, item.low)
            self.day_high = max(self.day_high, item.high)
        else:
            bar = KlineItem(open_price=self.day_open,
                            close_price=self.day_close,
                            high=self.day_high,
                            low=self.day_low)
            logger.info(f'new day: {bar.to_dict()}')
            self.calculate(bar)
            self.day_open = item.open_price
            self.day_high = item.high
            self.day_close = item.close_price
            self.day_low = item.low
        tend_high, tend_low, _ = tool.get_do_chain_value(self.kline)
        if position_side == LONG:
            """平多"""
            self.intra_trade_high = max(self.intra_trade_high, bar.high)
            long_stop = self.intra_trade_high * (1 - self.config.trailing_long / 100)
            self.order_manager.sell(self.config.symbol, long_stop, position_amount)
        elif position_side == SHORT:
            """平空"""
            self.intra_trade_low = min(self.intra_trade_low, bar.low)
            short_stop = self.intra_trade_low * (1 + self.config.trailing_short / 100)
            self.order_manager.cover(self.config.symbol, short_stop, position_amount)
        elif position_side is None:
            self.intra_trade_low = bar.low
            self.intra_trade_high = bar.high
            logger.info(f"tend_low: {tool.make_precision(tend_low, 2)}, "
                        f"tend_high: {tool.make_precision(tend_high, 2)}")
            if tend_high > self.sell_setup:
                long_entry = max(self.buy_break, self.day_high)
                self.order_manager.buy(self.config.symbol, long_entry, self.config.multiplier * self.config.fixed_size)
                self.order_manager.short(self.config.symbol, self.sell_enter, self.config.fixed_size)
            elif tend_low < self.buy_setup:
                short_entry = min(self.sell_break, self.day_low)
                self.order_manager.short(self.config.symbol, short_entry,
                                         self.config.multiplier * self.config.fixed_size)
                self.order_manager.buy(self.config.symbol, self.buy_enter, self.config.fixed_size)
        logger.info(f"当前挂单{self.order_manager.orders}")
