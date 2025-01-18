import requests
from telegram import Bot
from telegram.ext import Application, MessageHandler, filters
from core.pre_match import PreMatch  # Supondo que você tenha uma classe PreMatch configurada
from core.live_match import LiveMatch  # Supondo que você tenha uma classe Live configurada
from core.api import APIFootballClient
import asyncio
from datetime import datetime

class TelegramBot:
    def __init__(self, api_key, group_id):
        self.api_key = api_key
        self.group_id = group_id
        self.bot = Bot(token=self.api_key)

        # Usando a nova maneira de inicializar o bot com Application
        self.application = Application.builder().token(self.api_key).build()

        # Inicializando as classes de PreMatch e Live
        self.api_client = APIFootballClient()  # A API do futebol deve ser configurada corretamente
        self.pre_match = PreMatch(self.api_client)
        self.live = LiveMatch(self.api_client)

    def start(self):
        # Configura o manipulador para mensagens de texto (sem comandos)
        message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)

        # Em vez de acessar diretamente o 'dispatcher', usa-se diretamente 'add_handler'
        self.application.add_handler(message_handler)

        # Inicia o bot de maneira assíncrona
        self.application.run_polling()

        # Chama a função de envio das partidas do dia de maneira assíncrona
        asyncio.run(self.send_todays_matches())  # Faz a chamada assíncrona para as partidas de hoje

        # Inicia a atualização periódica para enviar alertas
        asyncio.run(self.start_periodic_updates())  # Usamos asyncio aqui para garantir que as tarefas sejam assíncronas

    async def send_todays_matches(self):
        """
        Envia uma lista de todas as partidas do dia para o grupo assim que o bot iniciar.
        """
        # Obter a data atual no formato 'YYYY-MM-DD'
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Obter todas as partidas do dia (não apenas as favoritas)
        all_matches_data = self.api_client.make_request("fixtures", params={"date": current_date})
        
        if not all_matches_data or 'response' not in all_matches_data:
            await self.send_message("Nenhuma partida encontrada para hoje.")
            return

        message = f"Partidas do dia {current_date}:\n"

        for match in all_matches_data['response']:
            home_team = match['teams']['home']['name']
            away_team = match['teams']['away']['name']
            
            # Formatação da mensagem
            message += f"{home_team} vs {away_team}\n"
            message += "---------------------\n"

        # Enviar a mensagem com as partidas do dia
        await self.send_message(message)

    async def start_periodic_updates(self):
        """
        Inicia um loop assíncrono para enviar atualizações periódicas sobre jogos de futebol.
        """
        while True:
            # Obter a data atual no formato 'YYYY-MM-DD'
            current_date = datetime.now().strftime("%Y-%m-%d")

            # Buscar partidas ao vivo e pré-jogo
            live_matches_data = self.api_client.make_request("fixtures", params={"live": "true"})
            pre_match_matches = self.pre_match.get_favorite_matches(current_date)  # Usando a data atual

            # Enviar alertas de partidas ao vivo
            if live_matches_data:
                live_matches = live_matches_data.get("response", [])
                for match in live_matches:
                    match_id = match.get("fixture", {}).get("id")
                    if match_id:
                        # Obter as estatísticas da partida ao vivo
                        possession, total_shots = self.live.get_live_stats(match_id)
                        if possession is not None and total_shots is not None:
                            message = f"Partida ao vivo: {match['teams']['home']['name']} vs {match['teams']['away']['name']}\n"
                            message += f"Posse de bola: {possession}%\nTotal de remates: {total_shots}\n"
                            await self.send_message(message)

            # Enviar alertas de partidas pré-jogo
            for match in pre_match_matches:
                message = f"Partida: {match['home_team']} vs {match['away_team']}\n"
                message += "+0.5 gols HT\n"
                message += f"Aposte no {match['home_team'] if match['odds'] < 1.50 else match['away_team']}\n"
                message += "**BET NOW**"
                await self.send_message(message)

            # Espera 30 minutos antes de buscar novos dados
            await asyncio.sleep(1800)  # Usando asyncio.sleep para aguardar de maneira assíncrona

    async def send_message(self, message):
        """
        Envia uma mensagem para o grupo do Telegram.
        :param message: A mensagem a ser enviada.
        """
        try:
            await self.bot.send_message(chat_id=self.group_id, text=message)
        except Exception as e:
            print(f"Erro ao enviar mensagem para o grupo: {e}")

    def handle_message(self, update, context):
        """
        Função para lidar com mensagens, caso necessário.
        (Você pode customizar conforme sua necessidade).
        """
        message = update.message.text
        print(f"Recebida mensagem: {message}")
        # Adicione o tratamento para mensagens recebidas, se necessário
