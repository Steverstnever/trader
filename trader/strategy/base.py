import logging
from abc import ABC, abstractmethod
from requests import RequestException

from trader.notifier import Notifier
from trader.store import StrategyStore
from trader.third_party.binance.exceptions import BinanceAPIException


logger = logging.getLogger(__name__)


class StrategyEvent(ABC):
    """
    策略事件
    """


class StrategyContext(ABC):

    @abstractmethod
    def get_notifier(self) -> Notifier:
        """
        获取通知器

        Returns:
            通知器实例
        """

    @abstractmethod
    def get_store(self) -> StrategyStore:
        """
        获取策略存储

        Returns:
            策略存储实例
        """


class Strategy(ABC):

    def __init__(self, context: StrategyContext):
        self.context = context

    @property
    def notifier(self):
        return self.context.get_notifier()

    @property
    def store(self):
        return self.context.get_store()

    @abstractmethod
    def initialize(self):
        """
        初始化
        """

    @abstractmethod
    def handle_event(self, event: StrategyEvent):
        """
        处理事件主程序（会被周期性调用）

        Args:
            event (StrategyEvent): 事件

        Returns:
            None
        """

    def handle_exception(self, e: Exception, event: StrategyEvent):
        """
        策略异常处理

        Args:
            e (Exception): 发生的异常
            event (StrategyEvent): 发生异常时策略正在处理的事件

        Returns:

        """
        if isinstance(e, RequestException):
            logger.exception(e)
            self.notifier.notify(f"在处理 {event} 时发生了 requests 相关的异常：{e}")
        elif isinstance(e, BinanceAPIException):
            logger.exception(e)
            self.notifier.notify(f"在处理 {event} 时发生了 BinanceAPI 相关的异常：{e}")
        elif isinstance(e, Exception):
            logger.exception(e)
            self.notifier.notify(f"在处理 {event} 时发生了未知异常：{e}，策略做退出处理！")
            self.handle_safely_quit()
            raise e

    @abstractmethod
    def handle_safely_quit(self):
        """
        当发生不能处理的异常时，安全退出
        """


class StrategyRunner(ABC):
    def __init__(self, strategy: Strategy):
        self.strategy = strategy

    @abstractmethod
    def run(self):
        """运行执行期"""


class StrategyApp:
    def __init__(self, strategy: Strategy, runner: StrategyRunner):
        self.strategy = strategy
        self.runner = runner

    def run(self):
        self.runner.run()
