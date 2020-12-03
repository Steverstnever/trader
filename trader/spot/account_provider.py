from abc import ABC, abstractmethod
from decimal import Decimal

from trader.spot.types import CoinPair


class AccountProvider(ABC):

    @abstractmethod
    def get_balance_by_symbol(self, asset_symbol: str) -> (Decimal, Decimal):
        """
        获取币种余额

        Args:
            asset_symbol (str): 币种

        Returns:
            （可用数量, 冻结数量）
        """

    def get_cash_balance(self, coin_pair: CoinPair) -> (Decimal, Decimal):
        """
        获取现金余额

        Args:
            coin_pair (CoinPair): 币对

        Returns:
            现金可用数量，现金冻结余额
        """
        return self.get_balance_by_symbol(coin_pair.cash_symbol)

    def get_asset_balance(self, coin_pair: CoinPair) -> (Decimal, Decimal):
        """
        获取资产余额

        Args:
            coin_pair (CoinPair): 币对

        Returns:
            资产可用数量，资产冻结余额
        """
        return self.get_balance_by_symbol(coin_pair.asset_symbol)

    def get_total_cash_qty(self, coin_pair: CoinPair) -> Decimal:
        """
        获取现金总数（可用+冻结）

        Args:
            coin_pair (CoinPair): 币对

        Returns:
            现金总数（可用+冻结）
        """
        free_qty, locked_qty = self.get_cash_balance(coin_pair)
        return free_qty + locked_qty

    def get_total_asset_qty(self, coin_pair: CoinPair) -> Decimal:
        """
        获取资产总数（可用+冻结）

        Args:
            coin_pair (CoinPair): 币对

        Returns:
            资产总数（可用+冻结）
        """
        free_qty, locked_qty = self.get_asset_balance(coin_pair)
        return free_qty + locked_qty
