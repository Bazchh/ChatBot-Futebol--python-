import json
from datetime import datetime

class APIFootball:
    def __init__(self, api_key=None):
        self.api_key = api_key
        # Não vamos usar a conexão real, pois estamos criando um jogo fictício
        self.host = "v3.football.api-sports.io"

    def listar_jogos_do_dia(self, fixture_id=None):
        # Criação de um jogo fictício que atenda aos requisitos
        jogos_ficticios = [
            {
                "fixture": {"id": 123456, "date": "2025-01-18T15:30:00+00:00"},
                "teams": {
                    "home": {"name": "Time A"},
                    "away": {"name": "Time B"}
                }
            }
        ]
        
        # Se um fixture_id for passado, encontrar o jogo correspondente
        if fixture_id:
            jogos = [jogo for jogo in jogos_ficticios if jogo["fixture"]["id"] == fixture_id]
        else:
            jogos = jogos_ficticios

        # Verificando e formatando os jogos
        if jogos:
            for jogo in jogos:
                fixture_id = jogo["fixture"]["id"]
                # Obtendo as odds para o jogo fictício (odds menores que 1.50)
                odds = self.obter_odds(fixture_id)
                if odds:
                    odd_casa = odds.get("home", None)
                    odd_fora = odds.get("away", None)
                    
                    # Critérios de ativação (odds menores ou iguais a 1.50)
                    if odd_casa and odd_fora and odd_casa <= 1.50 and odd_fora <= 1.50:
                        # Formatação do horário e nomes dos times
                        time_casa = jogo["teams"]["home"]["name"]
                        time_fora = jogo["teams"]["away"]["name"]
                        data_jogo = jogo["fixture"]["date"]
                        hora_jogo = datetime.strptime(data_jogo, "%Y-%m-%dT%H:%M:%S+00:00").strftime("%H:%M")
                        # Exibindo os jogos do dia
                        print(f"{time_casa} x {time_fora} - Hora: {hora_jogo} - id {fixture_id}")
                        self.gerar_mensagem_aposta(time_casa, time_fora, odd_casa, odd_fora, hora_jogo)
        else:
            print("Não há jogos programados para hoje.")

    def obter_odds(self, fixture_id):
        """Retorna odds fictícias para o jogo"""
        # Odds fictícias para o jogo (menores que 1.50 para atender ao critério)
        if fixture_id == 123456:
            return {"home": 1.45, "away": 1.40}
        return None

    def gerar_mensagem_aposta(self, time_casa, time_fora, odd_casa, odd_fora, hora_jogo):
        """Gera a mensagem com a recomendação de aposta"""
        aposta = f"{time_casa} {odd_casa} x {time_fora} {odd_fora}\n"
        aposta += f"Aposta: {time_casa} +0.5 gols HT\n\n"
        aposta += "BET NOW\n"
        print(aposta)


# Exemplo de uso para um jogo fictício
if __name__ == "__main__":
    api_key = "49dcecff9c9746a678c6b2887af923b1"  # Não usado no exemplo atual
    api_football = APIFootball(api_key)
    # Usando o jogo fictício para teste
    api_football.listar_jogos_do_dia(fixture_id=123456)
