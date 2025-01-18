class LiveMatch:
    def __init__(self, api_client):
        self.api_client = api_client

    def get_favorite_team(self, match_id):
        """
        Determina a equipe favorita com base na odd e nas estatísticas de sucesso.
        :param match_id: ID da partida a ser verificada.
        :return: O time favorito (pode ser a casa ou fora).
        """
        match_data = self.api_client.get_live_stats(match_id)
        if not match_data:
            print(f"Não foi possível obter dados para o jogo {match_id}.")
            return None

        match_info = match_data.get("response", [{}])[0]
        odds = match_info.get("odds", {})
        home_team = match_info.get("teams", {}).get("home", {}).get("name", "")
        away_team = match_info.get("teams", {}).get("away", {}).get("name", "")
        
        home_odds = odds.get("home", 0)
        away_odds = odds.get("away", 0)

        if home_odds <= 1.50 and home_odds < away_odds:
            return home_team
        elif away_odds <= 1.50 and away_odds < home_odds:
            return away_team
        return None

    def get_live_stats(self, match_id):
        """
        Obtém as estatísticas ao vivo da partida, focando na equipe favorita.
        :param match_id: ID da partida a ser verificada.
        :return: Possessão de bola e total de remates da equipe favorita.
        """
        match_data = self.api_client.get_live_stats(match_id)
        if not match_data:
            print("Erro ao obter estatísticas ao vivo.")
            return None, None

        match_info = match_data.get("response", [{}])[0]
        favorite_team = self.get_favorite_team(match_id)
        if not favorite_team:
            print("Equipe favorita não identificada.")
            return None, None

        teams = match_info.get("teams", {})
        home_team = teams.get("home", {}).get("name", "")
        away_team = teams.get("away", {}).get("name", "")

        if favorite_team == home_team:
            stats = match_info.get("statistics", {}).get("home", {})
        elif favorite_team == away_team:
            stats = match_info.get("statistics", {}).get("away", {})
        else:
            print(f"Estatísticas não encontradas para o time {favorite_team}.")
            return None, None

        possession = stats.get("possession", {}).get("percent", 0)
        total_shots = stats.get("shots", {}).get("total", 0)
        return possession, total_shots

    def check_activation_criteria(self, possession, total_shots, match_status):
        return possession >= 58 and total_shots >= 7 and match_status in ['0-0', '0-1', '1-0']

    def send_alert(self, match_id):
        # Obter informações do jogo
        match_data = self.api_client.get_live_stats(match_id)
        if not match_data:
            print(f"Erro ao obter dados para a partida {match_id}.")
            return

        match_info = match_data.get("response", [{}])[0]
        home_team = match_info.get("teams", {}).get("home", {}).get("name", "")
        away_team = match_info.get("teams", {}).get("away", {}).get("name", "")

        # Definir a aposta sugerida (supondo que estamos apostando no time da casa)
        favorite_team = self.get_favorite_team(match_id)
        if not favorite_team:
            print("Não foi possível identificar o time favorito.")
            return
        
        # Formatação da mensagem
        message = f"Partida: {home_team} vs {away_team}\n"
        message += "+0.5 gols HT\n"
        message += f"Aposte no {favorite_team}\n"
        message += "**BET NOW**"

        # Enviar mensagem
        self.send_message(message)


    def monitor_live_match(self, match_id, match_status):
        possession, total_shots = self.get_live_stats(match_id)
        if possession is None or total_shots is None:
            return

        if self.check_activation_criteria(possession, total_shots, match_status):
            self.send_alert(match_id)
        else:
            print(f"Critérios não atendidos para a partida {match_id}.")
