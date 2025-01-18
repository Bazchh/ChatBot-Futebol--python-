import sys
sys.path.append("..")  # Adiciona o diretório pai ao caminho de importação
from datetime import datetime
from core.api import APIFootballClient  # Substitua com o caminho correto para o seu módulo

def test_get_all_matches_today():
    # Cria a instância do cliente da API
    api_client = APIFootballClient()

    # Obtém todos os jogos de hoje
    matches = api_client.get_all_matches_today()

    # Imprime os confrontos
    if matches:
        for match in matches["response"]:  # A chave correta para a resposta dos jogos
            print(f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}")
    else:
        print("Nenhum jogo encontrado para hoje.")

if __name__ == "__main__":
    test_get_all_matches_today()
