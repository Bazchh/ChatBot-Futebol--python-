import asyncio
import sys
sys.path.append("..")  # Adiciona o diretório pai ao caminho de importação
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from core.api import APIFootball  # Certifique-se de que APIFootball esteja configurada corretamente
from pytz import timezone

class TelegramBot:
    def __init__(self, api_football, telegram_token, chat_id):
        self.api_football = api_football
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.bot = Bot(token=self.telegram_token)

    async def enviar_mensagem(self, mensagem):
        """Envia uma mensagem para o chat do Telegram."""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=mensagem)
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")

    async def enviar_jogos_do_dia(self):
        """Busca e envia a lista de jogos do dia."""
        print("\n=== Enviando jogos do dia ===\n")
        jogos = self.api_football.listar_jogos_do_dia()
        if jogos:
            mensagem = "Football games today:\n"
            for jogo in jogos:
                time_casa = jogo.get("time_casa", "Desconhecido")
                time_fora = jogo.get("time_fora", "Desconhecido")
                hora_jogo = jogo.get("hora_jogo", "Data não disponível")
                mensagem += f"{time_casa} x {time_fora} - Time: {hora_jogo}\n"
            await self.enviar_mensagem(mensagem)
        else:
            print("Não há jogos para hoje.")

    async def monitorar_jogos(self):
        """Monitora jogos ao vivo no primeiro tempo e envia apostas encontradas."""
        print("\n=== Monitorando jogos ao vivo no primeiro tempo ===\n")
        jogos = self.api_football.listar_jogos_HT()
        if jogos:
            for jogo in jogos:
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
                else:
                    print("Jogo não satisfez os critérios")
        else:
            print("Não há jogos ao vivo no momento.")
        

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
    scheduler.add_job(job_monitorar,"interval",seconds=5,args=[api_football,telegram_bot])
    scheduler.start()
    await asyncio.Event().wait()


def main():
    # Definir sua chave da API e token do Telegram
    api_key = "49dcecff9c9746a678c6b2887af923b1"  # Substitua com sua chave da API
    telegram_token = "8195835290:AAHnsVeIY_fS_Nmi9tkKl_e9JskMoZ4y1Zk"  # Substitua com seu token do Telegram
    chat_id = "-1002279145550"  # Substitua com o ID do chat para enviar as mensagens

    # Inicializa a classe APIFootball
    api_football = APIFootball(api_key)

    # Inicializa a classe TelegramBot
    telegram_bot = TelegramBot(api_football, telegram_token, chat_id)

    # Rodar o scheduler usando asyncio.run()
    asyncio.run(start_scheduler(api_football, telegram_bot))  # Utiliza asyncio.run() para executar o loop

if __name__ == "__main__":
    main()
