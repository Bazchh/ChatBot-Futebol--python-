import http.client
import json
from datetime import datetime
import pytz

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
        
        # Definindo o fuso horário de Brasília
        tz_brasilia = pytz.timezone('America/Sao_Paulo')

        # Verificando e formatando os jogos
        if jogos["results"] > 0:
            for jogo in jogos["response"]:
                # Verificando o status do jogo, apenas "HT" (Halftime) será considerado
                status_jogo = jogo["fixture"]["status"]["short"]
                
                # Considerando apenas os jogos que estão no primeiro tempo (status "HT")
                if status_jogo != "HT":
                    continue

                data_jogo = jogo["fixture"]["date"]
                # Convertendo para o horário UTC primeiro
                hora_utc = datetime.strptime(data_jogo, "%Y-%m-%dT%H:%M:%S+00:00")
                hora_utc = pytz.utc.localize(hora_utc)  # Localizando no fuso horário UTC
                hora_brasilia = hora_utc.astimezone(tz_brasilia)  # Convertendo para o horário de Brasília
                hora_jogo = hora_brasilia.strftime("%H:%M")  # Formato final da hora

                time_casa = jogo["teams"]["home"]["name"]
                time_fora = jogo["teams"]["away"]["name"]
                fixture_id = jogo["fixture"]["id"]
                
                # Exibindo os jogos do dia
                print(f"{time_casa} x {time_fora} - Hora: {hora_jogo} - id {fixture_id}")

                # Obtendo as odds para o jogo
                odds = self.obter_odds(fixture_id)
                if odds:
                    odd_casa = odds.get("home", None)
                    odd_fora = odds.get("away", None)

                    favorito = None
                    adversario = None
                    favorito_id = None
                    adversario_id = None
                    
                    # Critérios de ativação (odds menores ou iguais a 1.50)
                    if odd_casa and odd_fora:
                        if odd_casa <= 1.50:
                            favorito = time_casa
                            adversario = time_fora
                            favorito_id = jogo["teams"]["home"]["id"]
                            adversario_id = jogo["teams"]["away"]["id"]
                        elif odd_fora <= 1.50:
                            favorito = time_fora
                            adversario = time_casa
                            favorito_id = jogo["teams"]["away"]["id"]
                            adversario_id = jogo["teams"]["home"]["id"]

                        if favorito_id and adversario_id:
                            # Analisando os confrontos entre o time favorito e o adversário
                            self.analisar_media_gols_primeiro_tempo(favorito_id, adversario_id, favorito, adversario, hora_jogo)
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

    def analisar_media_gols_primeiro_tempo(self, favorito_id, adversario_id, favorito, adversario, hora_jogo):
        """Analisa a média de gols no primeiro tempo (halftime) do time favorito nos confrontos H2H"""
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        # Obtendo confrontos anteriores entre os times
        self.conn.request("GET", f"/fixtures/headtohead?h2h={favorito_id}-{adversario_id}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()

        h2h_data = json.loads(data.decode("utf-8"))

        if h2h_data["results"] > 0:
            total_gols_primeiro_tempo = 0
            jogos = h2h_data["response"]

            # Calculando a média de gols no primeiro tempo (halftime) do time favorito
            for jogo in jogos:
                if "score" in jogo and "halftime" in jogo["score"]:
                    if jogo["teams"]["home"]["id"] == favorito_id:
                        gols_primeiro_tempo = jogo["score"]["halftime"]["home"]
                    elif jogo["teams"]["away"]["id"] == favorito_id:
                        gols_primeiro_tempo = jogo["score"]["halftime"]["away"]

                    # Verifica se o valor de gols_primeiro_tempo é válido antes de somar
                    if gols_primeiro_tempo is not None:
                        total_gols_primeiro_tempo += gols_primeiro_tempo

            if len(jogos) > 0:
                media_gols_primeiro_tempo = total_gols_primeiro_tempo / len(jogos)

                # Se a média de gols do favorito for superior a 1, gerar a recomendação
                if media_gols_primeiro_tempo > 1:
                    self.gerar_mensagem_aposta(favorito, adversario, hora_jogo, media_gols_primeiro_tempo)

    def gerar_mensagem_aposta(self, favorito, adversario, hora_jogo, media_gols_primeiro_tempo):
        """Gera a mensagem de recomendação de aposta"""
        aposta = f"{favorito} vs {adversario}\n"
        aposta += f"Média de gols no primeiro tempo: {media_gols_primeiro_tempo}\n"
        aposta += f"Aposta recomendada: {favorito} - Mais de 1 gol no primeiro tempo\n"
        aposta += f"Hora do jogo: {hora_jogo}\n"
        print(aposta)


# Exemplo de uso
if __name__ == "__main__":
    api_key = "49dcecff9c9746a678c6b2887af923b1"  # Substitua com sua chave da API
    api_football = APIFootball(api_key)
    api_football.listar_jogos_do_dia()
