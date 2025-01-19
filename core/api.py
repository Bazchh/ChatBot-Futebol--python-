import http.client
import json
from datetime import datetime
import pytz

class APIFootball:
    def __init__(self, api_key):
        self.api_key = api_key
        self.host = "v3.football.api-sports.io"
        self.conn = http.client.HTTPSConnection(self.host)

    def listar_jogos_HT(self):
        print("\n=== Listando jogos ao vivo no primeiro tempo 1H ===\n")
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        # Realizando a requisição para pegar os jogos ao vivo
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
                
                if status_jogo != "1H":
                    continue

                # Obtendo o tempo de jogo para garantir que estamos no intervalo
                tempo_elapsed = jogo["fixture"]["status"]["elapsed"]
                if tempo_elapsed < 37 or tempo_elapsed > 45:
                    continue

                # Obtendo os gols no primeiro tempo
                gols_casa = jogo["score"]["halftime"]["home"]
                gols_fora = jogo["score"]["halftime"]["away"]

                # Filtrando os jogos com as condições solicitadas
                if (gols_casa == 0 and gols_fora == 0) or (gols_casa == 1 and gols_fora == 1):
                    self._processar_jogo(favorito=None, adversario=None, jogo=jogo)
                elif gols_casa == 0 and gols_fora == 1:
                    time_casa = jogo["teams"]["home"]["name"]
                    time_fora = jogo["teams"]["away"]["name"]
                    odds = self.obter_odds(jogo["fixture"]["id"])
                    if odds and odds.get("home") <= 1.50:
                        if self.posse_de_bola_suficiente(jogo, "away") or self.verificar_chutes(jogo, "away"):
                            self._processar_jogo(favorito=time_fora, adversario=time_casa, jogo=jogo)
                elif gols_casa == 1 and gols_fora == 0:
                    time_casa = jogo["teams"]["home"]["name"]
                    time_fora = jogo["teams"]["away"]["name"]
                    odds = self.obter_odds(jogo["fixture"]["id"])
                    if odds and odds.get("away") <= 1.50:
                        if self.posse_de_bola_suficiente(jogo, "home") or self.verificar_chutes(jogo, "home"):
                            self._processar_jogo(favorito=time_casa, adversario=time_fora, jogo=jogo)
        else:
            print("Não há jogos no intervalo no momento.")

    def posse_de_bola_suficiente(self, jogo, time):
        
        # Verificando as estatísticas do jogo
        for estatistica in jogo["response"]:
            if estatistica["team"]["name"] == jogo["teams"][time]["name"]:
                for item in estatistica["statistics"]:
                    if item["type"] == "Ball Possession":
                        posse_bola = item["value"]
                        # Removendo o símbolo '%' e convertendo para número, se o valor estiver presente
                        if posse_bola is not None:
                            posse_bola_num = float(posse_bola.replace('%', ''))
                            
                            # Verificando se a posse de bola do time é suficiente
                            if posse_bola_num >= 58:  # Por exemplo, 58% ou mais
                                return True
        return False

    def verificar_chutes(self, jogo, time):        

        # Verificando as estatísticas do jogo para o total de chutes
        for estatistica in jogo["response"]:
            if estatistica["team"]["name"] == jogo["teams"][time]["name"]:
                for item in estatistica["statistics"]:
                    if item["type"] == "Total Shots":
                        chutes = item["value"]
                        if chutes is not None and chutes >= 7:  # Verifica se o total de chutes é maior ou igual a 7
                            return True
        return False

    def _processar_jogo(self, favorito, adversario, jogo):
        # Formatação da hora do jogo para o fuso horário de Brasília
        data_jogo = jogo["fixture"]["date"]
        hora_utc = datetime.strptime(data_jogo, "%Y-%m-%dT%H:%M:%S+00:00")
        hora_utc = pytz.utc.localize(hora_utc)
        hora_brasilia = hora_utc.astimezone(pytz.timezone('America/Sao_Paulo'))
        hora_jogo = hora_brasilia.strftime("%H:%M")

        time_casa = jogo["teams"]["home"]["name"]
        time_fora = jogo["teams"]["away"]["name"]
        fixture_id = jogo["fixture"]["id"]
        
        print(f"{time_casa} x {time_fora} - Hora: {hora_jogo} - id {fixture_id}")

        if favorito and adversario:
            self.analisar_media_gols_primeiro_tempo(favorito, adversario, jogo, hora_jogo)

    def obter_odds(self, fixture_id):
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        self.conn.request(f"GET", f"/odds?fixture={fixture_id}&bookmaker=6", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        
        odds_data = json.loads(data.decode("utf-8"))

        if odds_data.get("results") > 0:
            bookmakers = odds_data["response"][0]["bookmakers"]
            for bookmaker in bookmakers:
                if bookmaker["id"] == 6:  # Bwin
                    for bet in bookmaker["bets"]:
                        if bet["name"] == "Home/Away":
                            values = bet["values"]
                            odd_casa = next((item['odd'] for item in values if item['value'] == 'Home'), None)
                            odd_fora = next((item['odd'] for item in values if item['value'] == 'Away'), None)
                            return {"home": float(odd_casa), "away": float(odd_fora)}
        return None

    def analisar_media_gols_primeiro_tempo(self, favorito, adversario, jogo, hora_jogo):
        favorito_id = jogo["teams"]["home"]["id"] if jogo["teams"]["home"]["name"] == favorito else jogo["teams"]["away"]["id"]
        adversario_id = jogo["teams"]["away"]["id"] if jogo["teams"]["home"]["name"] == favorito else jogo["teams"]["home"]["id"]

        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        self.conn.request("GET", f"/fixtures/headtohead?h2h={favorito_id}-{adversario_id}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()

        h2h_data = json.loads(data.decode("utf-8"))

        if h2h_data["results"] > 0:
            total_gols_primeiro_tempo = 0
            jogos = h2h_data["response"]

            for jogo in jogos:
                if "score" in jogo and "halftime" in jogo["score"]:
                    if jogo["teams"]["home"]["id"] == favorito_id:
                        gols_primeiro_tempo = jogo["score"]["halftime"]["home"]
                    elif jogo["teams"]["away"]["id"] == favorito_id:
                        gols_primeiro_tempo = jogo["score"]["halftime"]["away"]

                    if gols_primeiro_tempo is not None:
                        total_gols_primeiro_tempo += gols_primeiro_tempo

            if len(jogos) > 0:
                media_gols_primeiro_tempo = total_gols_primeiro_tempo / len(jogos)

                if media_gols_primeiro_tempo > 1:
                    self.gerar_mensagem_aposta(favorito, adversario, hora_jogo, media_gols_primeiro_tempo)

    def gerar_mensagem_aposta(self, favorito, adversario, hora_jogo, media_gols_primeiro_tempo):
        aposta = f"\n--- Recomendação de Aposta ---\n"
        aposta += f"{favorito} vs {adversario}\n"
        aposta += f"Média de gols no primeiro tempo: {media_gols_primeiro_tempo}\n"
        aposta += f"Aposta recomendada: {favorito} - Mais de 1 gol no primeiro tempo\n"
        aposta += f"Hora do jogo: {hora_jogo}\n"
        print(aposta)


# Exemplo de uso
if __name__ == "__main__":
    api_key = "49dcecff9c9746a678c6b2887af923b1"  # Substitua com sua chave da API
    api_football = APIFootball(api_key)
    api_football.listar_jogos_HT()
