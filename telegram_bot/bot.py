import asyncio
import logging
import os
from flask import Flask
from hypercorn.asyncio import serve
from hypercorn.config import Config
from core.api import APIFootball
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

class TelegramBot:
    def __init__(self, api_football, telegram_token, chat_id):
        self.api_football = api_football
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.bot = Bot(token=self.telegram_token)

    async def enviar_mensagem(self, mensagem):
        """Envia uma mensagem para o chat do Telegram."""
        try:
            logging.info(f"Enviando mensagem: {mensagem}")
            await self.bot.send_message(chat_id=self.chat_id, text=mensagem)
            logging.info("Mensagem enviada com sucesso")
        except Exception as e:
            logging.error(f"Erro ao enviar mensagem: {e}")

    async def start_message(self):
        """Envio de mensagem inicial quando o bot começa"""
        await self.enviar_mensagem("Starting analysis...")

async def job_jogos_do_dia(api_football, telegram_bot):
    """Executa os jobs do bot."""
    await telegram_bot.enviar_jogos_do_dia()

async def job_monitorar(api_football, telegram_bot):
    """Executa os jobs do bot."""
    await telegram_bot.monitorar_jogos()

async def start_scheduler(api_football, telegram_bot):
    """Inicia o agendador para executar jobs."""
    scheduler = AsyncIOScheduler(timezone=timezone('Europe/London'))
    scheduler.add_job(job_jogos_do_dia, "cron", hour=13, minute=44, args=[api_football, telegram_bot])
    scheduler.add_job(job_monitorar, "interval", seconds=5, args=[api_football, telegram_bot])
    scheduler.start()
    await asyncio.Event().wait()

@app.route("/")
def health_check():
    """Endpoint para checar se o serviço está ativo."""
    return {"status": "running"}, 200

def main():
    # Definir sua chave da API e token do Telegram
    api_key = "49dcecff9c9746a678c6b2887af923b1"  # Substitua com sua chave da API
    telegram_token = "8195835290:AAHnsVeIY_fS_Nmi9tkKl_e9JskMoZ4y1Zk"  # Substitua com seu token do Telegram
    chat_id = "-1002279145550"  # Substitua com o ID do chat para enviar as mensagens

    # Inicializa a classe APIFootball
    api_football = APIFootball(api_key)

    # Inicializa a classe TelegramBot
    telegram_bot = TelegramBot(api_football, telegram_token, chat_id)

    # Inicia o scheduler em segundo plano
    asyncio.get_event_loop().create_task(start_scheduler(api_football, telegram_bot))

    # Envia mensagem inicial ao começar
    asyncio.get_event_loop().create_task(telegram_bot.start_message())

    # Configuração do Hypercorn
    config = Config()
    config.bind = ["0.0.0.0:" + os.getenv("PORT", "8080")]
    
    # Inicia o servidor com Hypercorn de forma assíncrona
    asyncio.run(serve(app, config))

if __name__ == "__main__":
    main()
