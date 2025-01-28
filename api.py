import http.client
import json
from datetime import datetime
import pytz

class FootballAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.host = "v3.football.api-sports.io"
        self.conn = http.client.HTTPSConnection(self.host)

    def listar_jogos_HT(self):
        """Lista jogos que estão no intervalo desejado do primeiro tempo (30-45 minutos)."""
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }
        
        self.conn.request("GET", "/fixtures?live=all", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        ligas_selecionadas =  [
            871, 39, 97, 94, 95, 143, 439, 440, 735, 461, 66, 153, 675, 88, 89, 78, 1034, 218, 484, 197, 736, 209, 599,
            1044, 901, 899, 774, 775, 181, 179, 183, 704, 137, 253, 101, 293, 972, 482, 648, 191, 504, 307, 667, 810, 129
        ]
        jogos = json.loads(data.decode("utf-8"))
        jogos_filtrados = []

        if jogos["results"] > 0:
            for jogo in jogos["response"]:
                status_jogo = jogo["fixture"]["status"]["short"]
                tempo_elapsed = jogo["fixture"]["status"].get("elapsed", 0)
                id_liga = jogo["league"]["id"]

                if status_jogo == "1H" and (30 <= tempo_elapsed <= 45) and id_liga in ligas_selecionadas:
                    jogos_filtrados.append(jogo)

        return jogos_filtrados

    def verificar_criterios(self, jogo):
        """Verifica os critérios para apostar com base no placar e nas odds."""
        time_casa = jogo["teams"]["home"]["name"]
        time_fora = jogo["teams"]["away"]["name"]
        fixture_id = jogo["fixture"]["id"]

        gols_casa = jogo["score"]["halftime"].get("home", 0)
        gols_fora = jogo["score"]["halftime"].get("away", 0)

        odds = self.obter_odds(fixture_id)
        if not odds:
            return None

        # Critérios para 0x0 e 1x1
        if (gols_casa == 0 and gols_fora == 0) or (gols_casa == 1 and gols_fora == 1):
            if odds.get("home") <= 1.80:
                print(f"Critério atendido: Apostar no time da casa ({time_casa}), Odd: {odds['home']}")
                return time_casa
            elif odds.get("away") <= 1.80:
                print(f"Critério atendido: Apostar no time visitante ({time_fora}), Odd: {odds['away']}")
                return time_fora

        # Critérios para 0x1 e 1x0
        if gols_casa == 0 and gols_fora == 1:
            if odds.get("home") <= 1.80:
                print(f"Critério atendido: Time da casa ({time_casa}) está perdendo por 1x0 e possui odd de {odds['home']}")
                return time_casa

        if gols_casa == 1 and gols_fora == 0:
            if odds.get("away") <= 1.80:
                print(f"Critério atendido: Time visitante ({time_fora}) está perdendo por 1x0 e possui odd de {odds['away']}")
                return time_fora

        return None

    def listar_jogos_do_dia(self):
        """Lista jogos das ligas específicas programados para hoje."""
        print("\n=== Listando jogos das ligas específicas programados para hoje ===\n")
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        league_ids = [
            871, 39, 97, 94, 95, 143, 439, 440, 735, 461, 66, 153, 675, 88, 89, 78, 1034, 218, 484, 197, 736, 209, 599,
            1044, 901, 899, 774, 775, 181, 179, 183, 704, 137, 253, 101, 293, 972, 482, 648, 191, 504, 307, 667, 810, 129
        ]

        data_atual = datetime.now(pytz.utc).strftime("%Y-%m-%d")
        self.conn.request("GET", f"/fixtures?date={data_atual}", headers=headers)
        res = self.conn.getresponse()
        data = res.read()
        jogos = json.loads(data.decode("utf-8"))
        hora_atual_utc = datetime.now(pytz.utc)
        jogos_do_dia = []

        if jogos["results"] > 0:
            for jogo in jogos["response"]:
                
                status_jogo = jogo["fixture"]["status"]["short"]
                
                if status_jogo != "NS":
                    continue

                id_liga = jogo["league"]["id"]
                if id_liga not in league_ids:
                    continue

                data_jogo = jogo["fixture"]["date"]
                hora_utc = datetime.strptime(data_jogo, "%Y-%m-%dT%H:%M:%S+00:00")
                hora_utc = pytz.utc.localize(hora_utc)

                if hora_utc < hora_atual_utc:
                    continue

                hora_brasilia = hora_utc.astimezone(pytz.timezone('America/Sao_Paulo')).strftime("%H:%M")
                time_casa = jogo["teams"]["home"]["name"]
                time_fora = jogo["teams"]["away"]["name"]
                fixture_id = jogo["fixture"]["id"]

                jogos_do_dia.append({
                    "time_casa": time_casa,
                    "time_fora": time_fora,
                    "hora_jogo": hora_brasilia,
                    "fixture_id": fixture_id
                })
        return jogos_do_dia

    def obter_odds(self, fixture_id):
        """Obtém as odds pré-jogo para a fixture especificada."""
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }

        self.conn.request("GET", f"/odds?fixture={fixture_id}&bookmaker=3", headers=headers)
        res = self.conn.getresponse()
        data = res.read()

        odds_data = json.loads(data.decode("utf-8"))
        if odds_data.get("results") > 0:
            bookmakers = odds_data["response"][0]["bookmakers"]
            for bookmaker in bookmakers:
                if bookmaker["id"] == 3:  # Betfair
                    for bet in bookmaker["bets"]:
                        if bet["name"] == "Home/Away":
                            values = bet["values"]
                            odd_casa = next((item['odd'] for item in values if item['value'] == 'Home'), None)
                            odd_fora = next((item['odd'] for item in values if item['value'] == 'Away'), None)
                            return {"home": float(odd_casa), "away": float(odd_fora)}
        return None
