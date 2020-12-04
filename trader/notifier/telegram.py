from telegram.ext import Updater

from trader.notifier import Notifier


class TelegramNotifier(Notifier):
    """
    telegram 通知
    """

    def __init__(self, token: str, chat_id: int):
        self._token = token
        self._chat_id = chat_id

    def notify(self, msg: str):
        updater = Updater(token=self._token, use_context=True)
        updater.bot.send_message(self._chat_id, f"【通知】{msg}", timeout=5)
