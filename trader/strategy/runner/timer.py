import time
from datetime import datetime, timedelta
from typing import List

from trader.strategy.base import StrategyEvent, StrategyRunner, Strategy


class TimerEvent(StrategyEvent):
    """时钟事件"""

    def __init__(self, timer_id):
        self.timer_id = timer_id

    def __str__(self):
        return f"TimerEvent({self.timer_id})"


class ElapsedTimer:
    def __init__(self, last_time: datetime, timer_id: str, duration: timedelta):
        self.last_time = last_time
        self.timer_id = timer_id
        self.duration = duration

    def is_elapsed(self, now: datetime) -> bool:
        return now - self.last_time > self.duration

    def update(self, now: datetime):
        self.last_time = now


class TimerRunner(StrategyRunner):
    def __init__(self, strategy: Strategy):
        super().__init__(strategy)
        self.timers: List[ElapsedTimer] = []

    def add_timer(self, timer_id, duration: timedelta):
        elapsed_timer = ElapsedTimer(datetime.now(), timer_id, duration)
        self.timers.append(elapsed_timer)
        return elapsed_timer

    def run(self):
        self.strategy.initialize()
        while True:
            now = datetime.now()
            for timer in self.timers:
                if timer.is_elapsed(now):
                    # Timer 到期了，发送 timer 事件
                    event: TimerEvent = TimerEvent(timer.timer_id)  # 发送给策略的事件
                    try:
                        self.strategy.handle_event(event)
                    except Exception as e:
                        self.strategy.handle_exception(e, event)
                    timer.update(now)  # 更新 Timer 最后更新时间，开始重新计时

            time.sleep(0.01)  # sleep 最小间隔时间，提高精度
