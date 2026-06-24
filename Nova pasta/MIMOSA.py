@'
import logging
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_PRIVE")
ADMIN_CHAT_IDS = [int(x.strip()) for x in os.getenv("ADMIN_CHAT_IDS", "0").split(",") if x.strip()]

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────
# CATEGORIAS (20 categorias)
# ────────────────────────────────────────────────────────────────

CATEGORIAS = [
    ("🎓 Universitárias", "cat_universitarias"),
    ("📱 Omegle +18", "cat_omegle"),
    ("🔥 Cornos", "cat_cornos"),
    ("👩‍❤️‍👩 Lésbicas", "cat_lesbicas"),
    ("🎭 Amadores", "cat_amadores"),
    ("🖤 Fetiches", "cat_fetiches"),
    ("💃 Milfs", "cat_milfs"),
    ("💋 Boquetes", "cat_boquetes"),
    ("🌸 Novinhas +18", "cat_novinhas"),
    ("🔞 OnlyFans", "cat_onlyfans"),
    ("📸 Instagram +18", "cat_instagram"),
    ("🎥 Câmeras Ocultas", "cat_ocultas"),
    ("👑 Coroas", "cat_coroas"),
    ("💍 Casadas", "cat_casadas"),
    ("🎬 Lives +18", "cat_lives"),
    ("👨‍👩‍👧‍👦 Família Sacana", "cat_familia"),
    ("📤 Vazadas", "cat_vazadas"),
    ("🌏 Asiáticas", "cat_asiaticas"),
    ("🎉 Surubas", "cat_surubas"),
    ("🔞 Anal", "cat_anal"),
]

# ────────────────────────────────────────────────────────────────
# MENU PRINCIPAL
# ────────────────────────────────────────────────────────────────

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📋 Assinar", callback_data="assinar")],
        [InlineKeyboardButton("🎯 Promoções", callback_data="promocoes")],
        [InlineKeyboardButton("📂 Categorias", callback_data="categorias")],
        [InlineKeyboardButton("👩‍💼 Modelos", callback_data="modelos")],
        [InlineKeyboardButton("👤 Minha Conta", callback_data="minha_conta")],
        [InlineKeyboardButton("💳 Meus Pagamentos", callback_data="pagamentos")],
        [InlineKeyboardButton("📦 Meus Produtos", callback_data="produtos")],
        [InlineKeyboardButton("🎫 Cupons", callback_data="cupons")],
        [InlineKeyboardButton("👥 Indique Amigos", callback_data="indicar")],
        [InlineKeyboardButton("📞 Suporte", callback_data="suporte")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("⚙️ Configurações", callback_data="config")],
        [InlineKeyboardButton("🆕 Conteúdo Recente", callback_data="recente")],
        [InlineKeyboardButton("🔧 PAINEL ADMIN", callback_data="admin")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ────────────────────────────────────────────────────────────────
# MENU DE CATEGORIAS
# ────────────────────────────────────────────────────────────────

def get_categorias_menu():
    keyboard = []
    for nome, callback in CATEGORIAS:
        keyboard.append([InlineKeyboardButton(nome, callback_data=callback)])
    keyboard.append([InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

# ────────────────────────────────────────────────────────────────
# MENU ADMIN - GRADE 2x2
# ────────────────────────────────────────────────────────────────

def get_admin_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard", callback_data="admin_dashboard")],
        [
            InlineKeyboardButton("👥 Usuários", callback_data="admin_usuarios"),
            InlineKeyboardButton("📦 Assinaturas", callback_data="admin_assinaturas")
        ],
        [
            InlineKeyboardButton("📋 Pedidos", callback_data="admin_pedidos"),
            InlineKeyboardButton("⏳ Pendentes", callback_data="admin_pendentes")
        ],
        [
            InlineKeyboardButton("🎫 Cupons", callback_data="admin_cupons"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("📈 Analytics", callback_data="admin_analytics"),
            InlineKeyboardButton("📝 Logs", callback_data="admin_logs")
        ],
        [
            InlineKeyboardButton("🎁 Promoções", callback_data="admin_promocoes"),
            InlineKeyboardButton("👱 Modelos", callback_data="admin_modelos")
        ],
        [
            InlineKeyboardButton("💾 Backup", callback_data="admin_backup"),
            InlineKeyboardButton("⚙️ Config", callback_data="admin_config")
        ],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ────────────────────────────────────────────────────────────────
# COMANDOS PRINCIPAIS
# ────────────────────────────────────────────────────────────────

async def start(update, context):
    text = (
        "🔥 *MIMOSA HOT — CONTEÚDO EXCLUSIVO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Olá, *{update.effective_user.first_name}*! 👋\n\n"
        "Bem-vindo ao paraíso proibido!\n\n"
        "🎓 Universitárias | 📱 Omegle +18 | 🔥 Cornos\n"
        "👩‍❤️‍👩 Lésbicas | 🎭 Amadores | 🖤 Fetiches\n"
        "💃 Milfs | 💋 Boquetes | 🌸 Novinhas +18\n"
        "🔞 OnlyFans\n\n"
        "✨ *...e muito mais!*\n\n"
        "💳 *PIX* | 🔒 *100% Seguro* | 📦 *Entrega Imediata*\n\n"
        "⬇️ *Escolha uma opção abaixo:*"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_menu())

async def menu(update, context):
    query = update.callback_query
    await query.answer()
    text = (
        "🔥 *MIMOSA HOT — CONTEÚDO EXCLUSIVO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Olá, *{update.effective_user.first_name}*! 👋\n\n"
        "💳 *PIX* | 🔒 *100% Seguro* | 📦 *Entrega Imediata*\n\n"
        "⬇️ *Escolha uma opção abaixo:*"
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_menu())

# ────────────────────────────────────────────────────────────────
# CATEGORIAS
# ────────────────────────────────────────────────────────────────

async def categorias(update, context):
    query = update.callback_query
    await query.answer()
    text = (
        "📂 *CATEGORIAS DE CONTEÚDO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔥 Explore nosso acervo exclusivo:\n\n"
        "*Clique em uma categoria para ver os planos*"
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_categorias_menu())

async def categoria_detalhe(update, context):
    query = update.callback_query
    await query.answer()
    categoria = query.data.replace("cat_", "").replace("_", " ").title()
    
    text = (
        f"📂 *{categoria.upper()}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔞 *Conteúdo exclusivo*\n"
        "💳 *Pague com PIX*\n"
        "📦 *Entrega Imediata*\n\n"
        f"📋 *Planos disponíveis:*\n"
        "🔥 FAN - R$ 29,90\n"
        "👑 VIP - R$ 79,90\n"
        "💎 PRIVE - R$ 299,90\n\n"
        "⬇️ *Clique abaixo para assinar:*"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 Assinar Agora", callback_data="assinar")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="categorias")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")],
    ]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# PAINEL ADMIN
# ────────────────────────────────────────────────────────────────

async def admin_panel(update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id not in ADMIN_CHAT_IDS:
        await query.edit_message_text(
            "❌ *Acesso Negado*\n\n"
            "Você não tem permissão para acessar o painel administrativo.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Voltar", callback_data="menu")]])
        )
        return
    
    text = (
        "🔧 *PAINEL ADMINISTRATIVO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Bem-vindo, Admin! 👋\n\n"
        "📊 *Sistema:* Online\n"
        "📅 *Data:* Hoje\n\n"
        "⬇️ *Selecione uma opção:*"
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_menu())

