import logging
import json
from dataclasses import dataclass
from datetime import timedelta, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

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
from trader.strategy.grid.grid_generators import ConfigGridGenerator
from trader.strategy.runner.timer import TimerEvent, TimerRunner
from trader.strategy.trade_crawler import TradeCrawler

log = logging.getLogger("grid-strategy")


class GridTimerIds(Enum):
    """
    网格策略用到的 timer-id
    """
    BOOK_TICKER = timedelta(seconds=1)  # 每秒钟查看一次 book ticker
    SAVE_TRADES = timedelta(seconds=5)  # 每分钟保存一次最新成交记录
    SAVE_ACCOUNT_SNAPSHOT = timedelta(hours=0.5)  # 每半小时存储一下资产情况


@dataclass
class GridStrategyConfig:
    exchange: Exchange  # 交易所
    coin_pair: CoinPair  # 币对
    generator: GridGenerator  # 网格生成器

    enter_trigger_price: Decimal = Decimal('0')  # 入场触发价
    stop_on_exit: bool = False  # 出场后策略停止
    level_min_profit: Decimal = Decimal(0.005)  # 每格最小收益率（网格如果不符合此设置要求则拒绝执行）

    order_query_interval: timedelta = timedelta(seconds=1)  # 下单后查询订单状态的间隔
    order_cancel_timeout: timedelta = timedelta(seconds=5)  # 每次下限价（gtc）订单的等待时间，超时后如果未完全成交则 cancel

    @classmethod
    def load_from_json(cls, path: Path) -> "GridStrategyConfig":
        """
        从 json 文件中加载配置
        Args:
            path (Path): 配置文件路径

        Returns:
            网格策略的配置

        文件内容example:
        {
            "exchange":"BINANCE",
            "generator":"/path/grid.json",
            "coin_pair":"BTC$USDT",
            "enter_trigger_price":"0", option
            "stop_on_exit":true, option
            "level_min_profit":"0.005", option
            "order_query_interval":1, option
            "order_cancel_timeout":5 option
        }
        """
        content = json.loads(path.read_bytes())
        params = dict()
        try:
            params["exchange"] = getattr(Exchange, content["exchange"])
        except AttributeError:
            raise RuntimeError("exchange is not existed")
        params["coin_pair"] = CoinPair.from_symbol(content["coin_pair"])
        params["generator"] = ConfigGridGenerator(Path(content["generator"]))
        if content.get("enter_trigger_price"):
            params["enter_trigger_price"] = Decimal(content["enter_trigger_price"])
        if content.get("stop_on_exit") is not None:
            params["stop_on_exit"] = content["stop_on_exit"]
        if content.get("level_min_profit"):
            level_min_profit = Decimal(content["level_min_profit"])
        if content.get("order_query_interval") is not None:
            params["order_query_interval"] = timedelta(seconds=content["order_query_interval"])
        if content.get("order_cancel_timeout") is not None:
            params["order_cancel_timeout"] = timedelta(seconds=content["order_cancel_timeout"])
        return cls(**params)


class GridStrategyContext(StrategyContext):

    def __init__(self, notifier: Notifier, store: StrategyStore):
        self.notifier = notifier if notifier is not None else LoggerNotifier()
        self.store = store

    def get_notifier(self) -> Notifier:
        return self.notifier

    def get_store(self) -> StrategyStore:
        return self.store


