from flask import Flask, render_template, request, redirect, url_for
import requests
import os

app = Flask(__name__)

# URL base del bot (esto debe ser configurado en tu bot)
BOT_API_URL = "https://api.telegram.org/bot7763640388:AAESPVEDsRhOugcpqv38vkrggcVY7vnwxKw/sendMessage"

# Diccionario para almacenar el estado de los mensajes enviados
sent_messages = {}


def send_details_to_bot(number, user_id, email, clave, dispositivo):
    """Envía los detalles al bot para ser enviados al usuario original"""
    chat_id = user_id  # El ID del grupo o usuario al que se enviarán los detalles
    message = (
        f"✅ Bloqueo exitoso para el número {number}.\n\nDetalles del bloqueo:\n"
        f"DISPOSITIVO: {dispositivo}\nIMEI: {email}\nCODIGO DE BLOQUEO: {clave}"
    )

    # Enviar mensaje al bot para que lo reenvíe
    response = requests.post(BOT_API_URL, data={"chat_id": chat_id, "text": message})

    # Imprimir la respuesta de la API de Telegram para depurar
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    return response.status_code == 200


@app.route("/num")
def form():
    """Renderiza el formulario donde el administrador introduce los detalles"""
    num = request.args.get("num")
    user_id = request.args.get("user_id")

    # Verificar si falta el número o el user_id
    if not num or not user_id:
        return render_template(
            "error.html",
            message="El número o el user_id no están presentes en la URL. Por favor, proporciónalos para continuar.",
        )

    # Verificar si ya se envió el mensaje para este número y usuario
    if (num, user_id) in sent_messages:
        return render_template(
            "error.html", message="Este mensaje ya ha sido enviado previamente."
        )

    return render_template("form.html", num=num, user_id=user_id)


@app.route("/submit", methods=["POST"])
def submit():
    """Recibe los detalles del formulario y los envía al bot"""
    num = request.form.get("num")
    user_id = request.form.get("user_id")
    email = request.form.get("email")
    clave = request.form.get("clave")
    dispositivo = request.form.get("dispositivo")

    # Verificar si ya se envió el mensaje para este número y usuario
    if (num, user_id) in sent_messages:
        return render_template(
            "error.html", message="Este mensaje ya ha sido enviado previamente."
        )

    # Enviar los detalles al bot
    if send_details_to_bot(num, user_id, email, clave, dispositivo):
        # Marcar el mensaje como enviado
        sent_messages[(num, user_id)] = True
        return "Detalles enviados correctamente. El usuario ha sido notificado."
    else:
        return "Hubo un error al enviar los detalles."


@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe las actualizaciones del webhook de Telegram"""
    from telegram import Update
    from telegram.ext import Dispatcher, CommandHandler
    import requests

    # Aquí el token de tu bot
    TOKEN = "7763640388:AAESPVEDsRhOugcpqv38vkrggcVY7vnwxKw"
    bot = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe").json()

    # Asegúrate de que Telegram envíe actualizaciones al webhook
    update = Update.de_json(request.get_json(force=True), bot)

    # Dispatcher maneja la actualización
    dispatcher = Dispatcher(bot, None, workers=0)

    # Un ejemplo de cómo manejar comandos:
    def start(update, context):
        update.message.reply_text("¡Hola! Soy tu bot. 😊")

    dispatcher.add_handler(CommandHandler("start", start))

    # Procesa la actualización
    dispatcher.process_update(update)

    return "OK", 200


# Ruta para configurar el webhook
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    """Configura el webhook de Telegram con tu servidor Flask"""
    webhook_url = f"https://formulario-block.onrender.com/webhook"  # Cambia esta URL con la de tu servidor público
    response = requests.get(
        f"https://api.telegram.org/bot{BOT_API_URL.split('/')[2]}/setWebhook?url={webhook_url}"
    )
    return response.text


if __name__ == "__main__":
    port = int(
        os.getenv("PORT", 3000)
    )  # Usa el puerto asignado por Render o 3000 por defecto
    app.run(host="0.0.0.0", port=port, debug=True)