async def admin_dashboard(update, context):
    query = update.callback_query
    await query.answer()
    
    text = (
        "📊 *DASHBOARD*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👥 *Usuários:* 0\n"
        "📋 *Assinaturas:* 0\n"
        "📦 *Pedidos:* 0\n"
        "⏳ *Pendentes:* 0\n"
        "💰 *Faturamento:* R$ 0,00\n\n"
        "📈 *Crescimento:* 0%\n"
        "🕐 *Última atualização:* Agora"
    )
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_usuarios(update, context):
    query = update.callback_query
    await query.answer()
    text = "👥 *USUÁRIOS*\n━━━━━━━━━━━━━━━━━━━━━━\n\nNenhum usuário cadastrado ainda."
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_assinaturas(update, context):
    query = update.callback_query
    await query.answer()
    text = "📋 *ASSINATURAS*\n━━━━━━━━━━━━━━━━━━━━━━\n\nNenhuma assinatura ativa."
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_pedidos(update, context):
    query = update.callback_query
    await query.answer()
    text = "📦 *PEDIDOS*\n━━━━━━━━━━━━━━━━━━━━━━\n\nNenhum pedido encontrado."
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_pendentes(update, context):
    query = update.callback_query
    await query.answer()
    text = "⏳ *PENDENTES*\n━━━━━━━━━━━━━━━━━━━━━━\n\nNenhum pedido pendente."
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_cupons(update, context):
    query = update.callback_query
    await query.answer()
    text = "🎫 *CUPONS*\n━━━━━━━━━━━━━━━━━━━━━━\n\nNenhum cupom cadastrado."
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_broadcast(update, context):
    query = update.callback_query
    await query.answer()
    text = "📢 *BROADCAST*\n━━━━━━━━━━━━━━━━━━━━━━\n\nEnvie uma mensagem para todos os usuários.\n\n📝 Digite a mensagem que deseja enviar:"
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_analytics(update, context):
    query = update.callback_query
    await query.answer()
    text = "📈 *ANALYTICS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n📊 *Estatísticas:*\n\n👥 Usuários: 0\n📋 Assinaturas: 0\n💰 Faturamento: R$ 0,00\n📦 Conversão: 0%"
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_logs(update, context):
    query = update.callback_query
    await query.answer()
    text = "📝 *LOGS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n🟢 Sistema: Online\n📅 Último acesso: Hoje\n🔍 Nenhum erro registrado."
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_promocoes(update, context):
    query = update.callback_query
    await query.answer()
    text = "🎁 *PROMOÇÕES*\n━━━━━━━━━━━━━━━━━━━━━━\n\nNenhuma promoção ativa."
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_modelos(update, context):
    query = update.callback_query
    await query.answer()
    text = "👱 *MODELOS*\n━━━━━━━━━━━━━━━━━━━━━━\n\nNenhuma modelo cadastrada.\n\nUse /add_modelo para cadastrar."
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_backup(update, context):
    query = update.callback_query
    await query.answer()
    text = "💾 *BACKUP*\n━━━━━━━━━━━━━━━━━━━━━━\n\n✅ Último backup: Hoje\n📅 Próximo backup: Amanhã\n\n📂 Tamanho: 0 MB"
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_config(update, context):
    query = update.callback_query
    await query.answer()
    text = "⚙️ *CONFIGURAÇÕES*\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔹 Idioma: Português\n🔹 Moeda: BRL (R$)\n🔹 Pagamento: PIX\n🔹 Notificações: Ativadas"
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# OUTROS COMANDOS
# ────────────────────────────────────────────────────────────────

