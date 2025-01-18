import http.client
import json
from datetime import datetime

class APIFootball:
    def __init__(self, api_key):
        self.api_key = api_key
        self.host = "v3.football.api-sports.io"
        self.conn = http.client.HTTPSConnection(self.host)

    def listar_jogos_do_dia(self):
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        # Realizando a requisição para pegar os jogos do dia
        self.conn.request("GET", "/fixtures?live=all", headers=headers)
        res = self.conn.getresponse()
        data = res.read()

        # Convertendo o dado JSON
        jogos = json.loads(data.decode("utf-8"))
        
        # Verificando e formatando os jogos
        if jogos["results"] > 0:
            for jogo in jogos["response"]:
                data_jogo = jogo["fixture"]["date"]
                hora_jogo = datetime.strptime(data_jogo, "%Y-%m-%dT%H:%M:%S+00:00").strftime("%H:%M")
                time_casa = jogo["teams"]["home"]["name"]
                time_fora = jogo["teams"]["away"]["name"]
                fixture_id = jogo["fixtu    re"]["id"]
                
                # Exibindo os jogos do dia
                print(f"{time_casa} x {time_fora} - Hora: {hora_jogo} - id {fixture_id}")

                # Obtendo as odds para o jogo
                odds = self.obter_odds(fixture_id)
                if odds:
                    odd_casa = odds.get("home", None)
                    odd_fora = odds.get("away", None)
                    
                    # Critérios de ativação (odds menores ou iguais a 1.50)
                    if odd_casa and odd_fora and odd_casa <= 1.50 and odd_fora <= 1.50:
                        self.gerar_mensagem_aposta(time_casa, time_fora, odd_casa, odd_fora, hora_jogo)
        else:
            print("Não há jogos programados para hoje.")

    def obter_odds(self, fixture_id):
        """Obtém as odds para o jogo usando o fixture_id"""
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        # Realizando a requisição para pegar as odds
        self.conn.request(f"GET", f"/odds?fixture={fixture_id}&bookmaker=6", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        
        odds_data = json.loads(data.decode("utf-8"))

        # Acessando as odds dentro da estrutura correta
        if odds_data.get("results") > 0:
            bookmakers = odds_data["response"][0]["bookmakers"]
            for bookmaker in bookmakers:
                if bookmaker["id"] == 6:  # Verifica se o bookmaker é o Bwin
                    for bet in bookmaker["bets"]:
                        if bet["name"] == "Home/Away":
                            values = bet["values"]
                            odd_casa = next((item['odd'] for item in values if item['value'] == 'Home'), None)
                            odd_fora = next((item['odd'] for item in values if item['value'] == 'Away'), None)
                            return {"home": float(odd_casa), "away": float(odd_fora)}
        
        return None

    def gerar_mensagem_aposta(self, time_casa, time_fora, odd_casa, odd_fora, hora_jogo):
        """Gera a mensagem com a recomendação de aposta"""
        aposta = f"{time_casa} {odd_casa} x {time_fora} {odd_fora}\n"
        aposta += f"Aposta: {time_casa} +0.5 gols HT\n\n"
        aposta += "BET NOW\n"
        print(aposta)


# Exemplo de uso
if __name__ == "__main__":
    api_key = "49dcecff9c9746a678c6b2887af923b1"  # Substitua com sua chave da API
    api_football = APIFootball(api_key)
    api_football.listar_jogos_do_dia()
