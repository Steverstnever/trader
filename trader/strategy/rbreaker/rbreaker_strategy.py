import logging
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from enum import Enum

from trader.futures.types import ContractPair, Bar, Kline, PositionSide
from trader.notifier import Notifier, LoggerNotifier
from trader.spot.api.exchange import Exchange
from trader.store import StrategyStore
from trader.strategy.base import StrategyEvent, StrategyContext
from trader.strategy.rbreaker.rbreaker_strategy_adapter import RBreakerStrategyAdapter

from trader.strategy.base import Strategy
from trader.futures.api.futures_api import FuturesApi


logger = logging.getLogger('r-breaker')
binance_order_not_exit = -2013


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
    kline_interval: str
    do_chain_window_size: int
    setup_coef: Decimal
    enter_coef_1: Decimal
    enter_coef_2: Decimal
    break_coef: Decimal
    multiplier: Decimal
    fixed_size: Decimal
    trailing_long: Decimal
    trailing_short: Decimal
    order_query_interval: timedelta
    order_cancel_timeout: timedelta

    @classmethod
    def load_from_json(cls, path: Path):
        """"""


class Reporter:
    def __init__(self, futures_api):
        self.futures_api = futures_api

    def show_position(self, contract_pair: ContractPair):
        """"""

    def show_asset_position(self, contract_pair: ContractPair):
        """"""


def get_do_chain_value(kline):
    """计算唐奇安通道值"""
    tend_high = max([item.high for item in kline])
    tend_low = min([item.low for item in kline])
    tend_center = (tend_high+tend_low)/2
    return tend_high, tend_low, tend_center


