import logging
import uuid
from datetime import datetime
from decimal import Decimal

from trader.credentials import Credentials
from trader.futures.api.futures_api import FuturesApi
from trader.third_party.binance.client import Client
from trader.futures.types import (
    Asset, ContractPair, PerpetualContractPair, DeliveryContractPair, Bar, Position,
    PositionSide, Order, OrderStatus, OrderType, FuturesInstrumentInfo, OrderSide
)


logger = logging.getLogger(__name__)


def parse_binance_kline(data):
    open_price = data[1]
    high = data[2]
    low = data[3]
    close_price = data[4]
    volume = data[5]
    start_time = datetime.fromtimestamp(data[0] / 1000)
    return Bar(open_time=start_time,
               open_price=Decimal(open_price),
               close_price=Decimal(close_price),
               high=Decimal(high),
               low=Decimal(low),
               volume=Decimal(volume))


class BinanceUSDTFuturesApi(FuturesApi):
    """金本位合约"""

    def __init__(self, credentials: Credentials):
        self.client = Client(api_key=credentials.api_key, api_secret=credentials.secret_key)

    @classmethod
    def _contract_pair_to_symbol(cls, contract_pair: ContractPair) -> str:
        if isinstance(contract_pair, PerpetualContractPair):
            return contract_pair.asset_symbol + contract_pair.cash_symbol
        elif isinstance(contract_pair, DeliveryContractPair):  # todo usdt交割合约暂时没有
            """"""

    @classmethod
    def gen_client_order_id(cls):
        return str(uuid.uuid4())

    def cancel_all(self, contract_pair: ContractPair):
        symbol = self._contract_pair_to_symbol(contract_pair)
        return self.client.futures_cancel_all_open_orders(symbol=symbol)

    def get_instrument_info(self, contract_pair: ContractPair):
        rv = self.client.futures_exchange_info()
        symbol = self._contract_pair_to_symbol(contract_pair)
        info = FuturesInstrumentInfo(contract_pair, Decimal('0'), Decimal('0'))
        for each in rv['symbols']:
            if each['symbol'] == symbol:
                for f in each['filters']:
                    if 'PRICE_FILTER' == f['filterType']:
                        info.max_price = Decimal(f['maxPrice'])
                        info.min_price = Decimal(f['minPrice'])
                    if 'LOT_SIZE' == f['filterType']:
                        info.max_qty = Decimal(f['maxQty'])
                        info.min_qty = Decimal(f['minQty'])
                info.min_price_size = each['pricePrecision']
                info.min_qty_size = each['quantityPrecision']
                info.min_notional = info.min_price * info.min_qty
                return info

    def query_order(self, contract_pair: ContractPair, client_order_id: str, order_id: str, **kwargs):
        kwargs['symbol'] = self._contract_pair_to_symbol(contract_pair)
        return self.client.futures_get_order(**kwargs)

    def klines(self, contract_pair: ContractPair, interval: str, **kwargs):
        kwargs['symbol'] = self._contract_pair_to_symbol(contract_pair)
        kwargs['interval'] = interval
        rv = self.client.futures_klines(**kwargs)
        return [parse_binance_kline(each) for each in rv]

    def create_stop_order(self, client_order_id: str, contract_pair: ContractPair, order_side: OrderSide,
                          position_side: PositionSide, price: Decimal, stop_price: Decimal, qty: Decimal, **kwargs):
        """
        Response
        {
            "clientOrderId": "testOrder", // 用户自定义的订单号
            "cumQty": "0",
            "cumBase": "0", // 成交额(标的数量)
            "executedQty": "0", // 成交量(张数)
            "orderId": 22542179, // 系统订单号
            "avgPrice": "0.0",      // 平均成交价
            "origQty": "10", // 原始委托数量
            "price": "0", // 委托价格
            "reduceOnly": false, // 仅减仓
            "closePosition": false,   // 是否条件全平仓
            "side": "SELL", // 买卖方向
            "positionSide": "SHORT", // 持仓方向
            "status": "NEW", // 订单状态
            "stopPrice": "0", // 触发价,对`TRAILING_STOP_MARKET`无效
            "symbol": "BTCUSD_200925", // 交易对
            "pair": "BTCUSD",   // 标的交易对
            "timeInForce": "GTC", // 有效方法
            "type": "TRAILING_STOP_MARKET", // 订单类型
            "origType": "TRAILING_STOP_MARKET",  // 触发前订单类型
            "activatePrice": "9020", // 跟踪止损激活价格, 仅`TRAILING_STOP_MARKET` 订单返回此字段
            "priceRate": "0.3", // 跟踪止损回调比例, 仅`TRAILING_STOP_MARKET` 订单返回此字段
            "updateTime": 1566818724722, // 更新时间
            "workingType": "CONTRACT_PRICE", // 条件价格触发类型
            "priceProtect": false            // 是否开启条件单触发保护
        }
        """
        side = self.client.coin_futures_get_position_side_dual()
        if not side['dualSidePosition']:
            """单向持仓模式需要修改为双向持仓模式"""
            self.client.futures_update_position_side_dual(dualSidePosition=True)
        kwargs['newClientOrderId'] = client_order_id
        kwargs['symbol'] = self._contract_pair_to_symbol(contract_pair)
        kwargs['side'] = order_side.name
        kwargs['positionSide'] = position_side.name
        kwargs['type'] = 'STOP'
        kwargs['price'] = price
        kwargs['stopPrice'] = stop_price
        kwargs['quantity'] = qty
        rv = self.client.futures_create_order(**kwargs)
        return Order(
            client_order_id=rv['clientOrderId'],
            contract_pair=contract_pair,
            executed_qty=Decimal(rv['executedQty']),  # 成交量(张数)
            order_id=rv['clientOrderId'],  # 系统订单号
            avg_price=Decimal('avgPrice'),  # 平均成交价
            order_side=order_side,
            position_side=position_side,  # 持仓方向
            status=OrderStatus(rv['status']),
            type=OrderType('STOP')
        )

    def delete_all_order(self, contract_pair: ContractPair, **kwargs):
        kwargs['symbol'] = self._contract_pair_to_symbol(contract_pair)
        self.client.futures_cancel_all_open_orders(**kwargs)

    def get_balance_by_symbol(self, symbol: str) -> Asset:
        rv = self.client.futures_account()
        for each in rv['assets']:
            if each['asset'] == symbol:
                return Asset(symbol,
                             Decimal(each.get('walletBalance', '0')),
                             Decimal(each.get('marginBalance', '0')),
                             Decimal(each.get('availableBalance', '0'))
                             )

    def get_position(self, contract_pair: ContractPair):
        symbol = self._contract_pair_to_symbol(contract_pair)
        rv = self.client.futures_position_information(pair=symbol)
        position = []
        for each in rv:
            amt = Decimal(each['positionAmt'])
            if amt != 0:
                p = Position(contract_pair, abs(amt), Decimal(rv['entryPrice']), Decimal(rv['markPrice']),
                             PositionSide(each['positionSide'].lower()))
                position.append(p)
        return position

    def futures_account(self):
        return self.client.futures_account()

    def cancel_order(self, contract_pair: ContractPair, client_order_id: str, order_id: str, **kwargs):
        kwargs['symbol'] = self._contract_pair_to_symbol(contract_pair)
        if client_order_id:
            kwargs['origClientOrderId'] = client_order_id
        if order_id:
            kwargs['orderId'] = order_id
        rv = self.client.futures_cancel_order(**kwargs)
        return Order(
            client_order_id=rv['clientOrderId'],
            contract_pair=contract_pair,
            executed_qty=Decimal(rv['executedQty']),  # 成交量(张数)
            order_id=rv['clientOrderId'],  # 系统订单号
            avg_price=Decimal('avgPrice'),  # 平均成交价
            order_side=OrderSide(rv['side']),
            position_side=PositionSide(rv['positionSide']),  # 持仓方向
            status=OrderStatus(rv['status']),
            type=OrderType('STOP')
        )