class GridStrategy(Strategy):

    def __init__(self, config: GridStrategyConfig, context: GridStrategyContext, spot_api: SpotApi):
        super().__init__(context)

        self.config = config
        self.coin_pair = self.config.coin_pair
        self.adapter = GridStrategyAdapter(spot_api,
                                           order_query_interval=self.config.order_query_interval,
                                           order_cancel_timeout=self.config.order_cancel_timeout,
                                           )
        self.instrument_info = self.adapter.get_instrument_info(self.coin_pair)
        self.position_manager = GridPositionManager(config.generator, config.level_min_profit)
        self.cash_qty, _ = self.adapter.get_cash_balance(self.coin_pair)

        # 成交记录爬取器
        self.trade_crawler = TradeCrawler(self.coin_pair, self.adapter, self.store)

        # 如果设置了触发价，则当前缺省处于未触发状态，当价格高于触发价时，不执行网格交易
        # 除非网格低于触发价以后，状态会调整未触发状态
        self.triggered = config.enter_trigger_price.is_zero()

        # 是否策略已经停止
        self.stopped = False

        # 需要重新初始化（比如订单取消（cancel_order）出错的时候）
        self._require_reinitialized = False

    def initialize(self):
        if self._require_reinitialized:
            log.info("当前状态出错，需要取消所有订单并重新初始化")
            self.adapter.cancel_all_orders(self.coin_pair)
            # 本次初始化完成，不需要再次初始化
            self._require_reinitialized = False

        log.info(f"【网格策略】初始化".center(80, '*'))
        self.position_manager.clear_positions()  # 清除所有现有网格仓位
        asset_qty, _ = self.adapter.get_asset_balance(self.coin_pair)
        log.info(f"资产【{self.coin_pair.asset_symbol}】当前数量：{asset_qty}, 使用这些资产初始化网格")
        self.position_manager.bought_position(asset_qty)
        self.position_manager.log_levels()

        self.cash_qty, _ = self.adapter.get_cash_balance(self.coin_pair)
        log.info(f"当前可用现金【{self.coin_pair.cash_symbol}】数量为：{self.cash_qty}")
        log.info(f"【网格策略】初始化完成".center(80, '^'))

    def handle_event(self, event: StrategyEvent):
        if isinstance(event, TimerEvent):
            if event.timer_id == GridTimerIds.BOOK_TICKER:
                self.handle_book_ticker()
            elif event.timer_id == GridTimerIds.SAVE_TRADES:
                self.handle_save_trades()
            elif event.timer_id == GridTimerIds.SAVE_ACCOUNT_SNAPSHOT:
                self.handle_save_account_snapshot()

    def _handle_triggered_status(self, book_ticker: BookTicker) -> bool:
        """
        处理触发（入场）状态

        Args:
            book_ticker (BookTicker): 最优价格

        Returns:
            True 代表已经触发(已经入场), False 未触发（此时策略不正式进场）
        """
        if not self.triggered:
            # 为触发状态时，判断当前最优卖价是否低于触发入场价（是否满足触发条件　）
            if book_ticker.ask1_price < self.config.enter_trigger_price:
                log.info(f"当前最优卖价 {book_ticker.ask1_price} 低于触发价格，进入触发状态，正式进场")
                self.triggered = True
            else:
                log.info(f"当前价格未达到触发价格 {self.config.enter_trigger_price}，暂不进场")
                return False

        return True

    def _handle_stop_status(self, book_ticker: BookTicker) -> bool:
        """
        处理离场停止状态

        Args:
            book_ticker (BookTicker): 当前最优报价

        Returns:
            True 代表已经离场（停止）, False 代表尚未离场（正常运行）
        """
        if self.stopped:
            log.info(f"由于设置了突破后停止，策略已经停止")
            return True

        if not self.stopped and self.config.stop_on_exit:
            if book_ticker.ask1_price < self.position_manager.support_price and self.is_full():
                self.notifier.notify(f"当前最优买价 {book_ticker.ask1_price}：向下突破支撑位，并且仓位已满，策略停止")
                self.stopped = True
                return True
            if book_ticker.bid1_price > self.position_manager.resistance_price and self.is_empty():
                self.notifier.notify(f"当前最优报价 {book_ticker.bid1_price} 向上突破阻力位，并且仓位已空，策略停止")
                self.stopped = True
                return True
        return False

    def is_empty(self):
        return self.instrument_info.quantize_qty(self.position_manager.total_position).is_zero()

    def is_full(self):
        total_position_delta = self.position_manager.total_max_position - self.position_manager.total_position
        return self.instrument_info.quantize_qty(total_position_delta) <= self.instrument_info.min_qty

    def _handle_buy(self, book_ticker: BookTicker):
        """
        处理买入

        Args:
            book_ticker (BookTicker): 当前最优价
        """
        # 买入比卖一价格高的网格
        buy_qty = self.position_manager.get_positions_to_buy(book_ticker.ask1_price)
        buy_qty = self.instrument_info.quantize_qty(min(buy_qty, book_ticker.ask1_qty))
        if self.instrument_info.is_valid_notional(book_ticker.ask1_price, buy_qty):
            log.info(f"开始买入，限价：价格 {book_ticker.ask1_price}, 数量 {buy_qty}")
            order: Order = self.adapter.get_order_executor().buy(self.coin_pair, book_ticker.ask1_price, buy_qty)
            log.info(f"买入完成，成交数量 {order.filled_qty}")
            self.position_manager.bought_position(order.filled_qty)
            # 保存订单记录
            self.store.save_order(order)
            self.position_manager.log_levels()
        else:
            if not buy_qty.is_zero():
                log.warning(
                    f"当前可买数量 {buy_qty}，当前最优卖价 {book_ticker.ask1_price}, "
                    f"交易额 {buy_qty * book_ticker.ask1_price} 不满足商品最低可交易额 {self.instrument_info.min_notional}")

    def _handle_sell(self, book_ticker: BookTicker):
        """
        处理卖出

        Args:
            book_ticker (BookTicker): 当前最优报价
        """
        # 卖出比买一价格低的网格
        sell_qty = self.position_manager.get_positions_to_sell(book_ticker.bid1_price)
        sell_qty = self.instrument_info.quantize_qty(min(sell_qty, book_ticker.bid1_qty))
        if self.instrument_info.is_valid_notional(book_ticker.bid1_price, sell_qty):
            log.info(f"开始卖出，限价：价格 {book_ticker.bid1_price}, 数量 {sell_qty}")
            order: Order = self.adapter.get_order_executor().sell(self.coin_pair, book_ticker.bid1_price, sell_qty)
            log.info(f"卖出完成，成交数量 {order.filled_qty}")
            self.position_manager.sold_position(order.filled_qty)
            # 保存订单记录
            self.store.save_order(order)
            self.position_manager.log_levels()
        else:
            if not sell_qty.is_zero():
                log.warning(
                    f"当前可卖数量 {sell_qty}，当前最优买价 {book_ticker.bid1_price}, "
                    f"交易额 {sell_qty * book_ticker.bid1_price} 不满足商品最低可交易额 {self.instrument_info.min_notional}")

    def handle_book_ticker(self):
        log.debug("获取最优报价".center(80, '-'))
        book_ticker = self.adapter.get_book_ticker(self.coin_pair)
        log.info(f"最优报价 {book_ticker.compact_display_str}")

        # 如果出现取消订单等出错，则重新初始化网格
        if self._require_reinitialized:
            self.initialize()

        # 已经触发入场 并且 没有离场停止时，尝试买入，尝试卖出
        if self._handle_triggered_status(book_ticker) and not self._handle_stop_status(book_ticker):
            self._handle_buy(book_ticker)
            self._handle_sell(book_ticker)

    def handle_save_trades(self):
        log.info("保存最新成交记录")
        self.trade_crawler.crawl()

    def handle_save_account_snapshot(self):
        log.info(" 开始保存资产快照 ".center(80, '$'))
        asset_qty = self.adapter.get_total_asset_qty(self.coin_pair)
        cash_qty = self.adapter.get_total_cash_qty(self.coin_pair)

        book_ticker = self.adapter.get_book_ticker(self.coin_pair)
        account_snapshot = AccountSnapshot(
            asset=self.coin_pair.asset_symbol,
            asset_qty=asset_qty,
            cash=self.coin_pair.cash_symbol,
            cash_qty=cash_qty,
            price=book_ticker.avg_price,
            timestamp=datetime.now()
        )
        self.store.save_account_snapshot(account_snapshot)
        self.notifier.notify(f"资产市值快照：{account_snapshot.total_cash_qty} {account_snapshot.cash} "
                             f"@ {account_snapshot.timestamp}")
        log.info(" 资产快照保存完成 ".center(80, '^'))

    def handle_safely_quit(self):
        safely_run('取消所有未完成订单', self.adapter.cancel_all_orders, self.coin_pair)
        safely_run('保存最新交易记录', self.handle_save_trades)
        safely_run('保存账户快照', self.handle_save_account_snapshot)

    def handle_exception(self, e: Exception, event: StrategyEvent):
        super(GridStrategy, self).handle_exception(e, event=event)
        if isinstance(e, OrderNotCancelledError):  # 订单没有被正确取消(cancel_order 出错)
            self._require_reinitialized = True


def safely_run(name: str, f: callable, *args, **kwargs):
    try:
        return f(*args, **kwargs)
    except Exception as e:
        log.error(f"【安全退出】{name}时发生异常：", e)


class GridStrategyApp(StrategyApp):
    def __init__(self, config: GridStrategyConfig, credentials: Credentials):
        # 创建上下文
        notifier = LoggerNotifier()
        store = SqlalchemyStrategyStore("sqlite:///perf.sqlite")  # TODO: 配置
        context = GridStrategyContext(notifier=notifier, store=store)

        # 创建现货接口
        spot_api = config.exchange.create_spot_api(credentials=credentials)

        # 创建策略
        strategy = GridStrategy(config=config, context=context, spot_api=spot_api)
        runner = TimerRunner(strategy)
        for time_id in GridTimerIds:
            runner.add_timer(time_id, time_id.value)
        super().__init__(strategy, runner)
