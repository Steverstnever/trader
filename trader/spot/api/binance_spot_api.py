import logging
import os
import time
from datetime import datetime
from decimal import Decimal
from typing import List

from trader.credentials import Credentials
from trader.spot.api.spot_api import SpotApi
from trader.spot.types import CoinPair, OrderSide, TimeInForce, SpotInstrumentInfo, Trade
from trader.spot.types.book_ticker import BookTicker
from trader.spot.types.kline import KlinePeriod, Bar
from trader.spot.types.order_types import Order, OrderStatus, OrderType
from trader.third_party.binance.client import Client
from trader.third_party.binance.exceptions import BinanceAPIException
from trader.utils import parse_decimal

log = logging.getLogger("binance-spot-api")


# 此处设计了可重试模式。
# 【注意】️不能将此模式用于 下订单，此模式仅能用于查询和取消订单这些 "幂等"方法上！ ⚠️
#
# 参见：
# https://dev.binance.vision/t/faq-error-message-order-does-not-exist/46

class RetryBinanceClient:
    def __init__(self, client, max_retries=3, retry_interval=0.3):
        self._client = client
        self.max_retries = max_retries
        self.retry_interval = retry_interval

    @staticmethod
    def __safely_retry(func, max_retries, retry_interval):
        def wrapper(*args, **kwargs):
            num_tries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except BinanceAPIException as e:
                    if e.code == -2013 and num_tries < max_retries:  # -2013 订单不存在
                        log.debug(f'safely_retrying {func.__name__}, {args}, {kwargs}')
                        num_tries += 1
                        time.sleep(retry_interval)
                    else:
                        raise e

        return wrapper

    def __getattr__(self, name, *args, **kwargs):
        attr = getattr(self._client, name)
        if callable(attr):
            return self.__safely_retry(attr, self.max_retries, self.retry_interval)
        else:
            return attr


