# Usando uma imagem base
FROM python:3.9-slim

# Definindo o diretório de trabalho no container
WORKDIR /app

# Copiando os arquivos da aplicação para dentro do container
COPY . /app

# Instalando as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expondo a porta que o aplicativo vai usar
EXPOSE 8080

# Definindo o comando para rodar a aplicação usando Hypercorn
CMD ["hypercorn", "telegram_bot.bot:app", "--bind", "0.0.0.0:8080"]
