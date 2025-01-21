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
        jogos_filtrados = []  # Lista para armazenar os jogos filtrados
        # Verificando e formatando os jogos
        if jogos["results"] > 0:
            for jogo in jogos["response"]:
                # Verificando o status do jogo, apenas "1H" (primeiro tempo em andamento)
                status_jogo = jogo["fixture"]["status"]["short"]
                tempo_elapsed = jogo["fixture"]["status"]["elapsed"]

                # Verificando se o jogo está no primeiro tempo e se o tempo está entre 35 e 45 minutos
                if status_jogo == "1H" and (35 <= tempo_elapsed <= 45):
                    print(tempo_elapsed)
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

        # Critérios de jogo empatado em 0x0 ou 1x1
        if (gols_casa == 0 and gols_fora == 0) or (gols_casa == 1 and gols_fora == 1):
            odds = self.obter_odds(fixture_id)
            if odds:
                if self.posse_de_bola_suficiente(jogo, "home") and self.verificar_chutes(jogo, "home"):
                    chances_favorito = self.chances_de_gol_HT(time_casa, time_fora, jogo, jogo["fixture"]["date"])
                    if chances_favorito is not None and chances_favorito >= 0.75:
                        return time_casa  # Time favorito é o mandante
                elif self.posse_de_bola_suficiente(jogo, "away") and self.verificar_chutes(jogo, "away"):
                    chances_favorito = self.chances_de_gol_HT(time_casa, time_fora, jogo, jogo["fixture"]["date"])
                    if chances_favorito is not None and chances_favorito >= 0.75:
                        return time_fora  # Time favorito é o visitante

        # Critérios de jogo 0x1 ou 1x0
        if gols_casa == 0 and gols_fora == 1:
            odds = self.obter_odds(fixture_id)
            if odds and odds.get("home") <= 1.80:
                if self.posse_de_bola_suficiente(jogo, "home") and self.verificar_chutes(jogo, "home"):
                    chances_favorito = self.chances_de_gol_HT(time_casa, time_fora, jogo, jogo["fixture"]["date"])
                    if chances_favorito is not None and chances_favorito >= 0.75:
                        return time_casa  # Time favorito é o mandante

        elif gols_casa == 1 and gols_fora == 0:
            odds = self.obter_odds(fixture_id)
            if odds and odds.get("away") <= 1.80:
                if self.posse_de_bola_suficiente(jogo, "away") and self.verificar_chutes(jogo, "away"):
                    chances_favorito = self.chances_de_gol_HT(time_casa, time_fora, jogo, jogo["fixture"]["date"])
                    if chances_favorito is not None and chances_favorito >= 0.75:
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
                            if posse_bola_num >= 58:
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
                        if chutes is not None and chutes >= 7:  # Verifica se o total de chutes é maior ou igual a 7
                            return True
        return False

    def listar_jogos_do_dia(self):
        print("\n=== Listando jogos programados para hoje (ainda não iniciados) ===\n")
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        # Obtendo a data de hoje em formato YYYY-MM-DD no UTC
        data_atual = datetime.now(pytz.utc).strftime("%Y-%m-%d")

        # Realizando a requisição para pegar todos os jogos do dia
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
            print("Não há jogos programados para hoje.")
        
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
        self.conn.request(f"GET", f"/teams/statistics?season=2019&team={favorito_id}&league=39", headers=headers)
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
        
        # Considerando também a posse de bola e os chutes para refinar a probabilidade
        if self.posse_de_bola_suficiente(jogo, "home") and self.verificar_chutes(jogo, "home"):
            probabilidade_primeiro_tempo += 0.10  # Aumenta a chance se o time tiver boa posse de bola e muitos chutes

        # Retornando a probabilidade final
        return min(probabilidade_primeiro_tempo, 1.0)  # Limita a probabilidade a 100%
