class PreMatch:
    def __init__(self, api_client):
        self.api_client = api_client

    def get_favorite_matches(self, date):
        """
        Obtém todas as partidas com equipes favoritas que atendem aos critérios pré-jogo.
        :param date: Data das partidas no formato 'YYYY-MM-DD'.
        :return: Lista de partidas que atendem aos critérios.
        """
        matches_data = self.api_client.get_fixtures_by_date(date)
        if not matches_data:
            print("Erro ao obter partidas.")
            return []

        matches = matches_data.get("response", [])
        favorite_matches = []

        for match in matches:
            # Substituir pela lógica correta para obter odds e estatísticas
            odds = match.get("odds", {}).get("1", {}).get("value", None)
            stats = match.get("statistics", {})
            success_rate = stats.get("first_half_success", 0)

            if odds is not None and odds <= 1.50 and success_rate >= 80:
                favorite_matches.append({
                    "match_id": match.get("fixture", {}).get("id"),
                    "home_team": match.get("teams", {}).get("home", {}).get("name", ""),
                    "away_team": match.get("teams", {}).get("away", {}).get("name", ""),
                    "odds": odds,
                    "success_rate": success_rate
                })

        return favorite_matches

    def display_favorites(self, date):
        """
        Exibe as informações das partidas que atendem aos critérios pré-jogo.
        :param date: Data das partidas no formato 'YYYY-MM-DD'.
        """
        favorite_matches = self.get_favorite_matches(date)
        if not favorite_matches:
            print("Nenhuma partida favorita encontrada com os critérios definidos.")
            return

        print(f"Partidas favoritas para {date}:")
        for match in favorite_matches:
            home_team = match['home_team']
            away_team = match['away_team']
            favorite_team = home_team if home_team == match['home_team'] else away_team
            
            # Formatação da mensagem
            message = f"Partida: {home_team} vs {away_team}\n"
            message += "+0.5 gols HT\n"
            message += f"Aposte no {favorite_team}\n"
            message += "**BET NOW**"

            # Enviar mensagem
            self.send_message(message)
