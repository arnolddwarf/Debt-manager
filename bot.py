from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import filters
from telegram.ext import MessageHandler
from telegram.ext import CallbackQueryHandler
from datetime import datetime
import csv
import os

ARCHIVO = "deudas.csv"

# Crear el archivo si no existe
if not os.path.exists(ARCHIVO):
    with open(ARCHIVO, "w", newline="") as f: 
        writer = csv.writer(f)
        writer.writerow(["Cliente", "Monto", "Detalle", "Estado"])

CLIENTES_FRECUENTES = ["arnold", "María", "Pedro", "Lucía"]

def obtener_clientes():
    if not os.path.exists(ARCHIVO):
        return []
    with open(ARCHIVO, "r") as f:
        reader = csv.DictReader(f)
        nombres = [row["Cliente"] for row in reader]
        return sorted(set(nombres))



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Soy tu bot de deudas.\nUsa /nueva para registrar una deuda.")

async def nueva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clientes = obtener_clientes()
    keyboard = [
        [InlineKeyboardButton(nombre, callback_data=f"nuevo_cliente_{nombre}")]
        for nombre in clientes
    ]
    keyboard.append([InlineKeyboardButton("🆕 Otro cliente", callback_data="nuevo_cliente_otro")])
    keyboard.append([InlineKeyboardButton("🏠 Menú principal", callback_data="menu_principal")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("👤 ¿Quién te pidió fiado?", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("👤 ¿Quién te pidió fiado?", reply_markup=reply_markup)




async def seleccionar_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "nuevo_cliente_otro":
        context.user_data["estado"] = "esperando_nombre"
        await query.edit_message_text("✍️ Escribe el nombre del cliente:")
    elif query.data.startswith("nuevo_cliente_"):
        cliente = query.data.replace("nuevo_cliente_", "")
        context.user_data["cliente"] = cliente
        context.user_data["estado"] = "esperando_monto"
        await query.edit_message_text(f"💰 ¿Cuánto te debe {cliente}?")


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    estado = context.user_data.get("estado")

    if estado == "esperando_nombre":
        context.user_data["cliente"] = update.message.text.strip()
        context.user_data["estado"] = "esperando_monto"
        await update.message.reply_text(f"💰 ¿Cuánto te debe {update.message.text.strip()}?")

    elif estado == "esperando_monto":
        try:
            monto = float(update.message.text)
            if monto <= 0:
                raise ValueError
            context.user_data["monto"] = f"{monto:.2f}"
            context.user_data["estado"] = "esperando_detalle"
            await update.message.reply_text("📝 ¿Qué detalle quieres registrar?")
        except ValueError:
            await update.message.reply_text("❗ El monto debe ser un número positivo. Intenta de nuevo.")

    elif estado == "esperando_detalle":
        detalle = update.message.text.strip()
        if not detalle:
            await update.message.reply_text("❗ El detalle no puede estar vacío. Intenta de nuevo.")
            return

        context.user_data["detalle"] = detalle
        context.user_data["estado"] = "confirmar_registro"

        await mostrar_resumen_confirmacion(update, context)

    elif estado == "editar_monto":
        try:
            monto = float(update.message.text)
            if monto <= 0:
                raise ValueError
            context.user_data["monto"] = f"{monto:.2f}"
            context.user_data["estado"] = "confirmar_registro"
            await update.message.reply_text("✅ Monto actualizado.")
            await mostrar_resumen_confirmacion(update, context)
        except ValueError:
            await update.message.reply_text("❗ El monto debe ser un número positivo. Intenta de nuevo.")

    elif estado == "editar_detalle":
        detalle = update.message.text.strip()
        if not detalle:
            await update.message.reply_text("❗ El detalle no puede estar vacío. Intenta de nuevo.")
            return
        context.user_data["detalle"] = detalle
        context.user_data["estado"] = "confirmar_registro"
        await update.message.reply_text("✅ Detalle actualizado.")
        await mostrar_resumen_confirmacion(update, context)

    else:
        await update.message.reply_text("🤖 No entendí eso. Usa /menu para comenzar.")



async def manejar_confirmacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirmar_deuda":
        cliente = context.user_data.get("cliente")
        monto = context.user_data.get("monto")
        detalle = context.user_data.get("detalle")
        fecha = datetime.now().strftime("%d/%m %H:%M")


        with open(ARCHIVO, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([cliente, monto, detalle, "pendiente", fecha])

        await query.edit_message_text(f"✅ Deuda registrada para {cliente} por S/.{monto}")
        context.user_data.clear()

    elif query.data == "cancelar_deuda":
        await query.edit_message_text("❌ Registro cancelado.")
        context.user_data.clear()

    elif query.data == "editar_deuda":
        keyboard = [
            [
                InlineKeyboardButton("💰 Editar monto", callback_data="editar_monto"),
                InlineKeyboardButton("📝 Editar detalle", callback_data="editar_detalle")
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="volver_confirmacion")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("✏️ ¿Qué deseas editar?", reply_markup=reply_markup)


async def manejar_edicion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "editar_deuda":
        keyboard = [
            [
                InlineKeyboardButton("💰 Editar monto", callback_data="editar_monto"),
                InlineKeyboardButton("📝 Editar detalle", callback_data="editar_detalle")
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="volver_confirmacion")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("✏️ ¿Qué deseas editar?", reply_markup=reply_markup)

    elif query.data == "editar_monto":
        context.user_data["estado"] = "editar_monto"
        await query.edit_message_text("💰 Ingresa el nuevo monto:")

    elif query.data == "editar_detalle":
        context.user_data["estado"] = "editar_detalle"
        await query.edit_message_text("📝 Ingresa el nuevo detalle:")

    elif query.data == "volver_confirmacion":
        await mostrar_resumen_confirmacion(update, context)



async def mostrar_resumen_confirmacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cliente = context.user_data["cliente"]
    monto = context.user_data["monto"]
    detalle = context.user_data["detalle"]

    mensaje = (
        f"📋 *Resumen de la deuda:*\n"
        f"- Cliente: {cliente}\n"
        f"- Monto: S/.{monto}\n"
        f"- Detalle: {detalle}\n\n"
        f"¿Deseas registrar esta deuda?"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_deuda"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_deuda")
        ],
        [
            InlineKeyboardButton("✏️ Editar", callback_data="editar_deuda")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(mensaje, parse_mode="Markdown", reply_markup=reply_markup)




async def ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(ARCHIVO):
        await update.message.reply_text("📂 No hay deudas registradas.")
        return

    with open(ARCHIVO, "r") as f:
        reader = csv.DictReader(f)
        deudas = [row for row in reader if row["Estado"] == "pendiente"]

    if not deudas:
        await update.message.reply_text("🎉 No tienes deudas pendientes registradas.")
        return

    mensaje = "📋 *Deudas pendientes:*\n"
    for deuda in deudas:
        mensaje += f"- {deuda['Cliente']}: S/.{deuda['Monto']} ({deuda['Detalle']})\n"

    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clientes = obtener_clientes()
    if not clientes:
        await update.message.reply_text("📂 No hay clientes registrados aún.")
        return

    keyboard = [
        [InlineKeyboardButton(cliente, callback_data=f"pagar_cliente_{cliente}")]
        for cliente in clientes
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👥 ¿A qué cliente quieres registrar un pago?", reply_markup=reply_markup)

async def seleccionar_deuda_para_pagar_directo(cliente, query, context):
    context.user_data["cliente_pago"] = cliente

    with open(ARCHIVO, "r") as f:
        reader = csv.DictReader(f)
        deudas = [row for row in reader if row["Cliente"] == cliente and row["Estado"] == "pendiente"]

    if not deudas:
        await query.edit_message_text(f"🎉 {cliente} no tiene deudas pendientes.")
        return

    context.user_data["deudas_cliente"] = deudas

    keyboard = [
        [InlineKeyboardButton(f"S/.{d['Monto']} ({d['Detalle']})", callback_data=f"pagar_una_{i}")]
        for i, d in enumerate(deudas)
    ]
    keyboard.append([InlineKeyboardButton("💰 Pagar todo", callback_data="pagar_todo")])
    keyboard.append([InlineKeyboardButton(f"🔙 Atrás", callback_data=f"menu_cliente_{cliente}")])
    keyboard.append([InlineKeyboardButton("🏠 Menú principal", callback_data="menu_principal")])
    reply_markup = InlineKeyboardMarkup(keyboard)


    await query.edit_message_text(f"💳 Deudas pendientes de {cliente}:", reply_markup=reply_markup)




async def confirmar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cliente = context.user_data.get("cliente_pago")
    deudas = context.user_data.get("deudas_cliente", [])

    with open(ARCHIVO, "r") as f:
        todas = list(csv.DictReader(f))

    if query.data.startswith("pagar_una_"):
        index = int(query.data.replace("pagar_una_", ""))
        deuda = deudas[index]

        for row in todas:
            if (row["Cliente"] == deuda["Cliente"] and
                row["Monto"] == deuda["Monto"] and
                row["Detalle"] == deuda["Detalle"] and
                row["Estado"] == "pendiente"):
                row["Estado"] = "pagado"
                break

        mensaje = f"✅ Se marcó como pagada la deuda de {cliente} por S/.{deuda['Monto']}"

    elif query.data == "pagar_todo":
        for row in todas:
            if row["Cliente"] == cliente and row["Estado"] == "pendiente":
                row["Estado"] = "pagado"
        mensaje = f"✅ Todas las deudas de {cliente} han sido marcadas como pagadas."

    # Guardar cambios
    with open(ARCHIVO, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Cliente", "Monto", "Detalle", "Estado"])
        writer.writeheader()
        writer.writerows(todas)

    await query.edit_message_text(mensaje)
    context.user_data.clear()


async def listar_clientes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clientes = obtener_clientes()
    if not clientes:
        await update.message.reply_text("📂 No hay clientes registrados aún.")
        return

    keyboard = [
        [InlineKeyboardButton(cliente, callback_data=f"menu_cliente_{cliente}")]
        for cliente in clientes
    ]
    keyboard.append([InlineKeyboardButton("🏠 Menú principal", callback_data="menu_principal")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("👥 Selecciona un cliente:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("👥 Selecciona un cliente:", reply_markup=reply_markup)

    

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👥 Ver clientes", callback_data="menu_ver_clientes")],
        [InlineKeyboardButton("➕ Nueva deuda", callback_data="menu_nueva_deuda")],
        [InlineKeyboardButton("📊 Resumen general", callback_data="menu_resumen")],
        [InlineKeyboardButton("🚪 Salir", callback_data="menu_salir")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("📌 *Menú principal*", reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text("📌 *Menú principal*", reply_markup=reply_markup, parse_mode="Markdown")

async def manejar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu_ver_clientes":
        await listar_clientes(update, context)

    elif query.data == "menu_nueva_deuda":
        await nueva(update, context)

    elif query.data == "menu_resumen":
        total = 0.0
        if os.path.exists(ARCHIVO):
            with open(ARCHIVO, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["Estado"] == "pendiente":
                        try:
                            total += float(row["Monto"])
                        except ValueError:
                            pass
        await query.edit_message_text(f"📊 *Resumen general:*\n\n💰 Total pendiente: S/.{total:.2f}", parse_mode="Markdown")

    elif query.data == "menu_salir":
        await query.edit_message_text("👋 Menú cerrado.")



async def mostrar_menu_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("menu_cliente_"):
        return

    cliente = query.data.replace("menu_cliente_", "")
    context.user_data["cliente_menu"] = cliente

    keyboard = [
        [InlineKeyboardButton("📥 Nueva deuda", callback_data="menu_opcion_nueva")],
        [InlineKeyboardButton("📋 Ver deudas", callback_data="menu_opcion_ver")],
        [InlineKeyboardButton("✅ Pagar", callback_data="menu_opcion_pagar")],
        [InlineKeyboardButton("🔙 Atrás", callback_data="menu_opcion_atras")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"📌 Opciones para *{cliente}*:", reply_markup=reply_markup, parse_mode="Markdown")
    keyboard.append([InlineKeyboardButton("🏠 Menú principal", callback_data="menu_principal")])


async def manejar_opcion_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cliente = context.user_data.get("cliente_menu")

    if not cliente:
        await query.edit_message_text("⚠️ Error: cliente no definido.")
        return

    if query.data == "menu_opcion_nueva":
        context.user_data["cliente"] = cliente
        context.user_data["estado"] = "esperando_monto"
        await query.edit_message_text(f"💰 ¿Cuánto te debe {cliente}?")

    elif query.data == "menu_opcion_ver":
        await mostrar_deudas_cliente_directo(cliente, query)

    elif query.data == "menu_opcion_pagar":
        await seleccionar_deuda_para_pagar_directo(cliente, query, context)

    elif query.data == "menu_opcion_atras":
        context.user_data.pop("cliente_menu", None)
        await listar_clientes(update, context)



async def mostrar_deudas_cliente_directo(cliente, query):
    with open(ARCHIVO, "r") as f:
        reader = csv.DictReader(f)
        deudas = [row for row in reader if row["Cliente"] == cliente]

    if not deudas:
        await query.edit_message_text(f"📭 No hay deudas registradas para {cliente}.")
        return

    mensaje = f"📋 *Deudas de {cliente}:*\n"
    total_pendiente = 0.0

    for deuda in deudas:
        estado = "✅ Pagado" if deuda["Estado"] == "pagado" else "❌ Pendiente"
        mensaje += f"- S/.{deuda['Monto']} ({deuda['Detalle']}) — {estado} — 🕓 {deuda.get('Fecha', 'Sin fecha')}\n"

        if deuda["Estado"] == "pendiente":
            try:
                total_pendiente += float(deuda["Monto"])
            except ValueError:
                pass

    mensaje += f"\n💰 *Total pendiente:* S/.{total_pendiente:.2f}"
    keyboard = [
        [InlineKeyboardButton(f"🔙 Atrás", callback_data=f"menu_cliente_{cliente}")],
        [InlineKeyboardButton("🏠 Menú principal", callback_data="menu_principal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(mensaje, parse_mode="Markdown", reply_markup=reply_markup)

    







app = ApplicationBuilder().token("7280613379:AAEDYsmbszjOp411nWIVCxv2NaXDQShSvLM").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("nueva", nueva))
app.add_handler(CallbackQueryHandler(mostrar_deudas_cliente_directo, pattern="^ver_cliente_"))
app.add_handler(CallbackQueryHandler(mostrar_menu_cliente, pattern="^menu_cliente_"))
app.add_handler(CallbackQueryHandler(menu_principal, pattern="^menu_principal$"))
app.add_handler(CallbackQueryHandler(manejar_opcion_menu, pattern="^menu_opcion_"))
app.add_handler(CommandHandler("clientes", listar_clientes))

app.add_handler(CallbackQueryHandler(seleccionar_cliente, pattern="^nuevo_cliente_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
app.add_handler(CommandHandler("ver", ver))
app.add_handler(CommandHandler("pagar", pagar))
app.add_handler(CallbackQueryHandler(seleccionar_deuda_para_pagar_directo, pattern="^pagar_cliente_"))
app.add_handler(CallbackQueryHandler(confirmar_pago, pattern="^pagar_una_|^pagar_todo$"))

app.add_handler(CommandHandler("start", menu_principal))
app.add_handler(CommandHandler("menu", menu_principal))
app.add_handler(CallbackQueryHandler(manejar_menu_principal, pattern="^menu_"))

app.add_handler(CallbackQueryHandler(manejar_confirmacion, pattern="^confirmar_deuda|^cancelar_deuda$"))


app.add_handler(CallbackQueryHandler(manejar_edicion, pattern="^editar_|^volver_confirmacion$"))



app.run_polling()
