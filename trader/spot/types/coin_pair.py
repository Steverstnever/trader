class CoinPair:
    """
    币对
    """

    SEPARATOR = '$'

    def __init__(self, asset_symbol: str, cash_symbol: str):
        """
        构造函数

        Args:
            asset_symbol (str): 资产币种、本位币，比如：BTC、ETH，全部大写
            cash_symbol (str): 现金币种、报价币，比如：USDT，全部大写
        """
        self.asset_symbol = asset_symbol
        self.cash_symbol = cash_symbol

    @property
    def symbol(self):
        """
        返回交易所无关的币对标识符

        Returns:
            （交易所无关的）币对标识符
        """
        return f"{self.asset_symbol}{self.SEPARATOR}{self.cash_symbol}"

    @classmethod
    def from_symbol(cls, symbol: str) -> "CoinPair":
        asset_symbol, cash_symbol = symbol.split(cls.SEPARATOR, 2)
        if not (isinstance(asset_symbol, str) and isinstance(cash_symbol, str)):
            raise RuntimeError(f"非法的币对标识符: {symbol}")
        return CoinPair(asset_symbol=asset_symbol, cash_symbol=cash_symbol)

    def __str__(self):
        return self.symbol

    def __repr__(self):
        return f"CoinPair({self.symbol})"
