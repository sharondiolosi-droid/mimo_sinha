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

def get_categorias_menu():
    keyboard = []
    for nome, callback in CATEGORIAS:
        keyboard.append([InlineKeyboardButton(nome, callback_data=callback)])
    keyboard.append([InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

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
    else:
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
            "admin": "🔧 *PAINEL ADMIN*\n━━━━━━━━━━━━━━━━━━━━━━\n\n❌ Acesso restrito.",
        }
        
        text = mensagens.get(data, "🔄 *Opção em desenvolvimento*")
        keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="menu")]]
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

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