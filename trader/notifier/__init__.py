import logging
from abc import ABC, abstractmethod


class Notifier(ABC):
    """
    通知器
    """

    @abstractmethod
    def notify(self, msg: str):
        """
        发送通知

        Args:
            msg (str): 消息

        Returns:
            None
        """


class LoggerNotifier(Notifier):
    def __init__(self):
        self.log = logging.getLogger("logger-notifier")

    def notify(self, msg: str):
        self.log.warning(f"【通知】{msg}")
