# Usando uma imagem base do Python
FROM python:3.9-slim

# Definindo o diretório de trabalho
WORKDIR /app

# Copiar o arquivo de dependências para a imagem
COPY requirements.txt /app/

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código para a imagem
COPY . /app/

# Definir a porta que o container vai expor
EXPOSE 8080

# Definir o comando de execução do servidor
CMD ["python", "bot.py"]
