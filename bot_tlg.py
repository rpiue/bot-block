import json
from urllib.parse import quote

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import datetime
from functions import dataUser
from collections import defaultdict
import sys


print(sys.version)

TOKEN = "7113005692:AAH1fYlejoJDfUwHf1TFWNRzG3MnTdSbZOY"
GROUPS_FILE = "groups.json"  # Archivo donde se guardan los grupos
DATA_GROUP_ID = -4784656073  # ID del grupo "Grupo data"
USER_DETAILS = {}

pending_requests = defaultdict(lambda: None)  # El valor por defecto será None


def load_groups():
    """Carga los grupos guardados en el archivo JSON"""
    try:
        with open(GROUPS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_groups(groups):
    """Guarda los grupos en el archivo JSON"""
    with open(GROUPS_FILE, "w") as f:
        json.dump(groups, f, indent=4)


GROUPS = load_groups()  # Carga los grupos guardados

img = "https://img.freepik.com/free-vector/cute-robot-working-laptop-cartoon-vector-icon-illustration-science-technology-isolated-flat_138676-11815.jpg?semt=ais_hybrid"  # Aquí va la URL de la imagen


async def start(update: Update, context: CallbackContext):
    """Cuando alguien usa /start en un grupo o en privado, guarda el ID y nombre del grupo y muestra los comandos disponibles"""
    chat = update.message.chat
    user_name = update.message.from_user.first_name  # Obtiene el nombre del usuario
    developer = "👨‍💻 Desarrollado por @CodexPE"
    if chat.type in ["group", "supergroup"]:
        GROUPS[str(chat.id)] = chat.title  # Guarda el ID y nombre del grupo
        save_groups(GROUPS)

        # Envía la imagen y el mensaje de bienvenida con los comandos disponibles
        await update.message.reply_photo(
            photo=img,  # Envío de la imagen
            caption=f"💰 *Precio por cada bloqueo: 15 créditos*.\n\n"
            f"🎉 ¡Hola {user_name}! Bienvenido al bot de bloqueo en *{chat.title}*.\n\n"
            "Aquí tienes los *comandos* disponibles:\n\n"
            "📝 /register - Para registrarte y obtener más información.\n"
            "🔒 /block <número> - Para bloquear un número."
            f"{developer}",
            parse_mode="Markdown",
        )
    else:
        # Para mensajes privados o si no es en grupo
        await update.message.reply_photo(
            photo=img,  # Envío de la imagen
            caption=f"💰 *Precio por cada bloqueo: 15 créditos*.\n\n"
            f"🎉 ¡Hola {user_name}! Bienvenido al bot de bloqueo.\n\n"
            "Comandos disponibles:\n\n"
            "👤 /me - *Ver tu perfil.*\n"
            "📝 /register - *Para registrarte.*\n"
            "📋 /cmds - *Para ver los comandos.*\n"
            "💰 /buy - *Ver precios y adquirir créditos.*\n"
            "🔒 /block <número> - *Para bloquear un número.*\n\n"
            f"{developer}",
            parse_mode="Markdown",
        )


async def block(update: Update, context: CallbackContext):
    """Cuando alguien ejecuta /block [número], el bot manda un mensaje al grupo 'Grupo data'"""
    chat = update.message.chat
    user = update.message.from_user
    
    print(user)

    if user.id not in dataUser.REGISTERED_USERS:
        await update.message.reply_text(
            "⚠️ Debes registrarte antes de poder bloquear un número.\nUsa el comando /register."
        )
        return

    creditos = dataUser.Usuario.get_creditos(user.id)
    if creditos is None or int(creditos) < 15:
        # El usuario no tiene suficientes créditos, mostrar mensaje y botón para comprar créditos
        keyboard = [
            [InlineKeyboardButton("Comprar Créditos", callback_data="buy_credits")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚠️ No tienes suficientes créditos para realizar esta acción.\n"
            "Se requieren 15 créditos para bloquear un número.\n\n"
            "¿Te gustaría comprar créditos?",
            reply_markup=reply_markup,
        )
        return

    # Verificar si el comando es en un grupo o chat privado
    if chat.type not in ["group", "supergroup", "private"]:
        await update.message.reply_text(
            "⚠️ Este comando solo se puede usar en un grupo o en privado."
        )
        return

    # Verificar que el comando tenga un número
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("⚠️ El comando se ejecuta asi:\n/block 000000000.")
        return

    number_to_block = context.args[0]
    if user.id in pending_requests:
        if pending_requests[user.id]['status'] == 'pending' :  # Verificamos si el usuario ya tiene una solicitud pendiente
            await update.message.reply_text(
                    "⚠️ Ya tienes una solicitud pendiente. Espera una respuesta antes de hacer otra consulta."
                )
            return
        elif pending_requests[user.id]['number'] == number_to_block:
            
            await update.message.reply_text(
                    f"⚠️ Ya se ha bloqueado el número {number_to_block}.\nConsulta por otro numero",
            )
            return
        else:
            pass

    
    from datetime import datetime, time
    import pytz
    peru_tz = pytz.timezone('America/Lima')
    current_time = datetime.now(peru_tz).time()
    start_time = time(8, 0, 0)  # 8:00 AM
    end_time = time(12, 0, 0)  # 12:00 PM
    if start_time <= current_time <= end_time:
        await update.message.reply_text(
            "✅ Solicitud Enviada. Por favor, espera una respuesta antes de enviar otra solicitud."
        )
    else:
        await update.message.reply_text(
            "✅ <b>Tu solicitud ha sido enviada.</b>\n\n"
            "⚠️ Pero no hay solicitudes telefónicas en este momento.\n\n"
            "🕒 El horario de atención es de <b>8:00 AM a 12:00 PM.</b>"
            , parse_mode="HTML"
        )
        #return
    # Marcar la solicitud como pendiente para este usuario
    #pending_requests[user.id] = number_to_block
    pending_requests[user.id] = {'number': number_to_block, 'status': 'pending'}

    try:
        # Crear el mensaje para el grupo "Grupo data"
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Bloqueado",
                    callback_data=f"block_{number_to_block}_yes_{chat.id}",
                ),
                InlineKeyboardButton(
                    "❌ Error", callback_data=f"block_{number_to_block}_no_{chat.id}"
                ),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Enviar mensaje al grupo "Grupo data"
        #{user.username} ({user.full_name})
        await context.bot.send_message(
            chat_id=DATA_GROUP_ID,
            text=f"⚠️ <b>¡Alerta! Un Cliente</b>\n\n"
                 f"Ha solicitado bloquear el siguiente número:\n\n"
                 f"👤 Número: <a href='tel:{number_to_block}'>{number_to_block}</a>",
            parse_mode="HTML",  # Usamos HTML en lugar de Markdown
            reply_markup=reply_markup,
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ocurrió un error al intentar enviar el mensaje al grupo de administración. Error: {e}"
        )
        if pending_requests[user.id]['status']:
            print("Error sea none ahora el pendiente")
            pending_requests[user.id]['status'] = None
    finally:
        # Después de intentar enviar el mensaje, restablecemos el estado pendiente
        pass
    print(pending_requests[user.id], user.id)

async def handle_response(update: Update, context: CallbackContext):
    """Maneja las respuestas de los administradores en el grupo 'Grupo data'"""
    query = update.callback_query
    user = query.from_user
    data = query.data.split("_")

    # Verifica que la longitud de la lista 'data' es suficiente
    if len(data) < 4:
        await query.answer(
            "Error en los datos recibidos. Por favor, inténtalo de nuevo."
        )
        return

    number = data[1]
    action = data[2]
    original_group_id = int(data[3])

    # Responder al administrador que dio click
    await query.answer()

    # Bloquear a los demás administradores de interactuar
    await query.edit_message_reply_markup(reply_markup=None)

    # Solicitar detalles al administrador
    if action == "yes":
        USER_DETAILS[user.id] = {
            "number": number,
            "original_group_id": original_group_id,
        }
        hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        id_adm = user.id
        name_adm = user.full_name
        url_adm = f"https://t.me/{user.username}" if user.username else "N/A"
        # Usamos el ID del grupo como un identificador del cliente
        original_user = await context.bot.get_chat(original_group_id)
        id_client = str(original_group_id)
        # Esto puede cambiar si tienes detalles adicionales sobre el cliente
        name_client = (
            original_user.full_name or original_user.first_name
        )  # Nombre real del usuario original
        url_client = (
            f"https://t.me/{original_user.username}"
            if original_user.username
            else "N/A"
        )
        
        try:
            # Intentar guardar en Firestore
            dataUser.Usuario.save_to_firestore(
                id_adm,
                name_adm,
                url_adm,
                id_client,
                name_client,
                url_client,
                hora,
                number,
            )
        except Exception as e:
            # Imprimir el error detallado
            await update.message.reply_text(
                f"❌ Ocurrió un error al intentar guardar los datos en Firestore. Error: {e}"
            )
            print(f"Error al guardar en Firestore: {e}")

        # Crear el enlace con los parámetros del número y el user_id
        link = (
            f"https://formulario-block.onrender.com/num?num={number}&user_id={id_client}"
        )

        # Enviar el enlace al administrador para que complete el formulario
        mention = f"{user.name}"
        await query.message.reply_text(
            f"👤 {mention} ha confirmado el bloqueo. Por favor, accede al siguiente enlace para proporcionar los detalles del bloqueo:\n\n"
            f"{link}\n\n"
            "Al completar el formulario, el bot enviará los detalles al usuario original."
        )
    else:
        # Enviar respuesta negativa al grupo original
        await context.bot.send_message(
            chat_id=original_group_id,
            # text=f"❌ El usuario {
            #    user.username} no pudo bloquear el número {number}."
            text=f"❌ No se pudo bloquear el número {number}.",
            )
    
    id_client = int(original_group_id)
    
    if pending_requests[id_client]['status']:
        pending_requests[id_client]['status'] = None


async def register(update: Update, context: CallbackContext):
    """Cuando alguien usa /register, se registra el usuario"""
    user = update.message.from_user
    user_id = user.id
    name_user = user.full_name
    url_user = f"https://t.me/{user.username}" if user.username else "N/A"
    creditos = 0  # Los créditos iniciales para el usuario
    registro_fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Verificar si el usuario ya está registrado
    if dataUser.Usuario.check_user_exists(user_id):
        # Si ya está registrado, enviar mensaje indicando que ya existe
        keyboard = [
            [InlineKeyboardButton("Soporte", url="https://t.me/block_movil")],
            [InlineKeyboardButton("Me", callback_data="me_info")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🚫 ¡Ya estás registrado, {name_user}! 🚫\n\n"
            "Tu cuenta ya ha sido creada previamente. Si necesitas más ayuda, contacta con el soporte.\n\n"
            "¿Qué te gustaría hacer?",
            reply_markup=reply_markup,
        )
    else:
        # Si no está registrado, guardar los detalles del usuario en Firestore
        dataUser.Usuario.save_user_to_firestore(
            user_id, url_user, name_user, creditos, registro_fecha
        )

        # Definir la URL de la imagen de confirmación
        img_url = "https://img.freepik.com/free-vector/cute-robot-working-laptop-cartoon-vector-icon-illustration-science-technology-isolated-flat_138676-11815.jpg?semt=ais_hybrid"  # URL de la imagen de éxito

        # Crear los botones
        keyboard = [
            [InlineKeyboardButton("Comprar Créditos", callback_data="buy_credits")],
            [InlineKeyboardButton("Bloquear", callback_data="block_user")],
        ]

        # Enviar la imagen y mensaje de éxito
        await update.message.reply_photo(
            photo=img_url,  # URL de la imagen
            caption=f"🎉 ¡Te has registrado con éxito, {name_user}! 🎉\n\n"
            f"✅ Tu cuenta ha sido creada con {creditos} créditos.\n"
            f"🕒 Fecha y hora de registro: {registro_fecha}\n"
            f"📲 Tu URL: {url_user}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# Manejar la acción cuando se hace clic en "Comprar Créditos"


async def me_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la acción del botón 'Me' y muestra los datos del usuario con su foto de perfil"""
    try:
    # Verificar si update tiene callback_query
        if update.callback_query:
            query = update.callback_query
            user = query.from_user  # Obtener el usuario desde callback_query
        elif update.message:
            user = update.message.from_user  # Obtener el usuario desde un mensaje
        else:
            # Si no se recibió un callback_query ni un mensaje, se maneja el error
            await update.message.reply_text(
                "Error: No se pudo obtener la información del usuario."
            )
            return

        user_id = user.id
        name_user = user.full_name
        creditos = dataUser.Usuario.get_creditos(user.id)  # Obtener los créditos

        # Responder al callback del botón (si fue un callback_query)
        if update.callback_query:
            await update.callback_query.answer()

        # Obtener la foto de perfil del usuario
        profile_photos = await context.bot.get_user_profile_photos(user_id)

        if user.id not in dataUser.REGISTERED_USERS:
            await update.message.reply_text(
                "⚠️ Debes registrarte antes de poder ver tu perfil.\nUsa el comando /register."
            )
            return

        # Verificar si el usuario tiene fotos de perfil
        if profile_photos.total_count > 0:
            # Tomamos la primera foto de perfil
            photo_file = profile_photos.photos[0][-1].file_id
        else:
            photo_file = img
            
        
        caption = (
                f"📝 Información de {name_user}:\n\n"
                f"🆔 <b>USER ID:</b> <code>{user_id}</code>\n"
                f"👤 <b>Nombre:</b> {name_user}\n"
                f"💰 <b>Créditos:</b> {creditos if creditos is not None else 'No disponible'}"
        )
        
        keyboard = [
            [InlineKeyboardButton("Comprar Créditos", callback_data="buy_credits")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
            # Si se trata de un callback_query, usar edit_message_media, sino reply_text
        if update.callback_query:
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(photo_file, caption=caption, parse_mode="HTML"),
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_photo(photo=photo_file, caption=caption, parse_mode="HTML",reply_markup=reply_markup)

    except:
        print(f"Error al intentar responder el mensaje:")

async def handle_buy_credits(
    update: Update, context: CallbackContext, is_callback_query=True
):
    """Envía la información de créditos y botones de compra"""
    # Crear el texto con los precios y detalles de la compra
    creditos_info = (
        "💳 *Créditos disponibles*:\n\n"
        "  - 18 Créditos → 13 PEN\n"
        "  - 36 Créditos → 26 PEN\n"
        "  - 54 Créditos → 39 PEN\n"
        "  - 72 Créditos → 50 PEN\n"
        "  - 96 Créditos → 65 PEN\n"
        "\n*Para comprar créditos, presiona el botón de abajo.*"
    )
    
    # Verificar si es una callback_query
    if is_callback_query and update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id  # Obtiene el ID del usuario desde callback_query
        mensaje = f"Hola, quiero comprar créditos. Mi ID es: {user_id}"
        mensaje_codificado = quote(mensaje)

        url = f"https://t.me/block_movil?text={mensaje_codificado}"

        # Botones para comprar créditos y volver
        buttons = [
            [InlineKeyboardButton("Comprar", url=url)],
           # [InlineKeyboardButton("Volver", callback_data="back_to_start")],

        ]
        
        await query.answer()  # Responder al callback

        # Editar el mensaje si es una callback_query
        if query.message.text:
            await query.edit_message_text(
                text=creditos_info,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        else:
            # Si es una imagen, enviar un nuevo mensaje
            await query.message.reply_text(
                text=creditos_info,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
    else:
        # Si es un mensaje de texto (por ejemplo, un comando), responder con el mensaje
        user_name = update.message.from_user.first_name  # Nombre del usuario
        user_id = update.message.from_user.id  # Obtiene el ID del usuario
        mensaje = f"Hola, quiero comprar créditos. Mi ID es: {user_id}"
        mensaje_codificado = quote(mensaje)

        url = f"https://t.me/block_movil?text={mensaje_codificado}"

        # Botones para comprar créditos y volver
        buttons = [
            [InlineKeyboardButton("Comprar", url=url)],
        ]

        await update.message.reply_text(
            text=f"Hola {user_name}!\n{creditos_info}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
# Manejador de "Volver"


async def handle_back_to_start(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    # Mensaje de inicio o vuelta
    await query.edit_message_text(
        text="🎉 ¡Bienvenido de nuevo! ¿Qué deseas hacer?",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Comprar Créditos", callback_data="buy_credits")],
                [InlineKeyboardButton("Bloquear", callback_data="block_user")],
            ]
        ),
    )


async def block_user(update: Update, context: CallbackContext):
    # Responde al clic en el botón para evitar que el usuario quede esperando
    query = update.callback_query
    await query.answer()

    # Verifica si el mensaje tiene texto, de ser así lo edita
    if query.message.text:
        await query.edit_message_text(
            text="🎉 Has hecho clic en 'Bloquear'.\nPor favor, escribe el comando\n/block 000000000."
        )
    else:
        # Si no tiene texto, se envía un nuevo mensaje
        await query.message.reply_text(
            text="🎉 Has hecho clic en 'Bloquear'.\nPor favor, escribe el comando\n/block 000000000."
        )

    # Si quieres actualizar los botones también, puedes hacerlo después
    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Bloqueado", callback_data="blocked")]]
        )
    )


async def get_groups(update: Update, context: CallbackContext):
    """Muestra los grupos en los que el bot está presente."""
    chat = update.message.chat
    user_name = update.message.from_user.first_name  # Obtiene el nombre del usuario

    # Verifica si el usuario es administrador o tiene permisos para ver los grupos
    if chat.type == "private":
        groups_list = "\n".join(
            [
                f"- {group_name} (ID: {group_id})"
                for group_id, group_name in GROUPS.items()
            ]
        )

        if groups_list:
            await update.message.reply_text(
                f"🔍 Aquí están los grupos donde el bot está presente:\n\n{groups_list}"
            )
        else:
            await update.message.reply_text(
                "⚠️ El bot no está presente en ningún grupo aún."
            )
    else:
        await update.message.reply_text("⚠️ Este comando solo se puede usar en privado.")


async def cmds_info(update: Update, context: CallbackContext):
    """Muestra todos los comandos disponibles"""
    # Verifica que el mensaje provenga de un usuario
    user_name = update.message.from_user.first_name  # Obtiene el nombre del usuario

    # Enviar la lista de comandos con emojis
    await update.message.reply_text(
        f"👋 ¡Hola {user_name}! Aquí tienes la lista de comandos disponibles:\n\n"
        "👤 /me - *Ver tu perfil personal*.\n"
        "📝 /register - *Regístrate para comenzar*.\n"
        "📋 /cmds - *Consulta todos los comandos disponibles*.\n"
        "💸 /buy - *Ver precios y adquirir créditos*.\n"
        "🔒 /block <número> - *Bloquear un número específico*.\n\n"
        "Si necesitas más ayuda, no dudes en preguntar. 😊",
        parse_mode="Markdown",
    )

# Función para detener el bot
async def stop_bot():
    import os
    import signal


    app = Application.builder().token(TOKEN).build()
    
    """Función para detener el bot desde el código."""
    print("Deteniendo el bot...")
    if app.running:
        print("Deteniendo el bot...")
        await app.stop()  # Detener el bot correctamente
        os.kill(os.getpid(), signal.SIGTERM)  # Esto envía una señal para terminar el proceso actual
    else:
        print("El bot no está en ejecución, no se puede detener.")
    


async def dar_creditos(update: Update, context: CallbackContext) -> None:
    try:
        user = update.message.from_user

        if user.id not in [7304438558, 5387722607]:
            return
        
        
        target_user = context.args[0]  # ID o nombre de usuario del destinatario
        cantidad = int(context.args[1])  # Cantidad de créditos

        if cantidad <= 0:
            await update.message.reply_text("La cantidad de créditos debe ser mayor que cero.")
            return
        creditosINI = 0
        if(cantidad == 1):
            creditosINI = 18
        if(cantidad == 2):
            creditosINI = 36
        if(cantidad == 3):
            creditosINI = 54
        if(cantidad == 4):
            creditosINI = 72
        if(cantidad == 5):
            creditosINI = 96
        
        if str(target_user) not in map(str, dataUser.REGISTERED_USERS):
            await update.message.reply_text(
                f"⚠️ El usuario debe registrarse antes de darle créditos. ID: <code>{target_user}</code>",
                parse_mode="HTML"  # Para que el ID sea copiable
            )
            return
        
        dataUser.Usuario.agg_creditos(target_user, cantidad)
        await update.message.reply_text(f"Has dado {creditosINI} créditos a {target_user}. 🎉")

    except (IndexError, ValueError):
        await update.message.reply_text(
            "⚠️ <b>Uso incorrecto del comando.</b>\n\n"
            "✅ <b>Formato correcto:</b> <code>/dar &lt;user_id&gt; &lt;opción&gt;</code>\n\n"
            "💳 <b>Créditos disponibles:</b>\n"
            "  📌 <b>opc 1</b> - 18 Créditos\n"
            "  📌 <b>opc 2</b> - 36 Créditos\n"
            "  📌 <b>opc 3</b> - 54 Créditos\n"
            "  📌 <b>opc 4</b> - 72 Créditos\n"
            "  📌 <b>opc 5</b> - 96 Créditos",
            parse_mode="HTML"
        )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("block", block))
    app.add_handler(CommandHandler("me", me_info))
    app.add_handler(CommandHandler("exit", stop_bot))
    app.add_handler(CommandHandler("cmds", cmds_info))
    app.add_handler(CommandHandler("dar", dar_creditos))
    app.add_handler(CommandHandler("buy", handle_buy_credits))
    app.add_handler(CommandHandler("getgroups", get_groups))
    # Maneja las respuestas de los botones inline
    # # Agregar el nuevo comando /register
    app.add_handler(CallbackQueryHandler(handle_buy_credits, pattern="buy_credits"))
    app.add_handler(CallbackQueryHandler(handle_back_to_start, pattern="back_to_start"))
    app.add_handler(CallbackQueryHandler(block_user, pattern="block_user"))
    app.add_handler(CallbackQueryHandler(me_info, pattern="me_info"))

    app.add_handler(CallbackQueryHandler(handle_response))

    app.add_handler(CommandHandler("register", register))

    # Recibe los detalles del admin

    print("Bot iniciado...")
    app.run_polling()



if __name__ == "__main__":
    main()
    #import time
    #time.sleep(30)
    #asyncio.run(stop_bot()) 