class RBreakerStrategy(Strategy):

    def __init__(self, conf: RBreakerConfig, context: RBreakerStrategyContext, futures_api: FuturesApi):
        super(RBreakerStrategy, self).__init__(context)
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

        self.config: RBreakerConfig = conf
        self.contract_pair = conf.contract_pair
        self.kline = Kline(conf.do_chain_window_size)
        self.instrument_info = self.adapter.get_instrument_info(self.contract_pair)
        self.reporter = Reporter(futures_api)
        self.adapter = RBreakerStrategyAdapter(futures_api,
                                               order_query_interval=self.config.order_query_interval,
                                               order_cancel_timeout=self.config.order_cancel_timeout)

    def initialize(self):
        k = self.adapter.klines(self.contract_pair, self.config.kline_interval, limit=self.config.do_chain_window_size)
        for item in k:
            self.kline.append(item)

        k = self.adapter.klines(self.contract_pair, interval='1d', limit=2)
        last_day_bar, today_bar = k[0], k[1]
        self.calculate(last_day_bar)
        self.day_open = today_bar.open_price
        self.day_low = today_bar.low
        self.day_high = today_bar.high
        self.day_close = today_bar.close_price

    def get_position(self):
        rv = self.adapter.get_position(self.contract_pair)
        return rv[0] if rv else None  # todo 目前只考虑单向成交，不考虑多空同时成交

    def calculate(self, bar: Bar):
        self.buy_setup = bar.low - self.config.setup_coef * (bar.high - bar.close_price)  # 观察买入价
        self.sell_setup = bar.high + self.config.setup_coef * (bar.close_price - bar.low)  # 观察卖出价
        self.buy_enter = (self.config.enter_coef_1 / 2) * (
                    bar.high + bar.low) - self.config.enter_coef_2 * bar.high  # 反转买入价
        self.sell_enter = (self.config.enter_coef_1 / 2) * (
                    bar.high + bar.low) - self.config.enter_coef_2 * bar.low  # 反转卖出价
        self.buy_break = self.sell_setup + self.config.break_coef * (self.sell_setup - self.buy_setup)  # 突破买入价
        self.sell_break = self.buy_setup - self.config.break_coef * (self.sell_setup - self.buy_setup)  # 突破卖出价
        logger.info('buy_setup: ' + str(self.instrument_info.quantize_price(self.buy_setup)) +
                    ' sell_setup: ' + str(self.instrument_info.quantize_price(self.sell_setup)) +
                    ' buy_enter: ' + str(self.instrument_info.quantize_price(self.buy_enter)) +
                    ' sell_enter: ' + str(self.instrument_info.quantize_price(self.sell_enter)) +
                    ' buy_break: ' + str(self.instrument_info.quantize_price(self.buy_break)) +
                    ' sell_break: ' + str(self.instrument_info.quantize_price(self.sell_break)))

    def on_bar(self, new_bar: Bar):
        bar = self.kline.append(new_bar)
        if bar is None:
            return
        position = self.get_position()
        logger.info('open_time: ' + str(bar.open_time) +
                    '|open_price: ' + str(self.instrument_info.quantize_price(bar.open_price)) +
                    '|high: ' + str(self.instrument_info.quantize_price(bar.high)) +
                    '|low: ' + str(self.instrument_info.quantize_price(bar.low)) +
                    '|close_price: ' + str(self.instrument_info.quantize_price(bar.close_price))
                    )
        self.reporter.show_position(self.contract_pair)
        self.reporter.show_asset_position(self.contract_pair)
        self.adapter.cancel_all_orders(self.contract_pair)
        if bar.open_time.day == new_bar.open_time.day:
            self.day_close = new_bar.close_price
            self.day_low = min(self.day_low, new_bar.low)
            self.day_high = max(self.day_high, new_bar.high)
        else:
            bar = Bar(open_price=self.day_open,
                      close_price=self.day_close,
                      high=self.day_high,
                      low=self.day_low,
                      volume=Decimal('0'),  # 不关注volume
                      open_time=new_bar.open_time-timedelta(days=1))  # 不关注open time
            logger.info(f'new day: {bar.to_dict()}')
            self.calculate(bar)
            self.day_open = new_bar.open_price
            self.day_high = new_bar.high
            self.day_close = new_bar.close_price
            self.day_low = new_bar.low
        tend_high, tend_low, _ = get_do_chain_value(self.kline)
        if position and position.position_side == PositionSide.LONG:
            """平多"""
            self.intra_trade_high = max(self.intra_trade_high, bar.high)
            long_stop = self.intra_trade_high * (1 - self.config.trailing_long / 100)
            self.adapter.get_order_executor().sell(self.config.contract_pair,
                                                   price=long_stop,
                                                   stop_price=long_stop,
                                                   qty=position.position_amt)
        elif position and position.position_side == PositionSide.SHORT:
            """平空"""
            self.intra_trade_low = min(self.intra_trade_low, bar.low)
            short_stop = self.intra_trade_low * (1 + self.config.trailing_short / 100)
            self.adapter.get_order_executor().cover(self.config.contract_pair,
                                                    price=short_stop,
                                                    stop_price=short_stop,
                                                    qty=position.position_amt)
        elif position is None:
            self.intra_trade_low = bar.low
            self.intra_trade_high = bar.high
            logger.info(f"tend_low: {self.instrument_info.quantize_price(tend_low)}, "
                        f"tend_high: {self.instrument_info.quantize_price(tend_high)}")
            current_orders = []
            if tend_high > self.sell_setup:
                long_entry = max(self.buy_break, self.day_high)
                order1 = self.adapter.get_order_executor().buy(self.contract_pair,
                                                               price=long_entry,
                                                               stop_price=long_entry,
                                                               qty=self.config.multiplier * self.config.fixed_size)
                order2 = self.adapter.get_order_executor().short(self.contract_pair,
                                                                 price=self.sell_enter,
                                                                 stop_price=self.sell_enter,
                                                                 qty=self.config.fixed_size)
                current_orders = [order1, order2]
            elif tend_low < self.buy_setup:
                short_entry = min(self.sell_break, self.day_low)
                order1 = self.adapter.get_order_executor().short(self.contract_pair,
                                                                 price=short_entry,
                                                                 stop_price=short_entry,
                                                                 qty=self.config.multiplier * self.config.fixed_size)
                order2 = self.adapter.get_order_executor().buy(self.contract_pair,
                                                               price=self.buy_enter,
                                                               stop_price=self.buy_enter,
                                                               qty=self.config.fixed_size)
                current_orders = [order1, order2]
            logger.info(f"当前挂单{current_orders}")

    def handle_event(self, event: StrategyEvent):
        pass

    def handle_safely_quit(self):
        pass
