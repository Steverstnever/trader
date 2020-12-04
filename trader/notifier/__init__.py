import logging
from abc import ABC, abstractmethod

from telegram.ext import Updater


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


class TgNotifier(Notifier):
    """
    telegram 通知
    获取chat_id的地址https://api.telegram.org/bot{YourBOTToken}/getUpdates
    """

    def __init__(self, token: str, chat_id: int):
        self._token = token
        self._chat_id = chat_id

    def notify(self, msg: str):
        updater = Updater(token=self._token, use_context=True)
        updater.bot.send_message(self._chat_id, f"【通知】{msg}", timeout=5)
