from telegram_bot.bot import TelegramBot  # Supondo que a classe TelegramBot está no arquivo telegram_bot.py
from config.settings import TELEGRAM_TOKEN
from config.settings import CHAT_ID
def main():
    # Defina sua chave de API e o ID do grupo do Telegram

    # Crie uma instância do bot
    bot = TelegramBot(TELEGRAM_TOKEN, CHAT_ID)

    # Inicie o bot
    bot.start()

if __name__ == "__main__":
    main()
