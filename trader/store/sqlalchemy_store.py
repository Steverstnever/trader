import logging
from datetime import datetime
from typing import List

from sqlalchemy import Table, create_engine, MetaData, Column, Integer, String, DECIMAL, DateTime, Boolean, \
    UniqueConstraint, desc
from sqlalchemy.exc import IntegrityError

from trader.spot.types import Trade, CoinPair
from trader.spot.types.account_snapshot import AccountSnapshot
from trader.spot.types.order_types import Order, OrderSide
from trader.store import StrategyStore

log = logging.getLogger('sqlalchemy-strategy-store')


class SqlalchemyStrategyStore(StrategyStore):

    def __init__(self, db_url, echo: bool = False):
        self.engine = create_engine(db_url, echo=echo)
        self.metadata = MetaData(self.engine)

        self.order_table = Table('order', self.metadata,
                                 Column("id", Integer, primary_key=True, comment="主键"),
                                 Column("coin_pair", String, comment="币对"),
                                 Column("order_id", String, comment="订单id"),
                                 Column("client_order_id", String, comment="客户订单id"),
                                 Column("tif", String, comment="Time in force"),
                                 Column("price", DECIMAL, comment="订单价格"),
                                 Column("qty", DECIMAL, comment="订单数量"),
                                 Column("side", String, comment="买卖方向(buy|sell)"),
                                 Column("filled_qty", DECIMAL, comment="成交数量"),
                                 Column("avg_price", DECIMAL, comment="成交均价"),
                                 Column("commission", DECIMAL, comment="手续费"),
                                 Column("status", String, comment="订单状态(FILLED|CANCELED|REJECTED|EXPIRED)"),
                                 Column("type", String, comment="订单类型(maker|taker)"),
                                 Column("time", DateTime, comment="时间戳"),
                                 UniqueConstraint('coin_pair', 'order_id', name='unique_coin_pair_order_id')
                                 )

        self.trade_table = Table("trade", self.metadata,
                                 Column("id", Integer, primary_key=True, comment="主键"),
                                 Column("coin_pair", String, comment="币对"),
                                 Column("trade_id", String, comment="交易id"),
                                 Column("order_id", String, comment="订单id"),
                                 Column("price", DECIMAL, comment="成交价格"),
                                 Column("qty", DECIMAL, comment="成交数量"),
                                 Column("commission", DECIMAL, comment="资产数量"),
                                 Column("commission_asset", String, comment="现金币种"),
                                 Column("side", String, comment="买卖方向(buy|sell)"),
                                 Column("is_maker", Boolean, comment="是否 Maker"),
                                 Column("is_best_match", Boolean, comment="是否最佳匹配"),
                                 Column("time", DateTime, comment="时间戳"),
                                 UniqueConstraint('coin_pair', 'trade_id', name='unique_coin_pair_trade_id')
                                 )

        self.account_snapshot_table = Table("account_snapshot", self.metadata,
                                            Column("id", Integer, primary_key=True, comment="主键"),
                                            Column("asset", String, comment="资产币种"),
                                            Column("asset_qty", DECIMAL, comment="资产数量"),
                                            Column("cash", String, comment="现金币种"),
                                            Column("cash_qty", DECIMAL, comment="现金数量"),
                                            Column("price", DECIMAL, comment="资产价格"),
                                            Column("time", DateTime, comment="时间戳"),
                                            )

        self.metadata.create_all(checkfirst=True)

    def save_order(self, order: Order):
        try:
            ins = self.order_table.insert().values(coin_pair=order.coin_pair.symbol,
                                                   order_id=order.order_id,
                                                   client_order_id=order.client_order_id,
                                                   tif=order.tif.name,
                                                   price=order.price,
                                                   qty=order.qty,
                                                   filled_qty=order.filled_qty,
                                                   side=order.order_side.name,
                                                   status=order.status.name,
                                                   type=order.type.name,
                                                   time=order.time,
                                                   )
            with self.engine.connect() as conn:
                conn.execute(ins)

        except IntegrityError as e:
            # 忽略重复数据
            log.debug(f"save_order ignore duplicate-record: {order}, error: {e}")

    def save_account_snapshot(self, account_snapshot: AccountSnapshot):
        ins = self.account_snapshot_table.insert().values(asset=account_snapshot.asset,
                                                          asset_qty=account_snapshot.asset_qty,
                                                          cash=account_snapshot.cash,
                                                          cash_qty=account_snapshot.cash_qty,
                                                          price=account_snapshot.price,
                                                          time=datetime.now()
                                                          )
        with self.engine.connect() as conn:
            conn.execute(ins)

    def save_trades(self, trades: List[Trade]):
        for trade in trades:
            try:
                with self.engine.connect() as conn:
                    ins = self.trade_table.insert().values(coin_pair=trade.coin_pair.symbol,
                                                           trade_id=trade.trade_id,
                                                           order_id=trade.order_id,
                                                           price=trade.price,
                                                           qty=trade.qty,
                                                           commission=trade.commission,
                                                           commission_asset=trade.commission_asset,
                                                           side=trade.order_side.name,
                                                           is_maker=trade.is_marker,
                                                           is_best_match=trade.is_best_match,
                                                           time=trade.timestamp,
                                                           )
                    conn.execute(ins)
            except IntegrityError as e:
                # 忽略重复数据
                log.debug(f"save_trades ignore duplicate-record: {trade}, error: {e}")

    def load_trades(self, limit: int = None) -> List[Trade]:
        with self.engine.connect() as conn:
            sel = self.trade_table.select().order_by(desc(self.trade_table.c.time))
            if limit is not None:
                sel = sel.limit(limit)
            result_proxy = conn.execute(sel)
            result: List[Trade] = []
            for r in result_proxy:
                columns = self.trade_table.c
                t = Trade(
                    coin_pair=CoinPair.from_symbol(r[columns.coin_pair]),
                    trade_id=r[columns.trade_id],
                    order_id=r[columns.trade_id],
                    price=r[columns.price],
                    qty=r[columns.qty],
                    commission=r[columns.commission],
                    commission_asset=r[columns.commission_asset],
                    timestamp=r[columns.time],
                    order_side=OrderSide[r[columns.side]],
                    is_marker=r[columns.is_maker],
                    is_best_match=r[columns.is_best_match],
                )

                # from pprint import pprint
                # pprint(r)
                # print(t)
                result.append(t)
            return result

    def get_last_trade_id(self) -> str:
        trades = self.load_trades(1)
        return trades[0].trade_id if len(trades) > 0 else None
