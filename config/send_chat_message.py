import asyncio
from telegram import Bot

# Substitua com o token do seu bot
api_key = '7948020728:AAEzjLZzu58hLD6_cruXS6BUtwKl48RnVz8'
bot = Bot(token=api_key)

# Substitua com o chat ID do grupo
chat_id = -1002440594973

async def send_message():
    # Envia a mensagem de forma assíncrona
    await bot.send_message(chat_id=chat_id, text="teste")

# Executa a função assíncrona
asyncio.run(send_message())
