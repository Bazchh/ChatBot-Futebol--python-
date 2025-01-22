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
        print("\n=== Listando jogos ao vivo no primeiro tempo (1H) ===\n")
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        # IDs das ligas selecionadas
        ligas_selecionadas = [
            6979, 6712, 6280, 6335, 6336, 6445, 6419, 6418, 6315, 6310, 6313, 6314,
            6295, 6375, 6387, 6338, 6347, 6505, 6322, 6910, 6949, 6967, 6354, 6986,
            6374, 6435, 6552, 6958, 6860, 6950, 7016, 7005, 6962, 6521
        ]

        # Realizando a requisição para pegar os jogos ao vivo
        self.conn.request("GET", "/fixtures?live=all", headers=headers)
        res = self.conn.getresponse()
        data = res.read()

        # Convertendo o dado JSON
        jogos = json.loads(data.decode("utf-8"))
        jogos_filtrados = []  # Lista para armazenar os jogos filtrados

        # Verificando e formatando os jogos
        if jogos["results"] > 0:
            for jogo in jogos["response"]:
                # Verificando o status do jogo, apenas "1H" (primeiro tempo em andamento)
                status_jogo = jogo["fixture"]["status"]["short"]
                tempo_elapsed = jogo["fixture"]["status"]["elapsed"]
                id_liga = jogo["league"]["id"]

                # Filtrar jogos que estão nas ligas selecionadas e no intervalo de tempo desejado
                if status_jogo == "1H" and (35 <= tempo_elapsed <= 45) and id_liga in ligas_selecionadas:
                    print(f"Jogo: {jogo['teams']['home']['name']} vs {jogo['teams']['away']['name']}, Minuto: {tempo_elapsed}")
                    jogos_filtrados.append(jogo)

        return jogos_filtrados  # Retornando os jogos filtrados


    
    def verificar_criterios(self, jogo):
        """
        Verifica os critérios de aposta para um jogo específico e retorna o time favorito se os critérios forem atendidos.
        """
        time_casa = jogo["teams"]["home"]["name"]
        time_fora = jogo["teams"]["away"]["name"]
        fixture_id = jogo["fixture"]["id"]
        # Obtendo os gols no primeiro tempo
        gols_casa = jogo["score"]["halftime"]["home"]
        gols_fora = jogo["score"]["halftime"]["away"]

        if (gols_casa == 0 and gols_fora == 0) or (gols_casa == 1 and gols_fora == 1):
            odds = self.obter_odds(fixture_id)
            print(f"Odds obtidas: {odds}")
            if odds:
                if odds.get("home") <= 1.80:
                    print(f"Odd do time da casa ({time_casa}): {odds['home']}")
                    if self.posse_de_bola_suficiente(jogo, "home") and self.verificar_chutes(jogo, "home"):
                        chances_favorito = self.chances_de_gol_HT(time_casa, time_fora, jogo, jogo["fixture"]["date"])
                        if chances_favorito is not None and chances_favorito >= 0.65:
                            print(f"{time_casa} é o favorito com {chances_favorito*100:.2f}% de chances de gol no HT.")
                            return time_casa
                elif odds.get("away") <= 1.80:
                    print(f"Odd do time visitante ({time_fora}): {odds['away']}")
                    if self.posse_de_bola_suficiente(jogo, "away") and self.verificar_chutes(jogo, "away"):
                        chances_favorito = self.chances_de_gol_HT(time_casa, time_fora, jogo, jogo["fixture"]["date"])
                        if chances_favorito is not None and chances_favorito >= 0.65:
                            print(f"{time_fora} é o favorito com {chances_favorito*100:.2f}% de chances de gol no HT.")
                            return time_fora

        # Critérios de jogo 0x1 ou 1x0
        if gols_casa == 0 and gols_fora == 1:
            odds = self.obter_odds(fixture_id)
            if odds and odds.get("home") <= 1.80:
                if self.posse_de_bola_suficiente(jogo, "home") and self.verificar_chutes(jogo, "home"):
                    chances_favorito = self.chances_de_gol_HT(time_casa, time_fora, jogo, jogo["fixture"]["date"])
                    if chances_favorito is not None and chances_favorito >= 0.65:
                        return time_casa  # Time favorito é o mandante

        elif gols_casa == 1 and gols_fora == 0:
            odds = self.obter_odds(fixture_id)
            if odds and odds.get("away") <= 1.80:
                if self.posse_de_bola_suficiente(jogo, "away") and self.verificar_chutes(jogo, "away"):
                    chances_favorito = self.chances_de_gol_HT(time_casa, time_fora, jogo, jogo["fixture"]["date"])
                    if chances_favorito is not None and chances_favorito >= 0.65:
                        return time_fora  # Time favorito é o visitante

        return None  # Nenhum time atende aos critérios


    def posse_de_bola_suficiente(self, jogo, time):
        # Verificando se a chave 'response' existe
        response = jogo.get("response", [])
        
        # Caso a chave 'response' não exista ou esteja vazia, retorna False
        if not response:
            return False
        
        # Verificando as estatísticas do jogo
        for estatistica in response:
            if estatistica["team"]["name"] == jogo["teams"][time]["name"]:
                for item in estatistica["statistics"]:
                    if item["type"] == "Ball Possession":
                        posse_bola = item["value"]
                        if posse_bola is not None:
                            posse_bola_num = float(posse_bola.replace('%', ''))
                            if posse_bola_num >= 55:
                                return True
        return False

    def verificar_chutes(self, jogo, time):        
        response = jogo.get("response", [])
        
        # Caso a chave 'response' não exista ou esteja vazia, retorna False
        if not response:
            return False
        # Verificando as estatísticas do jogo para o total de chutes
        for estatisticas in response:
            if estatisticas["team"]["name"] == jogo["teams"][time]["name"]:
                for item in estatisticas["statistics"]:
                    if item["type"] == "Total Shots":
                        chutes = item["value"]
                        if chutes is not None and chutes >= 6:  # Verifica se o total de chutes é maior ou igual a 7
                            return True
        return False

    def listar_jogos_do_dia(self):
        print("\n=== Listando jogos das ligas específicas programados para hoje (ainda não iniciados) ===\n")
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        # IDs das ligas desejadas
        league_ids = [6979, 6712, 6280, 6335, 6336, 6445, 6419, 6418, 6315, 6310, 6313, 6314, 6295, 6375, 
                    6387, 6338, 6347, 6505, 6322, 6910, 6949, 6967, 6354, 6986, 6374, 6435, 6552, 6958, 
                    6860, 6950, 7016, 7005, 6962, 6521]

        # Obtendo a data de hoje no formato YYYY-MM-DD no UTC
        data_atual = datetime.now(pytz.utc).strftime("%Y-%m-%d")

        # Fazendo a requisição apenas para jogos do dia
        self.conn.request(f"GET", f"/fixtures?date={data_atual}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()

        # Convertendo o dado JSON
        jogos = json.loads(data.decode("utf-8"))

        # Obtendo a hora atual
        hora_atual_utc = datetime.now(pytz.utc)

        jogos_do_dia = []

        # Verificando e formatando os jogos
        if jogos["results"] > 0:
            for jogo in jogos["response"]:
                status_jogo = jogo["fixture"]["status"]["short"]

                # Filtrando apenas jogos que ainda não começaram (status "NS")
                if status_jogo != "NS":
                    continue

                # Filtrando pelas ligas desejadas
                id_liga = jogo["league"]["id"]
                if id_liga not in league_ids:
                    continue

                # Obtendo a data e hora do jogo
                data_jogo = jogo["fixture"]["date"]
                hora_utc = datetime.strptime(data_jogo, "%Y-%m-%dT%H:%M:%S+00:00")
                hora_utc = pytz.utc.localize(hora_utc)

                # Verificando se o jogo já passou
                if hora_utc < hora_atual_utc:
                    continue

                # Convertendo a hora para o fuso horário de Brasília
                hora_londres = hora_utc.astimezone(pytz.timezone('Europe/London'))
                hora_jogo = hora_londres.strftime("%H:%M")

                time_casa = jogo["teams"]["home"]["name"]
                time_fora = jogo["teams"]["away"]["name"]
                fixture_id = jogo["fixture"]["id"]

                # Adicionando o jogo à lista
                jogos_do_dia.append({
                    "time_casa": time_casa,
                    "time_fora": time_fora,
                    "hora_jogo": hora_jogo,
                    "fixture_id": fixture_id
                })
        else:
            print("Não há jogos programados para hoje nas ligas específicas.")
        
        return jogos_do_dia


    def obter_odds(self, fixture_id):
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        self.conn.request(f"GET", f"/odds?fixture={fixture_id}&bookmaker=3", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        
        odds_data = json.loads(data.decode("utf-8"))
        if odds_data.get("results") > 0:
            bookmakers = odds_data["response"][0]["bookmakers"]
            for bookmaker in bookmakers:
                if bookmaker["id"] == 3:  #betfair
                    for bet in bookmaker["bets"]:
                        if bet["name"] == "Home/Away":
                            values = bet["values"]
                            odd_casa = next((item['odd'] for item in values if item['value'] == 'Home'), None)
                            odd_fora = next((item['odd'] for item in values if item['value'] == 'Away'), None)
                            return {"home": float(odd_casa), "away": float(odd_fora)}
        return None
    
    def chances_de_gol_HT(self, favorito, adversario, jogo, hora_jogo):
        # Obtendo os dados do time favorito e adversário
        time_casa = jogo["teams"]["home"]["name"]
        time_fora = jogo["teams"]["away"]["name"]
        favorito_id = jogo["teams"]["home"]["id"] if time_casa == favorito else jogo["teams"]["away"]["id"]
        adversario_id = jogo["teams"]["away"]["id"] if time_casa == favorito else jogo["teams"]["home"]["id"]
        
        # Realizando a requisição para pegar as estatísticas do time favorito
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        # Obtendo as estatísticas de gols do time favorito
        self.conn.request(f"GET", f"/teams/statistics?season={jogo['league']['season']}&team={favorito_id}&league={jogo['league']['id']}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()

        stats = json.loads(data.decode("utf-8"))
        if stats.get("results") == 0:
            print(f"Não há dados de estatísticas para o time {favorito}")
            return None

        # Obtendo o total de gols marcados no primeiro tempo
        gols_primeiro_tempo = stats["response"]["goals"]["for"]["minute"]["0-15"]["total"] + stats["response"]["goals"]["for"]["minute"]["16-30"]["total"] + stats["response"]["goals"]["for"]["minute"]["31-45"]["total"]
        
        # Calculando o total de gols do time em toda a temporada
        total_gols = stats["response"]["goals"]["for"]["total"]["total"]  # Total de gols no campeonato
        if total_gols == 0:
            print(f"{favorito} não marcou gols em toda a temporada!")
            return None
        
        # Calculando a probabilidade de marcar no primeiro tempo
        probabilidade_primeiro_tempo = gols_primeiro_tempo / total_gols if total_gols > 0 else 0  # Probabilidade relativa aos gols totais

        print(f"Probabilidade de {favorito} marcar no primeiro tempo: {probabilidade_primeiro_tempo * 100:.2f}%")

        # Retornando a probabilidade final
        return min(probabilidade_primeiro_tempo, 1.0)  # Limita a probabilidade a 100%