class BinanceCoinFuturesApi(FuturesApi):
    """币本位合约"""

    perpetual_contract_suffix = '_PERP'

    def __init__(self, credentials: Credentials):
        self.client = Client(api_key=credentials.api_key, api_secret=credentials.secret_key)

    @classmethod
    def gen_client_order_id(cls):
        return str(uuid.uuid4())

    @classmethod
    def _contract_pair_to_symbol(cls, contract_pair: ContractPair) -> str:
        if isinstance(contract_pair, PerpetualContractPair):
            """永续合约"""
            return contract_pair.asset_symbol + contract_pair.cash_symbol + cls.perpetual_contract_suffix
        elif isinstance(contract_pair, DeliveryContractPair):
            """交割合约"""
            return contract_pair.asset_symbol + contract_pair.cash_symbol + str(contract_pair.delivery_time)

    def klines(self, contract_pair: ContractPair, interval: str, **kwargs):
        kwargs['symbol'] = self._contract_pair_to_symbol(contract_pair)
        kwargs['interval'] = interval
        rv = self.client.coin_futures_klines(**kwargs)
        return [parse_binance_kline(each) for each in rv]

    def create_stop_order(self, client_order_id: str, contract_pair: ContractPair, order_side: OrderSide,
                          position_side: PositionSide, price: Decimal, stop_price: Decimal, qty: Decimal, **kwargs):
        """
        Response
        {
            "clientOrderId": "testOrder", // 用户自定义的订单号
            "cumQty": "0",
            "cumBase": "0", // 成交额(标的数量)
            "executedQty": "0", // 成交量(张数)
            "orderId": 22542179, // 系统订单号
            "avgPrice": "0.0",      // 平均成交价
            "origQty": "10", // 原始委托数量
            "price": "0", // 委托价格
            "reduceOnly": false, // 仅减仓
            "closePosition": false,   // 是否条件全平仓
            "side": "SELL", // 买卖方向
            "positionSide": "SHORT", // 持仓方向
            "status": "NEW", // 订单状态
            "stopPrice": "0", // 触发价,对`TRAILING_STOP_MARKET`无效
            "symbol": "BTCUSD_200925", // 交易对
            "pair": "BTCUSD",   // 标的交易对
            "timeInForce": "GTC", // 有效方法
            "type": "TRAILING_STOP_MARKET", // 订单类型
            "origType": "TRAILING_STOP_MARKET",  // 触发前订单类型
            "activatePrice": "9020", // 跟踪止损激活价格, 仅`TRAILING_STOP_MARKET` 订单返回此字段
            "priceRate": "0.3", // 跟踪止损回调比例, 仅`TRAILING_STOP_MARKET` 订单返回此字段
            "updateTime": 1566818724722, // 更新时间
            "workingType": "CONTRACT_PRICE", // 条件价格触发类型
            "priceProtect": false            // 是否开启条件单触发保护
        }
        """
        side = self.client.coin_futures_get_position_side_dual()
        if not side['dualSidePosition']:
            """单向持仓模式需要修改为双向持仓模式"""
            self.client.coin_futures_update_position_side_dual(dualSidePosition=True)
        kwargs['newClientOrderId'] = client_order_id
        kwargs['symbol'] = self._contract_pair_to_symbol(contract_pair)
        kwargs['side'] = order_side.name
        kwargs['positionSide'] = position_side.name
        kwargs['type'] = 'STOP'
        kwargs['price'] = price
        kwargs['stopPrice'] = stop_price
        kwargs['quantity'] = qty
        rv = self.client.coin_futures_create_order(**kwargs)
        return Order(
            client_order_id=rv['clientOrderId'],
            contract_pair=contract_pair,
            executed_qty=Decimal(rv['executedQty']),  # 成交量(张数)
            order_id=rv['clientOrderId'],  # 系统订单号
            avg_price=Decimal('avgPrice'),  # 平均成交价
            order_side=order_side,
            position_side=position_side,  # 持仓方向
            status=OrderStatus(rv['status']),
            type=OrderType('STOP')
        )

    def get_balance_by_symbol(self, symbol: str) -> Asset:
        rv = self.client.coin_futures_account()
        for each in rv['assets']:
            if each['asset'] == symbol:
                return Asset(symbol,
                             Decimal(each.get('walletBalance', '0')),
                             Decimal(each.get('marginBalance', '0')),
                             Decimal(each.get('availableBalance', '0'))
                             )

    def coin_futures_account(self):
        return self.client.coin_futures_account()

    def get_position(self, contract_pair: ContractPair):
        symbol = self._contract_pair_to_symbol(contract_pair)
        rv = self.client.coin_futures_position_information(pair=symbol)
        position = []
        for each in rv:
            amt = Decimal(each['positionAmt'])
            if amt != 0:
                p = Position(contract_pair, abs(amt), Decimal(rv['entryPrice']), Decimal(rv['markPrice']),
                             PositionSide(each['positionSide'].lower()))
                position.append(p)
        return position

    def delete_all_order(self, contract_pair: ContractPair, **kwargs):
        kwargs['symbol'] = self._contract_pair_to_symbol(contract_pair)
        return self.client.coin_futures_cancel_all_open_orders(**kwargs)

    def query_order(self, contract_pair: ContractPair, client_order_id: str, order_id: str, **kwargs):
        kwargs['symbol'] = self._contract_pair_to_symbol(contract_pair)
        if client_order_id:
            kwargs['origClientOrderId'] = client_order_id
        if order_id:
            kwargs['orderId'] = order_id
        return self.client.coin_futures_get_order(**kwargs)

    def cancel_order(self, contract_pair: ContractPair, client_order_id: str, order_id: str, **kwargs):
        kwargs['symbol'] = self._contract_pair_to_symbol(contract_pair)
        if client_order_id:
            kwargs['origClientOrderId'] = client_order_id
        if order_id:
            kwargs['orderId'] = order_id
        rv = self.client.coin_futures_cancel_order(**kwargs)
        return Order(
            client_order_id=rv['clientOrderId'],
            contract_pair=contract_pair,
            executed_qty=Decimal(rv['executedQty']),  # 成交量(张数)
            order_id=rv['clientOrderId'],  # 系统订单号
            avg_price=Decimal('avgPrice'),  # 平均成交价
            order_side=OrderSide(rv['side']),
            position_side=PositionSide(rv['positionSide']),  # 持仓方向
            status=OrderStatus(rv['status']),
            type=OrderType('STOP')
        )

    def get_instrument_info(self, contract_pair: ContractPair):
        rv = self.client.coin_futures_exchange_info()
        symbol = self._contract_pair_to_symbol(contract_pair)
        info = FuturesInstrumentInfo(contract_pair, Decimal('0'), Decimal('0'))
        for each in rv['symbols']:
            if each['symbol'] == symbol:
                for f in each['filters']:
                    if 'PRICE_FILTER' == f['filterType']:
                        info.max_price = Decimal(f['maxPrice'])
                        info.min_price = Decimal(f['minPrice'])
                    if 'LOT_SIZE' == f['filterType']:
                        info.max_qty = Decimal(f['maxQty'])
                        info.min_qty = Decimal(f['minQty'])
                info.min_price_size = each['pricePrecision']
                info.min_qty_size = each['quantityPrecision']
                info.min_notional = info.min_price * info.min_qty
                return info

    def cancel_all(self, contract_pair: ContractPair):
        symbol = self._contract_pair_to_symbol(contract_pair)
        return self.client.futures_cancel_all_open_orders(symbol=symbol)
