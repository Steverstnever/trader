import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path

from trader.credentials import Credentials
from trader.futures.api.futures_api import FuturesApi
from trader.futures.types import Bar, ContractPair, DeliveryContractPair, PerpetualContractPair, PositionSide
from trader.notifier import Notifier, LoggerNotifier
from trader.futures.api.exchange import Exchange, exchange_map
from trader.store import StrategyStore
from trader.strategy.base import Strategy, StrategyEvent, StrategyContext, StrategyApp
from trader.strategy.rbreaker.rbreaker_strategy_adapter import RBreakerStrategyAdapter
from trader.strategy.runner.timer import TimerEvent, TimerRunner
from trader.store.sqlalchemy_store import SqlalchemyStrategyStore


logger = logging.getLogger('r-breaker')
binance_order_not_exit = -2013


class RBreakerTimerIds(Enum):
    """
    网格策略用到的 timer-id
    """
    BAR_TICKER = timedelta(seconds=60)  # 每个一分钟获取一次k线
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
        with path.open() as f:
            conf = json.load(f)
        asset, cash, delivery_time = conf['asset'], conf['cash'], conf['delivery_time']
        if delivery_time == 'PERP':  # 永续合约
            contract_pair = PerpetualContractPair(asset, cash)
        else:
            contract_pair = DeliveryContractPair(asset, cash, int(delivery_time))

        return RBreakerConfig(
            exchange=exchange_map[conf['exchange']],
            contract_pair=contract_pair,
            kline_interval=conf['kline_interval'],
            do_chain_window_size=conf['do_chain_window_size'],
            setup_coef=Decimal(conf['setup_coef']),
            enter_coef_1=Decimal(conf['enter_coef_1']),
            enter_coef_2=Decimal(conf['enter_coef_2']),
            break_coef=Decimal(conf['break_coef']),
            multiplier=Decimal(conf['multiplier']),
            fixed_size=Decimal(conf['fixed_size']),
            trailing_long=Decimal(conf['trailing_long']),
            trailing_short=Decimal(conf['trailing_short']),
            order_query_interval=timedelta(seconds=conf['order_query_interval']),
            order_cancel_timeout=timedelta(seconds=conf['order_cancel_timeout'])
        )


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
        self.contract_pair: ContractPair = conf.contract_pair
        self.adapter = RBreakerStrategyAdapter(futures_api,
                                               order_query_interval=self.config.order_query_interval,
                                               order_cancel_timeout=self.config.order_cancel_timeout)
        self.instrument_info = self.adapter.get_instrument_info(self.contract_pair)

    def initialize(self):
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

    def handle_bar_ticker(self):
        kline = self.adapter.klines(self.contract_pair, self.config.kline_interval,
                                    limit=self.config.do_chain_window_size)
        bar, new_bar = kline[-2], kline[-1]
        logger.info('open_time: ' + str(bar.open_time) +
                    '|open_price: ' + str(self.instrument_info.quantize_price(bar.open_price)) +
                    '|high: ' + str(self.instrument_info.quantize_price(bar.high)) +
                    '|low: ' + str(self.instrument_info.quantize_price(bar.low)) +
                    '|close_price: ' + str(self.instrument_info.quantize_price(bar.close_price))
                    )
        position = self.get_position()
        if position:
            logger.info(f"当前持仓: {position}")
        asset = self.adapter.get_asset_by_symbol(self.contract_pair.cash_symbol)
        logger.info(f"|{asset.asset_symbol}｜账户余额:{asset.wallet_balance}"
                    f"|保证金余额:{asset.margin_balance}"
                    f"|可用余额:{asset.available_balance}|")

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
        tend_high, tend_low, _ = get_do_chain_value(kline)
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
        if isinstance(event, TimerEvent):
            if event.timer_id == RBreakerTimerIds.BAR_TICKER:
                self.handle_bar_ticker()
            elif event.timer_id == RBreakerTimerIds.SAVE_TRADES:
                self.handle_save_trades()
            elif event.timer_id == RBreakerTimerIds.SAVE_ACCOUNT_SNAPSHOT:
                self.handle_save_account_snapshot()

    def handle_save_trades(self):
        """"""

    def handle_save_account_snapshot(self):
        """"""

    def handle_safely_quit(self):
        safely_run('取消所有未完成订单', self.adapter.cancel_all_orders, self.contract_pair)
        safely_run('保存最新交易记录', self.handle_save_trades)
        safely_run('保存账户快照', self.handle_save_account_snapshot)

    def handle_exception(self, e: Exception, event: StrategyEvent):
        super().handle_exception(e, event=event)


def safely_run(name: str, f: callable, *args, **kwargs):
    try:
        return f(*args, **kwargs)
    except Exception as e:
        logger.error(f"【安全退出】{name}时发生异常：", e)


class RBreakerStrategyApp(StrategyApp):
    def __init__(self, config: RBreakerConfig, credentials: Credentials):
        notifier = LoggerNotifier()
        store = SqlalchemyStrategyStore("sqlite:///perf.sqlite")  # TODO: 配置
        context = RBreakerStrategyContext(notifier=notifier, store=store)
        futures_api = config.exchange.create_coin_future_api(credentials=credentials)
        strategy = RBreakerStrategy(config, context, futures_api)
        runner = TimerRunner(strategy)
        for time_id in RBreakerTimerIds:
            runner.add_timer(time_id, time_id.value)
        super().__init__(strategy, runner)
