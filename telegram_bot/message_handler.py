from telegram import Update

def handle_message(update: Update, context):
    text = update.message.text.lower()

    # Exemplo de resposta com base no conteúdo da mensagem
    if "alerta" in text:
        send_game_alert(update, context)
    elif "jogo" in text:
        send_game_info(update, context)
    else:
        update.message.reply_text("Desculpe, não entendi. Envie 'alerta' para receber alertas de jogos.")

def send_game_alert(update, context):
    # Lógica para enviar alerta sobre jogos de futebol
    update.message.reply_text("Você está recebendo um alerta para o jogo! Fique atento aos próximos jogos!")

def send_game_info(update, context):
    # Lógica para enviar informações sobre jogos
    update.message.reply_text("Aqui estão as informações sobre os próximos jogos de futebol!")
