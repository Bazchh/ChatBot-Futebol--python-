import asyncio
from telegram import Bot

# Substitua com o token do seu bot
api_key = '8195835290:AAHnsVeIY_fS_Nmi9tkKl_e9JskMoZ4y1Zk'
bot = Bot(token=api_key)

# Substitua com o chat ID do grupo
chat_id = -1002279145550

async def send_message():
    # Envia a mensagem de forma assíncrona
    await bot.send_message(chat_id=chat_id, text="testando conexão")

# Executa a função assíncrona
asyncio.run(send_message())
