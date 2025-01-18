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
                id_jogo = jogo ["fixture"]["id"]
                # Exibindo os jogos do dia
                print(f"{time_casa} x {time_fora} - Hora: {hora_jogo} - id {id_jogo}")
        else:
            print("Não há jogos programados para hoje.")

# Exemplo de uso
if __name__ == "__main__":
    api_key = "49dcecff9c9746a678c6b2887af923b1"  # Substitua com sua chave da API
    api_football = APIFootball(api_key)
    api_football.listar_jogos_do_dia()
