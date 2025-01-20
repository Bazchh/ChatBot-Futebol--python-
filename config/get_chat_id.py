import asyncio
from telegram import Bot

async def get_chat_id(api_key):
    bot = Bot(token=api_key)
    
    # Obtendo as últimas atualizações
    updates = await bot.get_updates()  # Aguarda as atualizações

    if not updates:
        print("Nenhuma atualização encontrada.")
    else:
        print(f"Encontradas {len(updates)} atualizações.")
        
    # Exibindo cada atualização recebida
    for update in updates:
        print(f"Update: {update}")
        
        # Verificando se a atualização contém uma mensagem
        if update.message:
            print(f"Chat ID: {update.message.chat.id} - Texto da mensagem: {update.message.text}")

if __name__ == "__main__":
    api_key = '8195835290:AAHnsVeIY_fS_Nmi9tkKl_e9JskMoZ4y1Zk'  # Substitua pelo seu token
    asyncio.run(get_chat_id(api_key))
