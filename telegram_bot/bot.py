import asyncio
import sys
sys.path.append("..")  # Adiciona o diretório pai ao caminho de importação
import pytz
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # Usando AsyncIOScheduler
from telegram import Bot
from core.api import APIFootball  # Certifique-se de que a classe APIFootball está no mesmo diretório

class TelegramBot:
    def __init__(self, api_football, telegram_token, chat_id):
        self.api_football = api_football
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.bot = Bot(token=self.telegram_token)

    async def enviar_mensagem_boas_vindas(self):
        mensagem_boas_vindas = "Olá, bem-vindo ao bot de futebol! Eu posso te ajudar com informações sobre os jogos de futebol e acompanhar jogos ao vivo. Fique ligado!"
        await self.bot.send_message(chat_id=self.chat_id, text=mensagem_boas_vindas)

    async def enviar_jogos_do_dia(self):
        print("\n=== Enviando jogos do dia ===\n")
        jogos = self.api_football.listar_jogos_do_dia()  # Usando o método da APIFootball para pegar os jogos

        if jogos:
            mensagem = "Jogos de futebol de hoje:\n"
            for jogo in jogos:
                # Verificando se as chaves estão presentes
                time_casa = jogo.get("time_casa", "Desconhecido")
                time_fora = jogo.get("time_fora", "Desconhecido")
                hora_jogo = jogo.get("hora_jogo", "Data não disponível")
                
                mensagem += f"{time_casa} x {time_fora} - Hora: {hora_jogo}\n"

            # Envia a mensagem no chat do Telegram
            await self.bot.send_message(chat_id=self.chat_id, text=mensagem)

        else:
            print("Não há jogos para hoje.")

    async def monitorar_jogos(self):
        print("\n=== Monitorando jogos ao vivo no primeiro tempo ===\n")
        jogos = self.api_football.listar_jogos_HT()  # Usando o método da APIFootball para monitorar os jogos ao vivo

        if jogos:
            for jogo in jogos:
                time_casa = jogo["teams"]["home"]["name"]
                time_fora = jogo["teams"]["away"]["name"]
                hora_jogo = jogo["fixture"]["date"]

                # Convertendo o formato da hora para 'HH:MM' (hora e minuto)
                hora_jogo = datetime.fromisoformat(hora_jogo).strftime('%H:%M')

                # Formatando a mensagem
                mensagem = f"{time_casa} x {time_fora} - Hora: {hora_jogo}"

                # Enviar a mensagem
                await self.bot.send_message(chat_id=self.chat_id, text=mensagem)

        else:
            print("Não há jogos ao vivo no momento.")   

# Função para enviar a lista de jogos às 15h15 e começar a monitorar os jogos ao vivo
async def job(api_football, telegram_bot):
    # Envia a lista de jogos às 15h15
    await telegram_bot.enviar_jogos_do_dia()  

    # Inicia o monitoramento dos jogos ao vivo
    await telegram_bot.monitorar_jogos()  

async def start_scheduler(api_football, telegram_bot):
    # Scheduler para rodar a função às 17h13 todos os dias
    scheduler = AsyncIOScheduler()  # Usando AsyncIOScheduler

    # Agendar a execução do job
    scheduler.add_job(job, 'cron', hour=17, minute=54, args=[api_football, telegram_bot])

    # Iniciar o agendador
    scheduler.start()

    # Manter o loop ativo
    await asyncio.Event().wait()  # Esse comando faz o loop rodar indefinidamente

def main():
    # Definir sua chave da API e token do Telegram
    api_key = "49dcecff9c9746a678c6b2887af923b1"  # Substitua com sua chave da API
    telegram_token = "7948020728:AAEzjLZzu58hLD6_cruXS6BUtwKl48RnVz8"  # Substitua com seu token do Telegram
    chat_id = "-1002440594973"  # Substitua com o ID do chat para enviar as mensagens

    # Inicializa a classe APIFootball
    api_football = APIFootball(api_key)

    # Inicializa a classe TelegramBot
    telegram_bot = TelegramBot(api_football, telegram_token, chat_id)

    # Rodar o scheduler usando asyncio.run()
    asyncio.run(start_scheduler(api_football, telegram_bot))  # Utiliza asyncio.run() para executar o loop

if __name__ == "__main__":
    main()
