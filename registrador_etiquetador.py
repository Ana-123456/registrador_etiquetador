# ==============================
# IMPORTACIONES Y CONFIGURACIÓN GENERAL
# ==============================
import os
import logging
import asyncio
import traceback
from datetime import datetime, timedelta
import pytz

from telethon import TelegramClient, events
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# ==============================
# CONFIGURACIÓN
# ==============================

# Configuración del logging
logging.basicConfig(level=logging.INFO, filename='errores_bot.log', filemode='a')

# Credenciales de Telegram (CUENTA PERSONAL)
api_id = 29677993
api_hash = '1af91cf9d0f390bc921bf2159288ea4c'
phone_number = '+51932995121'

# ID del grupo para reportes y errores
GRUPO_PRIVADO_ID = 4731826714

# Ruta relativa al archivo de credenciales de Google
RUTA_CREDENCIALES = os.path.join(os.path.dirname(__file__), 'credentials.json')

# Cliente de Telethon
client = TelegramClient('bot_fusionado', api_id, api_hash)

# ==============================
# CONEXIÓN A GOOGLE SHEETS
# ==============================
alcance = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

credenciales = ServiceAccountCredentials.from_json_keyfile_name(RUTA_CREDENCIALES, alcance)
cliente_sheets = gspread.authorize(credenciales)

documento = cliente_sheets.open("BaseDatosTelegram")
hoja_registro = documento.worksheet("Usuarios")

# ==============================
# FUNCIONES DEL BOT REGISTRADOR
# ==============================

def esta_registrado(user_id):
    ids = hoja_registro.col_values(1)
    return str(user_id) in ids

async def reporte_registrador():
    tz = pytz.timezone("America/Lima")
    while True:
        ahora = datetime.now(tz)
        if ahora.hour == 12 or ahora.hour == 19:
            try:
                await client.send_message(GRUPO_PRIVADO_ID, "✅ BOT REGISTRADOR SIGUE FUNCIONANDO CORRECTAMENTE 1️⃣")
                await asyncio.sleep(3600)  # Espera 1 hora para no enviar dos veces seguidas
            except Exception as e:
                await client.send_message(GRUPO_PRIVADO_ID, f"❌ERROR BOT REGISTRADOR CTA1Q‼️\nFallo al enviar reporte:\n{e}")
        await asyncio.sleep(60)

@client.on(events.NewMessage(incoming=True))
async def registrar_usuario(event):
    try:
        if event.is_private:
            remitente = await event.get_sender()
            user_id = remitente.id
            username = remitente.username or "sin_username"
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not esta_registrado(user_id):
                try:
                    hoja_registro.append_row([str(user_id), username, "pendiente", ahora, ahora])
                    logging.info(f"Nuevo usuario registrado: {username}")
                except Exception as e_registro:
                    error_msg = f"❌ERROR REGISTRANDO USUARIO CTA1‼️\nID: {user_id}\nUsername: @{username}\nError: {e_registro}"
                    await client.send_message(GRUPO_PRIVADO_ID, error_msg)
                    logging.error(error_msg)
    except Exception as e:
        msg = f"❌ERROR GENERAL BOT REGISTRADOR CTA1Q‼️\n{e}"
        await client.send_message(GRUPO_PRIVADO_ID, msg)
        logging.error(msg)

# ==============================
# FUNCIONES DEL BOT ETIQUETADOR
# ==============================

async def reportar_error(error_msg):
    try:
        resumen = error_msg.strip().splitlines()[-1][:1000]
        await client.send_message(GRUPO_PRIVADO_ID, f"❌ BOT ETIQUETADOR CTA1‼️\nResumen del error:\n{resumen}")
    except Exception as e:
        logging.error(f"No se pudo enviar resumen: {e}\n{error_msg}")

async def reporte_etiquetador():
    tz = pytz.timezone("America/Lima")
    ya_reportado = {"12:01": False, "19:01": False}

    while True:
        ahora = datetime.now(tz)
        hora_actual = ahora.strftime("%H:%M")

        if hora_actual == "12:01" and not ya_reportado["12:01"]:
            await client.send_message(GRUPO_PRIVADO_ID, "✅ EL BOT (ETIQUETADOR CTA1) SIGUE FUNCIONANDO CORRECTAMENTE 2️⃣")
            ya_reportado["12:01"] = True

        if hora_actual == "19:01" and not ya_reportado["19:01"]:
            await client.send_message(GRUPO_PRIVADO_ID, "✅ EL BOT (ETIQUETADOR CTA1) SIGUE FUNCIONANDO CORRECTAMENTE 2️⃣")
            ya_reportado["19:01"] = True

        if hora_actual == "00:00":
            ya_reportado = {"12:01": False, "19:01": False}

        await asyncio.sleep(60)

async def actualizar_etiqueta(user_id, nueva_etiqueta):
    try:
        header = hoja_registro.row_values(1)
        col_id = header.index("user_id") + 1
        col_tag = header.index("etiqueta_actual") + 1
        col_fecha = header.index("fecha_etiqueta") + 1

        celda = hoja_registro.find(str(user_id))
        if not celda:
            raise ValueError(f"Usuario con ID {user_id} no encontrado en la hoja de cálculo.")

        fila = celda.row
        etiqueta_actual = hoja_registro.cell(fila, col_tag).value
        if etiqueta_actual != nueva_etiqueta:
            hoja_registro.update_cell(fila, col_tag, nueva_etiqueta)
            hoja_registro.update_cell(fila, col_fecha, datetime.now().strftime('%d/%m/%Y'))
            logging.info(f"Etiqueta actualizada: {user_id} -> {nueva_etiqueta}")
    except Exception:
        await reportar_error(traceback.format_exc())

@client.on(events.NewMessage(outgoing=True))
async def etiquetador(event):
    try:
        mensaje = event.message.text
        if mensaje in ['VIP_PERMANENTE', 'VIP_1MES', 'VIP_VIDEOS']:
            if event.is_private:
                usuario = await event.get_input_chat()
                user_id = usuario.user_id if hasattr(usuario, 'user_id') else usuario.channel_id
                await actualizar_etiqueta(user_id, mensaje)
    except Exception:
        await reportar_error(traceback.format_exc())

# ==============================
# INICIO DEL BOT
# ==============================

async def main():
    await client.start(phone_number)
    logging.info("Bot fusionado iniciado correctamente.")
    print("bot Registrador y bot Etiquetador están activos")

    asyncio.create_task(reporte_registrador())
    asyncio.create_task(reporte_etiquetador())

    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
