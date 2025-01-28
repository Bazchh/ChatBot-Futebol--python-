import asyncio
import sys
import json
import logging
from flask import Flask, jsonify, Response
from flask_sse import sse
sys.path.append("..")  # Adiciona o diretório pai ao caminho de importação
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from api import FootballAPI  # Certifique-se de que FootballAPI esteja configurada corretamente
import os
from pytz import timezone
from hypercorn.config import Config
from hypercorn.asyncio import serve

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

app = Flask(__name__)  # Cria o servidor Flask

# Configuração do Redis
app.config["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # A URL de conexão com o Redis
app.register_blueprint(sse, url_prefix='/stream')  # Registra o blueprint do SSE

class TelegramBot:
    def __init__(self, api_football, telegram_token, chat_id):
        self.api_football = api_football
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.bot = Bot(token=self.telegram_token)
        self.jogos_enviados = set()  # Cache para evitar mensagens duplicadas

    async def enviar_mensagem(self, mensagem):
        """Envia uma mensagem para o chat do Telegram, dividindo-a se for muito longa."""
        try:
            max_length = 4096  # Limite de caracteres permitido pelo Telegram
            if len(mensagem) > max_length:
                partes = [mensagem[i:i + max_length] for i in range(0, len(mensagem), max_length)]
                for parte in partes:
                    await self.bot.send_message(chat_id=self.chat_id, text=parte)
                    logger.info(f"Mensagem enviada em partes para {self.chat_id}: {parte}")
            else:
                await self.bot.send_message(chat_id=self.chat_id, text=mensagem)
                logger.info(f"Mensagem enviada para {self.chat_id}: {mensagem}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")

    async def enviar_jogos_do_dia(self):
        """Busca e envia a lista de jogos do dia."""
        logger.info("\n=== Enviando jogos do dia ===\n")
        jogos = self.api_football.listar_jogos_do_dia()
        
        if jogos:
            mensagem = "Football games today:\n"
            for jogo in jogos:
                time_casa = jogo.get("time_casa", "Desconhecido")
                time_fora = jogo.get("time_fora", "Desconhecido")
                hora_jogo = jogo.get("hora_jogo", "Data não disponível")
                mensagem += f"{time_casa} x {time_fora} - Time: {hora_jogo}\n"
                print(mensagem)
            await self.enviar_mensagem(mensagem)
        else:
            logger.info("Não há jogos para hoje.")

    async def monitorar_jogos(self):
        """Monitora jogos ao vivo no primeiro tempo e envia apostas encontradas."""
        logger.info("\n=== Monitorando jogos ao vivo no primeiro tempo ===\n")
        jogos = self.api_football.listar_jogos_HT()
        if jogos:
            for jogo in jogos:
                fixture_id = jogo["fixture"]["id"]

                # Verifica se o jogo já foi enviado
                if fixture_id in self.jogos_enviados:
                    continue  # Ignora jogos já processados

                logger.info("\n=== Listando jogos ao vivo no primeiro tempo 1H ===")
                time_favorito = self.api_football.verificar_criterios(jogo)  # Obter o time favorito
                if time_favorito:  # Se houver um time favorito que atenda aos critérios
                    time_casa = jogo["teams"]["home"]["name"]
                    time_fora = jogo["teams"]["away"]["name"]

                    aposta = (
                        f"BET FOUND:\n\n"
                        f"{time_casa} x {time_fora}\n"
                        f"Site: www.orbitxch.com\n"
                        f"Bet on team: {time_favorito} +0.5 gols HT\n\nBET NOW"
                    )
                    await self.enviar_mensagem(aposta)

                    # Marca o jogo como enviado
                    self.jogos_enviados.add(fixture_id)
                else:
                    logger.info("Jogo não satisfez os critérios")
        else:
            logger.info("Não há jogos ao vivo no momento.")

async def job_jogos_do_dia(api_football, telegram_bot):
    """Executa os jobs do bot."""
    await telegram_bot.enviar_jogos_do_dia()

async def job_monitorar(api_football, telegram_bot):
    """Executa os jobs do bot."""
    await telegram_bot.monitorar_jogos()

async def job_limpar_cache(telegram_bot):
    """Limpa o cache de mensagens enviadas."""
    telegram_bot.jogos_enviados.clear()
    logger.info("Cache de mensagens enviadas limpo.")

async def start_scheduler(api_football, telegram_bot):
    """Inicia o agendador para executar jobs."""
    scheduler = AsyncIOScheduler(timezone=timezone('Europe/London'))

    # Adiciona os jobs ao agendador
    scheduler.add_job(job_jogos_do_dia, "cron", hour=10, minute=0, args=[api_football, telegram_bot])
    scheduler.add_job(job_monitorar, "cron", minute="*", hour="10-23", args=[api_football, telegram_bot])
    
    # Job para limpar o cache, configure o horário desejado (exemplo: meia-noite)
    scheduler.add_job(job_limpar_cache, "cron", hour=0, minute=0, args=[telegram_bot])

    # Inicia o agendador
    scheduler.start()

    # Mantém o agendador rodando indefinidamente
    while True:
        await asyncio.sleep(10)  # Dorme por 10 segundos, mas mantém o agendador ativo


@app.route("/events")
def events():
    """Rota SSE para receber as atualizações em tempo real."""
    def generate():
        # Este gerador envia eventos SSE para o cliente
        while True:
            yield f"data: {json.dumps({'message': 'Aguardando atualizações'})}\n\n"
    return Response(generate(), content_type='text/event-stream')

@app.route("/health")
def health_check():
    """Endpoint para checar se o serviço está ativo."""
    logger.info("Acessando o endpoint /health para verificação de integridade")
    return jsonify({"status": "running"}), 200

async def main():
    # Definir sua chave da API e token do Telegram
    api_key = "49dcecff9c9746a678c6b2887af923b1"  # Substitua com sua chave da API
    telegram_token = "8195835290:AAHnsVeIY_fS_Nmi9tkKl_e9JskMoZ4y1Zk"  # Substitua com seu token do Telegram
    chat_id = "-1002279145550"  # Substitua com o ID do chat para enviar as mensagens

    # Inicializa a classe FootballAPI
    api_football = FootballAPI(api_key)

    # Inicializa a classe TelegramBot
    telegram_bot = TelegramBot(api_football, telegram_token, chat_id)

    # Inicia o scheduler em segundo plano
    asyncio.create_task(start_scheduler(api_football, telegram_bot))

    # Configuração do Hypercorn
    config = Config()
    port = int(os.environ.get("PORT", 8080))  # Obtém a porta da variável de ambiente ou usa 8080 por padrão
    config.bind = [f"0.0.0.0:{port}"]  # Configura o Hypercorn para usar essa porta

    # Inicia o servidor Hypercorn
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())