async def outros(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    mensagens = {
        "assinar": "📋 *ASSINAR*\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔥 *FAN* - R$ 29,90\n👑 *VIP* - R$ 79,90\n💎 *PRIVE* - R$ 299,90\n\n💳 Pagamento via PIX",
        "promocoes": "🎯 *PROMOÇÕES*\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔥 Pacote VIP Completo\n💰 De: R$ 199,90\n🎯 Por: R$ 99,90",
        "modelos": "👩‍💼 *MODELOS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n📢 Em breve novas modelos!",
        "minha_conta": "👤 *MINHA CONTA*\n━━━━━━━━━━━━━━━━━━━━━━\n\n🆔 ID: 123456\n👤 Nome: Usuário",
        "pagamentos": "💳 *MEUS PAGAMENTOS*\n━━━━━━━━━━━━━━━━━━━━━━\n\nNenhum pagamento encontrado.",
        "produtos": "📦 *MEUS PRODUTOS*\n━━━━━━━━━━━━━━━━━━━━━━\n\nVocê ainda não possui produtos.",
        "cupons": "🎫 *CUPONS*\n━━━━━━━━━━━━━━━━━━━━━━\n\nNenhum cupom disponível.",
        "indicar": "👥 *INDIQUE AMIGOS*\n━━━━━━━━━━━━━━━━━━━━━━\n\nCompartilhe seu link e ganhe R$ 5,00!",
        "suporte": "📞 *SUPORTE*\n━━━━━━━━━━━━━━━━━━━━━━\n\n📱 WhatsApp: +5511940462611",
        "faq": "❓ *FAQ*\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔹 Como assinar?\nClique em Assinar.",
        "config": "⚙️ *CONFIGURAÇÕES*\n━━━━━━━━━━━━━━━━━━━━━━\n\n🔹 Idioma: Português",
        "recente": "🆕 *CONTEÚDO RECENTE*\n━━━━━━━━━━━━━━━━━━━━━━\n\n📸 Novos vídeos e fotos!",
    }
    
    text = mensagens.get(data, "🔄 *Opção em desenvolvimento*")
    keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="menu")]]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# HANDLER PRINCIPAL
# ────────────────────────────────────────────────────────────────

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "menu":
        await menu(update, context)
    elif data == "categorias":
        await categorias(update, context)
    elif data.startswith("cat_"):
        await categoria_detalhe(update, context)
    elif data == "admin":
        await admin_panel(update, context)
    elif data == "admin_dashboard":
        await admin_dashboard(update, context)
    elif data == "admin_usuarios":
        await admin_usuarios(update, context)
    elif data == "admin_assinaturas":
        await admin_assinaturas(update, context)
    elif data == "admin_pedidos":
        await admin_pedidos(update, context)
    elif data == "admin_pendentes":
        await admin_pendentes(update, context)
    elif data == "admin_cupons":
        await admin_cupons(update, context)
    elif data == "admin_broadcast":
        await admin_broadcast(update, context)
    elif data == "admin_analytics":
        await admin_analytics(update, context)
    elif data == "admin_logs":
        await admin_logs(update, context)
    elif data == "admin_promocoes":
        await admin_promocoes(update, context)
    elif data == "admin_modelos":
        await admin_modelos(update, context)
    elif data == "admin_backup":
        await admin_backup(update, context)
    elif data == "admin_config":
        await admin_config(update, context)
    else:
        await outros(update, context)

# ────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🚀 MIMOSA HOT BOT rodando!")
    app.run_polling()

if __name__ == "__main__":
    main()
'@ | Out-File -FilePath mimosa.py -Encoding ascii