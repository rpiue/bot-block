import threading
from flask_app import app  # Importa Flask
from bot_tlg import main as bot_main  # Importa el bot

def run_bot():
    """Ejecuta el bot de Telegram en un hilo separado"""
    bot_main()

if __name__ == "__main__":
    # Iniciar el bot en un hilo separado
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Ejecutar Flask en el hilo principal
    app.run(host="0.0.0.0", port=3000, debug=True)
