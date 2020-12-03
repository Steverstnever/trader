from abc import ABC, abstractmethod
from typing import List

from trader.spot.types.account_snapshot import AccountSnapshot
from trader.spot.types.order_types import Trade, Order


class StrategyStore(ABC):
    """
    策略存储
    """

    @abstractmethod
    def save_trades(self, trades: List[Trade]):
        """
        保存成交记录列表

        Args:
            trades (List[Trade]): 成交记录列表
        """

    @abstractmethod
    def save_order(self, order: Order):
        """
        保存订单记录（包含已经取消、完成的、部分完成……订单）

        Args:
            order (Order): 订单
        """

    @abstractmethod
    def save_account_snapshot(self, account_snapshot: AccountSnapshot):
        """
        保存账户快照

        Args:
            account_snapshot (AccountSnapshot): 账户快照
        """

    @abstractmethod
    def load_trades(self, limit: int = None) -> List[Trade]:
        """
        装载成交记录，从最新到最旧

        Args:
            limit (int): 最多返回数量

        Returns:
            成交记录列表
        """

    @abstractmethod
    def get_last_trade_id(self) -> str:
        """
        最新成交记录id

        Returns:
            最新成交记录id
        """
