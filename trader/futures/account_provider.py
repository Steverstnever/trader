from abc import ABC, abstractmethod
from decimal import Decimal

from trader.futures.types import ContractPair


class AccountProvider(ABC):

    @abstractmethod
    def get_balance_by_symbol(self, asset_symbol: str) -> (Decimal, Decimal):
        """"""

    def get_cash_balance(self, contract_pair: ContractPair) -> (Decimal, Decimal):
        return self.get_balance_by_symbol(contract_pair.cash_symbol)

    def get_asset_balance(self, contract_pair: ContractPair) -> (Decimal, Decimal):
        return self.get_balance_by_symbol(contract_pair.asset_symbol)

    def get_total_cash_qty(self, contract_pair: ContractPair) -> Decimal:
        free_qty, locked_qty = self.get_cash_balance(contract_pair)
        return free_qty + locked_qty

    def get_total_asset_qty(self, contract_pair: ContractPair) -> Decimal:
        free_qty, locked_qty = self.get_asset_balance(contract_pair)
        return free_qty + locked_qty