class BinanceSpotApi(SpotApi):

    def __init__(self, credentials: Credentials = None):
        super().__init__(credentials)
        # 针对慢速网格（通过代理访问服务器）时的签名接口时间戳的调整
        slow_network_adjust_ms = os.getenv("BINANCE_SLOW_NETWORK_ADJUST_MS", 1000)

        credentials = credentials if credentials is not None else Credentials.create_blank_credentials()
        self.client = Client(api_key=credentials.api_key,
                             api_secret=credentials.secret_key,
                             slow_network_adjust_ms=slow_network_adjust_ms)

    @staticmethod
    def _coin_pair_to_symbol(coin_pair: CoinPair) -> str:
        """
        将 coin_pair 转换为币安的格式

        Returns:
            币安格式的币对标识符，比如：LTCBTC，ETHBTC
        """
        return coin_pair.asset_symbol + coin_pair.cash_symbol

    def get_instrument_info(self, coin_pair: CoinPair) -> SpotInstrumentInfo:
        log.debug(f"get_instrument_info {coin_pair}")
        symbol = self._coin_pair_to_symbol(coin_pair)
        resp = self.client.get_symbol_info(symbol=symbol)
        # 响应格式：
        # {'baseAsset': 'BNB',
        #  'baseAssetPrecision': 8,
        #  'baseCommissionPrecision': 8,
        #  'filters': [{'filterType': 'PRICE_FILTER',
        #               'maxPrice': '100000.00000000',
        #               'minPrice': '0.00010000',
        #               'tickSize': '0.00010000'},
        #              {'avgPriceMins': 5,
        #               'filterType': 'PERCENT_PRICE',
        #               'multiplierDown': '0.2',
        #               'multiplierUp': '5'},
        #              {'filterType': 'LOT_SIZE',
        #               'maxQty': '900000.00000000',
        #               'minQty': '0.00100000',
        #               'stepSize': '0.00100000'},
        #              {'applyToMarket': True,
        #               'avgPriceMins': 5,
        #               'filterType': 'MIN_NOTIONAL',
        #               'minNotional': '10.00000000'},
        #              {'filterType': 'ICEBERG_PARTS', 'limit': 10},
        #              {'filterType': 'MARKET_LOT_SIZE',
        #               'maxQty': '28339.62586752',
        #               'minQty': '0.00000000',
        #               'stepSize': '0.00000000'},
        #              {'filterType': 'MAX_NUM_ORDERS', 'maxNumOrders': 200},
        #              {'filterType': 'MAX_NUM_ALGO_ORDERS', 'maxNumAlgoOrders': 5}],
        #  'icebergAllowed': True,
        #  'isMarginTradingAllowed': True,
        #  'isSpotTradingAllowed': True,
        #  'ocoAllowed': True,
        #  'orderTypes': ['LIMIT',
        #                 'LIMIT_MAKER',
        #                 'MARKET',
        #                 'STOP_LOSS_LIMIT',
        #                 'TAKE_PROFIT_LIMIT'],
        #  'permissions': ['SPOT', 'MARGIN'],
        #  'quoteAsset': 'USDT',
        #  'quoteAssetPrecision': 8,
        #  'quoteCommissionPrecision': 8,
        #  'quoteOrderQtyMarketAllowed': True,
        #  'quotePrecision': 8,
        #  'status': 'TRADING',
        #  'symbol': 'BNBUSDT'}
        if resp['status'] != 'TRADING':
            raise RuntimeError(f"指定币对不能交易：{symbol}")

        result = SpotInstrumentInfo(coin_pair=coin_pair,
                                    min_price_size=Decimal(),
                                    min_qty_size=Decimal())
        for symbol_filter in resp['filters']:
            if symbol_filter['filterType'] == 'PRICE_FILTER':
                result.min_price_size = parse_decimal(symbol_filter['tickSize'])
                result.min_price = parse_decimal(symbol_filter['minPrice'])
                result.max_price = parse_decimal(symbol_filter['maxPrice'])
            elif symbol_filter['filterType'] == 'LOT_SIZE':
                result.min_qty_size = parse_decimal(symbol_filter['stepSize'])
                result.min_qty = parse_decimal(symbol_filter['minQty'])
                result.max_qty = parse_decimal(symbol_filter['maxQty'])
            elif symbol_filter['filterType'] == 'MIN_NOTIONAL':
                result.min_notional = parse_decimal(symbol_filter['minNotional'])
        return result

    def get_book_ticker(self, coin_pair: CoinPair) -> BookTicker:
        log.debug(f"get_book_ticker {coin_pair}")
        symbol = self._coin_pair_to_symbol(coin_pair)
        resp = self.client.get_orderbook_ticker(symbol=symbol)
        # 返回格式
        # {'askPrice': '28.11960000',
        #  'askQty': '2.00000000',
        #  'bidPrice': '28.11500000',
        #  'bidQty': '1.97000000',
        #  'symbol': 'BNBUSDT'}
        return BookTicker(coin_pair=coin_pair,
                          ask1_price=parse_decimal(resp['askPrice']),
                          ask1_qty=parse_decimal(resp['askQty']),
                          bid1_price=parse_decimal(resp['bidPrice']),
                          bid1_qty=parse_decimal(resp['bidQty'])
                          )

    def _require_credentials(self):
        if self.credentials is None:
            raise RuntimeError("此方法需要用户凭证, credentials is None")

    def get_balance_by_symbol(self, asset_symbol: str) -> (Decimal, Decimal):
        log.debug(f"get_balance_by_symbol {asset_symbol}")
        self._require_credentials()
        # 获取资产余额
        resp = self.client.get_asset_balance(asset_symbol)
        log.debug(f"get_balance_by_symbol resp: {resp}")
        # 返回格式
        # {'asset': 'BNB', 'free': '0.00000000', 'locked': '0.00000000'}
        return parse_decimal(resp['free']), parse_decimal(resp['locked'])

    def _convert_tif(self, tif: TimeInForce) -> str:
        return {
            TimeInForce.GTC: self.client.TIME_IN_FORCE_GTC,
            TimeInForce.FOK: self.client.TIME_IN_FORCE_FOK,
            TimeInForce.IOC: self.client.TIME_IN_FORCE_IOC,
        }.get(tif)

    def _convert_order_side(self, order_side: OrderSide) -> str:
        return {
            OrderSide.SELL: self.client.SIDE_SELL,
            OrderSide.BUY: self.client.SIDE_BUY,
        }.get(order_side)

    def _convert_binance_order_status(self, binance_order_status: str) -> OrderStatus:
        return {
            self.client.ORDER_STATUS_NEW: OrderStatus.NEW,
            self.client.ORDER_STATUS_PARTIALLY_FILLED: OrderStatus.PARTIALLY_FILLED,
            self.client.ORDER_STATUS_FILLED: OrderStatus.FILLED,
            self.client.ORDER_STATUS_CANCELED: OrderStatus.CANCELED,
            self.client.ORDER_STATUS_PENDING_CANCEL: OrderStatus.PENDING_CANCEL,
            self.client.ORDER_STATUS_REJECTED: OrderStatus.REJECTED,
            self.client.ORDER_STATUS_EXPIRED: OrderStatus.EXPIRED
        }.get(binance_order_status)

    def _convert_binance_order_side(self, binance_order_side: str) -> OrderSide:
        return {
            self.client.SIDE_BUY: OrderSide.BUY,
            self.client.SIDE_SELL: OrderSide.SELL,
        }.get(binance_order_side)

    def _convert_binance_order_type(self, binance_order_type: str) -> OrderType:
        return {
            self.client.ORDER_TYPE_LIMIT: OrderType.LIMIT,
            self.client.ORDER_TYPE_MARKET: OrderType.MARKET,
            # TODO: 添加其它订单类型
        }.get(binance_order_type)

    def _convert_binance_tif(self, binance_tif: str) -> TimeInForce:
        return {
            self.client.TIME_IN_FORCE_GTC: TimeInForce.GTC,
            self.client.TIME_IN_FORCE_FOK: TimeInForce.FOK,
            self.client.TIME_IN_FORCE_IOC: TimeInForce.IOC,
        }.get(binance_tif)

    @staticmethod
    def _convert_binance_datetime(binance_timestamp: int) -> datetime:
        return datetime.fromtimestamp(binance_timestamp / 1000)

    def create_limit_order(self, coin_pair: CoinPair, order_side: OrderSide, price: Decimal, qty: Decimal,
                           tif: TimeInForce = TimeInForce.GTC) -> Order:
        log.debug(f"create_limit_order {coin_pair}, {order_side}, {price}, {qty}, {tif}")
        self._require_credentials()
        # 限价单
        resp = self.client.order_limit(
            symbol=self._coin_pair_to_symbol(coin_pair),
            timeInForce=self._convert_tif(tif),
            side=self._convert_order_side(order_side),
            quantity=float(qty),
            price=float(price),
        )

        log.debug(f"create_limit_order resp: {resp}")

        # 返回格式:
        # {'clientOrderId': '9bHVLj9iNoVQkzq7oRByrl',
        #  'cummulativeQuoteQty': '0.00000000',
        #  'executedQty': '0.00000000',
        #  'fills': [],
        #  'orderId': 1057791006,
        #  'orderListId': -1,
        #  'origQty': '1.00100000',
        #  'price': '10.12340000',
        #  'side': 'BUY',
        #  'status': 'NEW',
        #  'symbol': 'BNBUSDT',
        #  'timeInForce': 'GTC',
        #  'transactTime': 1606665799609,
        #  'type': 'LIMIT'}
        return Order(
            coin_pair=coin_pair,  # 注意：此处没有从响应中解析
            order_id=str(resp['orderId']),
            client_order_id=resp['clientOrderId'],
            tif=self._convert_binance_tif(resp['timeInForce']),
            price=parse_decimal(resp['price']),
            qty=parse_decimal(resp['origQty']),
            filled_qty=parse_decimal(resp['executedQty']),
            order_side=self._convert_binance_order_side(resp['side']),
            status=self._convert_binance_order_status(resp['status']),
            type=self._convert_binance_order_type(resp['type']),
            time=self._convert_binance_datetime(resp['transactTime']),
        )

    def cancel_order(self, coin_pair: CoinPair, order_id: str) -> Order:
        log.debug(f"cancel_order {coin_pair} {order_id}")
        self._require_credentials()
        # 取消订单
        retry_client = RetryBinanceClient(self.client, 5, 0.5)  # 查询5次，如果查不到，每次休眠 0.3
        resp = retry_client.cancel_order(
            symbol=self._coin_pair_to_symbol(coin_pair),
            orderId=int(order_id)
        )

        log.debug(f"cancel_order resp: {resp}")

        # 返回格式:
        # {'clientOrderId': 'AYC2WhHdaqrhVdnh4Ep7E6',
        #  'cummulativeQuoteQty': '0.00000000',
        #  'executedQty': '0.00000000',
        #  'orderId': 1057721280,
        #  'orderListId': -1,
        #  'origClientOrderId': 'xObrDaLwW6n8QBtlZFa61T',
        #  'origQty': '1.00100000',
        #  'price': '10.12340000',
        #  'side': 'BUY',
        #  'status': 'CANCELED',
        #  'symbol': 'BNBUSDT',
        #  'timeInForce': 'GTC',
        #  'type': 'LIMIT'}
        return Order(
            coin_pair=coin_pair,  # 注意：此处没有从响应中解析
            order_id=str(resp['orderId']),
            client_order_id=resp['origClientOrderId'],
            tif=self._convert_binance_tif(resp['timeInForce']),
            price=parse_decimal(resp['price']),
            qty=parse_decimal(resp['origQty']),
            filled_qty=parse_decimal(resp['executedQty']),
            order_side=self._convert_binance_order_side(resp['side']),
            status=self._convert_binance_order_status(resp['status']),
            type=self._convert_binance_order_type(resp['type']),
            time=datetime.now()
        )

    def query_order(self, coin_pair: CoinPair, order_id: str) -> Order:
        log.debug(f"query_order {coin_pair} {order_id}")
        self._require_credentials()
        # 查询订单
        retry_client = RetryBinanceClient(self.client, 5, 0.3)  # 查询5次，如果查不到，每次休眠 0.3
        resp = retry_client.get_order(
            symbol=self._coin_pair_to_symbol(coin_pair),
            orderId=int(order_id)
        )

        log.debug(f"query_order resp: {resp}")

        # 返回格式:
        # {
        # "symbol": "LTCBTC", // 交易对
        # "orderId": 1, // 系统的订单ID
        # "orderListId": -1, // OCO订单的ID，不然就是 - 1
        # "clientOrderId": "myOrder1", // 客户自己设置的ID
        # "price": "0.1", // 订单价格
        # "origQty": "1.0", // 用户设置的原始订单数量
        # "executedQty": "0.0", // 交易的订单数量
        # "cummulativeQuoteQty": "0.0", // 累计交易的金额
        # "status": "NEW", // 订单状态
        # "timeInForce": "GTC", // 订单的时效方式
        # "type": "LIMIT", // 订单类型， 比如市价单，现价单等
        # "side": "BUY", // 订单方向，买还是卖
        # "stopPrice": "0.0", // 止损价格
        # "icebergQty": "0.0", // 冰山数量
        # "time": 1499827319559, // 订单时间
        # "updateTime": 1499827319559, // 最后更新时间
        # "isWorking": true, // 订单是否出现在orderbook中
        # "origQuoteOrderQty": "0.000000" // 原始的交易金额
        # }
        return Order(
            coin_pair=coin_pair,  # 注意：此处没有从响应中解析
            order_id=str(resp['orderId']),
            client_order_id=resp['clientOrderId'],
            tif=self._convert_binance_tif(resp['timeInForce']),
            price=parse_decimal(resp['price']),
            qty=parse_decimal(resp['origQty']),
            filled_qty=parse_decimal(resp['executedQty']),
            order_side=self._convert_binance_order_side(resp['side']),
            status=self._convert_binance_order_status(resp['status']),
            type=self._convert_binance_order_type(resp['type']),
            time=self._convert_binance_datetime(resp['updateTime']),
        )

    def cancel_all(self, coin_pair: CoinPair) -> List[Order]:
        log.debug(f"cancel_all {coin_pair}")
        self._require_credentials()

        try:
            # 取消所有订单
            resp = self.client.cancel_orders(
                symbol=self._coin_pair_to_symbol(coin_pair),
            )

            log.debug(f"cancel_all resp: {resp}")

            # 返回格式：
            # [
            #     {
            #         "symbol": "BTCUSDT",
            #         "origClientOrderId": "E6APeyTJvkMvLMYMqu1KQ4",
            #         "orderId": 11,
            #         "orderListId": -1,
            #         "clientOrderId": "pXLV6Hz6mprAcVYpVMTGgx",
            #         "price": "0.089853",
            #         "origQty": "0.178622",
            #         "executedQty": "0.000000",
            #         "cummulativeQuoteQty": "0.000000",
            #         "status": "CANCELED",
            #         "timeInForce": "GTC",
            #         "type": "LIMIT",
            #         "side": "BUY"
            #     },
            #     {
            #         "symbol": "BTCUSDT",
            #         "origClientOrderId": "A3EF2HCwxgZPFMrfwbgrhv",
            #         "orderId": 13,
            #         "orderListId": -1,
            #         "clientOrderId": "pXLV6Hz6mprAcVYpVMTGgx",
            #         "price": "0.090430",
            #         "origQty": "0.178622",
            #         "executedQty": "0.000000",
            #         "cummulativeQuoteQty": "0.000000",
            #         "status": "CANCELED",
            #         "timeInForce": "GTC",
            #         "type": "LIMIT",
            #         "side": "BUY"
            #     }
            # ]
            return [Order(
                coin_pair=coin_pair,  # 注意：此处没有从响应中解析
                order_id=str(r['orderId']),
                client_order_id=r['origClientOrderId'],
                tif=self._convert_binance_tif(r['timeInForce']),
                price=parse_decimal(r['price']),
                qty=parse_decimal(r['origQty']),
                filled_qty=parse_decimal(resp['executedQty']),
                order_side=self._convert_binance_order_side(r['side']),
                status=self._convert_binance_order_status(r['status']),
                type=self._convert_binance_order_type(r['type']),
                time=datetime.now()
            ) for r in resp]

        except BinanceAPIException as e:
            if e.code == -2011:  # Unknown order sent.
                # If the order status is not NEW (open order), this message will be returned.
                log.debug("取消全部未结订单时, 订单状态不是 NEW")
                return []
            else:
                raise e

    def get_trades(self, coin_pair: CoinPair, from_trade_id: str = None) -> List[Trade]:
        log.debug(f"get_trades {coin_pair} {from_trade_id}")
        self._require_credentials()
        # 获取所有成交记录
        params = {
            "symbol": self._coin_pair_to_symbol(coin_pair),
        }
        if from_trade_id is not None:
            params['fromId'] = int(from_trade_id)
        resp = self.client.get_my_trades(**params)

        log.debug(f"get_trades resp: {resp}")

        # 响应格式
        # [
        #     {
        #         "symbol": "BNBBTC",
        #         "id": 28457,
        #         "orderId": 100234,
        #         "orderListId": -1,
        #         "price": "4.00000100",
        #         "qty": "12.00000000",
        #         "quoteQty": "48.000012",
        #         "commission": "10.10000000",
        #         "commissionAsset": "BNB",
        #         "time": 1499865549590,
        #         "isBuyer": true,
        #         "isMaker": false,
        #         "isBestMatch": true
        #     }
        # ]
        return [
            Trade(coin_pair=coin_pair,
                  trade_id=str(r['id']),
                  order_id=str(r['orderId']),
                  price=parse_decimal(r['price']),
                  qty=parse_decimal(r['qty']),
                  commission=parse_decimal(r['commission']),
                  commission_asset=r['commissionAsset'],
                  timestamp=self._convert_binance_datetime(r['time']),
                  is_marker=r['isMaker'],
                  order_side=OrderSide.BUY if r['isBuyer'] else OrderSide.SELL,
                  is_best_match=r['isBestMatch']
                  )
            for r in resp]

    def _convert_kline_period(self, period: KlinePeriod) -> str:
        return {

            KlinePeriod.MIN1: self.client.KLINE_INTERVAL_1MINUTE,
            KlinePeriod.MIN5: self.client.KLINE_INTERVAL_5MINUTE,
            KlinePeriod.MIN15: self.client.KLINE_INTERVAL_15MINUTE,
            KlinePeriod.MIN30: self.client.KLINE_INTERVAL_30MINUTE,
            KlinePeriod.HOUR1: self.client.KLINE_INTERVAL_1HOUR,
            KlinePeriod.HOUR4: self.client.KLINE_INTERVAL_4HOUR,
            KlinePeriod.HOUR8: self.client.KLINE_INTERVAL_8HOUR,
            KlinePeriod.DAY1: self.client.KLINE_INTERVAL_1DAY,
            KlinePeriod.WEEK1: self.client.KLINE_INTERVAL_1WEEK,
        }.get(period)

    def get_kline(self, coin_pair: CoinPair, period: KlinePeriod) -> List[Bar]:
        log.debug(f"获取K线数据 {coin_pair}, {period}")
        resp = self.client.get_klines(
            symbol=self._coin_pair_to_symbol(coin_pair),
            interval=self._convert_kline_period(period),
        )
        log.debug(f"get_kline resp: {resp}")

        # 响应格式
        # [
        #         [
        #             1499040000000,      # Open time
        #             "0.01634790",       # Open
        #             "0.80000000",       # High
        #             "0.01575800",       # Low
        #             "0.01577100",       # Close
        #             "148976.11427815",  # Volume
        #             1499644799999,      # Close time
        #             "2434.19055334",    # Quote asset volume
        #             308,                # Number of trades
        #             "1756.87402397",    # Taker buy base asset volume
        #             "28.46694368",      # Taker buy quote asset volume
        #             "17928899.62484339" # Can be ignored
        #         ]
        # ]
        return [
            Bar(
                time=self._convert_binance_datetime(r[6]),
                open=parse_decimal(r[1]),
                high=parse_decimal(r[2]),
                low=parse_decimal(r[3]),
                close=parse_decimal(r[4]),
                volume=parse_decimal(r[5])
            )
            for r in resp
        ]
