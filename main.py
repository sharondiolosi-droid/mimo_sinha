import logging
import asyncio
import os
import sys
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Correção de Event Loop para Windows e Python 3.10+ / 3.14
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

load_dotenv()

# ────────────────────────────────────────────────────────────────
# CREDENCIAIS E CONFIGURAÇÕES OFICIAIS DO CLIENTE
# ────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN", "8840039207:AAEuUFTayyACnskLZGmqxjgXdNjDE2snSPA")

raw_admin_ids = os.getenv("ADMIN_IDS", "8881712229")
ADMIN_CHAT_IDS = [int(x.strip()) for x in raw_admin_ids.split(",") if x.strip() and x.strip().isdigit()]

PIX_KEY = os.getenv("PIX_KEY", "(11)9.4046-2611")
SUPPORT_EMAIL = os.getenv("SUPPORT_USERNAME", "sharondiolosi@gmail.com")

logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_FILE = "users_db.json"

# ────────────────────────────────────────────────────────────────
# MOTOR DE BANCO DE DADOS EM JSON (PERSISTÊNCIA COMPLETA)
# ────────────────────────────────────────────────────────────────
class Database:
    def __init__(self, filename=DB_FILE):
        self.filename = filename
        self.data = {
            "users": {},
            "coupons": {
                "MIMOSA10": {"discount": 10, "uses": 100},
                "VIP2026": {"discount": 20, "uses": 50},
                "GRATIS": {"discount": 100, "uses": 5}
            },
            "models": [
                {"id": 1, "name": "🌹 Sheron", "handle": "@sheronHot", "slug": "sheron", "price": 29.90, "likes": 482},
                {"id": 2, "name": "🌸 Annynha", "handle": "@AnnynhaHot", "slug": "annynha", "price": 34.90, "likes": 612},
                {"id": 3, "name": "🌺 Lari", "handle": "@lariHot", "slug": "lari", "price": 29.90, "likes": 530},
                {"id": 4, "name": "💋 Biatriz", "handle": "@biatrizHot", "slug": "biatriz", "price": 39.90, "likes": 741},
                {"id": 5, "name": "🔥 Maju", "handle": "@majuHot", "slug": "maju", "price": 44.90, "likes": 890}
            ],
            "orders": {},
            "stats": {
                "total_revenue": 0.0,
                "orders_count": 0,
                "upsells_count": 0
            }
        }
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                logger.error(f"Erro ao carregar banco de dados: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar banco de dados: {e}")

    def get_user(self, user_id: int, first_name="Usuário", username=""):
        uid = str(user_id)
        if uid not in self.data["users"]:
            self.data["users"][uid] = {
                "user_id": user_id,
                "first_name": first_name or "Usuário",
                "username": username,
                "joined_date": datetime.now().strftime("%d/%m/%Y"),
                "is_vip": False,
                "plan": "Gratuito",
                "total_spent": 0.0,
                "balance": 0.0,
                "referrals": 0,
                "referred_by": None,
                "products": [],
                "payments": [],
                "cart": [],
                "notif": True,
                "priv": True,
                "lang": "pt_BR"
            }
            self.save()
        else:
            if first_name:
                self.data["users"][uid]["first_name"] = first_name
            if username:
                self.data["users"][uid]["username"] = username
        return self.data["users"][uid]

    def add_to_cart(self, user_id: int, item_name: str, price: float):
        user = self.get_user(user_id)
        user["cart"].append({"name": item_name, "price": price})
        self.save()

    def clear_cart(self, user_id: int):
        user = self.get_user(user_id)
        user["cart"] = []
        self.save()

    def upgrade_user(self, user_id: int, plan_name: str, amount: float):
        uid = str(user_id)
        user = self.get_user(user_id)
        user["is_vip"] = True
        user["plan"] = plan_name
        user["total_spent"] += amount
        
        prod_title = f"Acesso Oficial — {plan_name}"
        if prod_title not in user["products"]:
            user["products"].append(prod_title)
        if "Canal VIP Telegram" not in user["products"]:
            user["products"].append("Canal VIP Telegram")
        
        tx_id = f"PIX_{int(datetime.now().timestamp())}"
        user["payments"].append({
            "id": tx_id,
            "plan": plan_name,
            "amount": amount,
            "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "status": "Aprovado"
        })
        
        self.data["orders"][tx_id] = {
            "user_id": user_id,
            "plan": plan_name,
            "amount": amount,
            "date": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        
        self.data["stats"]["total_revenue"] += amount
        self.data["stats"]["orders_count"] += 1
        self.save()
        return tx_id

db = Database()

# ────────────────────────────────────────────────────────────────
# MATRIZ DE CATEGORIAS (20 ITENS DO ACERVO COMPLETO)
# ────────────────────────────────────────────────────────────────
CATEGORIAS = [
    ("🔥 Universitárias", "cat_universitarias"),
    ("🔞 Omegle +18", "cat_omegle"),
    ("💋 Cornos", "cat_cornos"),
    ("👩‍❤️‍💋‍👩 Lésbicas", "cat_lesbicas"),
    ("🎬 Amadores", "cat_amadores"),
    ("🪢 Fetiches", "cat_fetiches"),
    ("👱 Milfs", "cat_milfs"),
    ("💋 Boquetes", "cat_boquetes"),
    ("🌸 Novinhas +18", "cat_novinhas"),
    ("🔞 OnlyFans", "cat_onlyfans"),
    ("📸 Instagram +18", "cat_instagram"),
    ("🎥 Vazadas", "cat_vazadas"),
    ("📷 Câmeras Ocultas", "cat_ocultas"),
    ("🌏 Asiáticas", "cat_asiaticas"),
    ("👑 Coroas", "cat_coroas"),
    ("🔥 Surubas", "cat_surubas"),
    ("💍 Casadas", "cat_casadas"),
    ("🔞 Anal", "cat_anal"),
    ("🎥 Lives +18", "cat_lives"),
    ("👥 Família Sacana", "cat_familia"),
]

# ────────────────────────────────────────────────────────────────
# HELPER DE EDIÇÃO OU ENVIO DE MENSAGENS
# ────────────────────────────────────────────────────────────────
async def send_or_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                try:
                    await update.callback_query.message.reply_text(
                        text=text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                except Exception:
                    pass
    elif update.message:
        await update.message.reply_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

# ────────────────────────────────────────────────────────────────
# ESTRUTURA DE TECLADOS INLINE
# ────────────────────────────────────────────────────────────────
def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("⭐ Assinar", callback_data="assinar"),
            InlineKeyboardButton("🎁 Promoções", callback_data="promocoes")
        ],
        [
            InlineKeyboardButton("📋 Categorias", callback_data="categorias"),
            InlineKeyboardButton("👱 Modelos", callback_data="modelos")
        ],
        [
            InlineKeyboardButton("👤 Minha Conta", callback_data="minha_conta"),
            InlineKeyboardButton("💳 Meus Pagamentos", callback_data="pagamentos")
        ],
        [
            InlineKeyboardButton("📦 Meus Produtos", callback_data="produtos"),
            InlineKeyboardButton("🎫 Cupons", callback_data="cupons")
        ],
        [
            InlineKeyboardButton("🤝 Indique Amigos", callback_data="indicar"),
            InlineKeyboardButton("📞 Suporte", callback_data="suporte")
        ],
        [
            InlineKeyboardButton("❓ FAQ", callback_data="faq"),
            InlineKeyboardButton("⚙️ Configurações", callback_data="config")
        ],
        [
            InlineKeyboardButton("🛒 Carrinho", callback_data="carrinho"),
            InlineKeyboardButton("📱 Recarga Celular", callback_data="recarga")
        ],
        [InlineKeyboardButton("🏢 Institucional & Catálogo", callback_data="institucional")],
        [InlineKeyboardButton("🎬 Conteúdo Recente", callback_data="recente")],
        [InlineKeyboardButton("🔓 PAINEL ADMIN", callback_data="admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_assinaturas_menu():
    keyboard = [
        [InlineKeyboardButton("📅 Plano 3 Dias (Trial) — R$ 9,90", callback_data="chk_Plano 3 Dias_9.90")],
        [InlineKeyboardButton("📅 Plano 7 Dias — R$ 19,90", callback_data="chk_Plano 7 Dias_19.90")],
        [InlineKeyboardButton("🔓 FAN — R$ 29,90/mês", callback_data="chk_Plano FAN_29.90")],
        [InlineKeyboardButton("👑 VIP — R$ 79,90/mês", callback_data="chk_Plano VIP_79.90")],
        [InlineKeyboardButton("💎 PRIVÊ — R$ 299,90", callback_data="chk_Plano PRIVÊ_299.90")],
        [InlineKeyboardButton("⭐ DIAMOND — R$ 499,90", callback_data="chk_Plano DIAMOND_499.90")],
        [InlineKeyboardButton("♾️ VITALÍCIO — R$ 1.999,90", callback_data="chk_Plano VITALÍCIO_1999.90")],
        [InlineKeyboardButton("─────────────────────────", callback_data="noop")],
        [InlineKeyboardButton("📷 Fotos Exclusivas", callback_data="sub_fotos")],
        [InlineKeyboardButton("🎥 Vídeos Exclusivos", callback_data="sub_videos")],
        [InlineKeyboardButton("📞 Chamada Premium", callback_data="sub_chamada")],
        [InlineKeyboardButton("🎁 Combos & Pacotes", callback_data="sub_combos")],
        [InlineKeyboardButton("🔥 Oferta Relâmpago 🔥", callback_data="sub_oferta")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_categorias_menu():
    keyboard = []
    for i in range(0, len(CATEGORIAS), 2):
        keyboard.append([
            InlineKeyboardButton(CATEGORIAS[i][0], callback_data=CATEGORIAS[i][1]),
            InlineKeyboardButton(CATEGORIAS[i+1][0], callback_data=CATEGORIAS[i+1][1])
        ])
    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

def get_config_menu():
    keyboard = [
        [InlineKeyboardButton("🌏 Idioma", callback_data="cfg_idioma")],
        [InlineKeyboardButton("🔔 Notificações", callback_data="toggle_notif")],
        [InlineKeyboardButton("🔒 Privacidade", callback_data="toggle_priv")],
        [InlineKeyboardButton("🗑️ Excluir Minha Conta", callback_data="cfg_excluir")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

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
        [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ────────────────────────────────────────────────────────────────
# COMANDOS PÚBLICOS
# ────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "Usuário"
    username = update.effective_user.username or ""

    args = context.args
    if args and args[0].startswith("ref_"):
        try:
            ref_id = int(args[0].replace("ref_", ""))
            if ref_id != user_id:
                user = db.get_user(user_id, first_name, username)
                if not user.get("referred_by"):
                    user["referred_by"] = ref_id
                    ref_user = db.get_user(ref_id)
                    ref_user["referrals"] += 1
                    db.save()
        except Exception:
            pass

    db.get_user(user_id, first_name, username)
    
    text = (
        "🔥 *MIMOSA HOT — CONTEÚDO EXCLUSIVO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Olá, *{first_name}*! 👋\n\n"
        "Bem-vindo ao maior ecossistema de conteúdo premium do Telegram!\n\n"
        "🎓 Universitárias | 📱 Omegle +18 | 🔥 Cornos\n"
        "👩‍❤️‍💋‍👩 Lésbicas | 🎬 Amadores | 🪢 Fetiches\n"
        "👱 Milfs | 💋 Boquetes | 🌸 Novinhas +18\n"
        "🔞 OnlyFans\n\n"
        "✨ *PIX Exclusivo* | 🔒 *100% Seguro* | 📦 *Entrega Imediata*\n\n"
        "⬇️ *Escolha uma opção no menu abaixo:*"
    )
    await send_or_edit(update, context, text, get_main_menu())

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "Usuário"
    db.get_user(user_id, first_name, update.effective_user.username or "")
    
    text = (
        "🔥 *MIMOSA HOT — MENU PRINCIPAL*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Olá, *{first_name}*! 👋\n\n"
        "💳 *PIX Único* | 🔒 *Sigilo Absoluto* | 📦 *Acesso Instantâneo*\n\n"
        "⬇️ *Escolha uma opção no menu abaixo:*"
    )
    await send_or_edit(update, context, text, get_main_menu())

async def modelos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await mostrar_modelos(update, context)

async def planos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await mostrar_assinaturas(update, context)

async def faq_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tela_faq(update, context)

async def suporte_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tela_suporte(update, context)

# ────────────────────────────────────────────────────────────────
# COMANDOS DE ADMIN
# ────────────────────────────────────────────────────────────────
async def add_modelo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_CHAT_IDS:
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Uso: `/add_modelo Nome @usuario Preço`", parse_mode=ParseMode.MARKDOWN)
        return
    nome = f"🔥 {args[0].title()}"
    handle = args[1]
    preco = float(args[2])
    novo_id = max([m["id"] for m in db.data["models"]] + [0]) + 1
    db.data["models"].append({"id": novo_id, "name": nome, "handle": handle, "slug": args[0].lower(), "price": preco, "likes": 120})
    db.save()
    await update.message.reply_text(f"✅ Modelo *{nome}* cadastrada!")

async def drop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_CHAT_IDS:
        return
    args = context.args
    if len(args) < 2:
        return
    await update.message.reply_text(f"🚀 *DROP POSTADO EM {args[0].upper()}:*\n🔗 {args[1]}", parse_mode=ParseMode.MARKDOWN)

async def drop_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_CHAT_IDS:
        return
    text = update.message.text.replace("/drop_all", "").strip()
    if not text:
        return
    users = list(db.data["users"].keys())
    sent = 0
    for uid_str in users:
        try:
            await context.bot.send_message(chat_id=int(uid_str), text=f"🔥 *SUPER DROP GERAL*\n\n{text}", parse_mode=ParseMode.MARKDOWN)
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Drop disparado para {sent} usuários!")

async def relatorio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_CHAT_IDS:
        return
    total = len(db.data["users"])
    vips = len([u for u in db.data["users"].values() if u.get("is_vip")])
    rev = db.data["stats"]["total_revenue"]
    rel = f"📈 *BALANÇO GERAL*\n\n👥 Membros: {total}\n👑 VIPs: {vips}\n💰 Faturamento: R$ {rev:.2f}"
    await update.message.reply_text(rel, parse_mode=ParseMode.MARKDOWN)

# ────────────────────────────────────────────────────────────────
# CHECKOUT PIX, UPSELL, DOWNSELL E ORDER BUMP
# ────────────────────────────────────────────────────────────────
async def mostrar_assinaturas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⭐ *ASSINAR — ESCOLHA SEU PLANO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔓 *FAN — R$ 29,90/mês*\n"
        "• Conteúdo exclusivo semanal\n\n"
        "👑 *VIP — R$ 79,90/mês*\n"
        "• Conteúdo premium 3x semana\n\n"
        "💎 *PRIVÊ — R$ 299,90/mês*\n"
        "• Interação direta + Lives exclusivas\n\n"
        "⭐ *DIAMOND — R$ 499,90/mês*\n"
        "• Experiência VIP total\n\n"
        "♾️ *VITALÍCIO — R$ 1.999,90*\n"
        "• Acesso ilimitado para sempre!"
    )
    await send_or_edit(update, context, text, get_assinaturas_menu())

async def fazer_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    parts = data.split("_")
    nome_plano = parts[1]
    valor = float(parts[2])
    
    bump_active = context.user_data.get("order_bump", False)
    valor_total = valor + (14.90 if bump_active else 0.0)
    txid = f"TX{int(datetime.now().timestamp())}"
    pix_code = f"00020101021126580014br.gov.bcb.pix2536mimosa.hot/pix/{txid}5204000053039865405{valor_total:.2f}5802BR5910MIMOSA HOT6009SAO PAULO62070503VIP6304C1D2"
    
    bump_label = "✅ BUMP ATIVO: Pack Bastidores (+R$ 14,90)" if bump_active else "⬜ ORDER BUMP: Adicionar Pack Bastidores (+R$ 14,90)"
    
    text = (
        f"💳 *CHECKOUT PIX ÚNICO — {nome_plano.upper()}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 *Produto Principal:* {nome_plano} (R$ {valor:.2f})\n"
        f"💡 *Oferta Bump:* {'Pack Bastidores (+R$ 14,90)' if bump_active else 'Nenhuma'}\n"
        f"💰 *VALOR TOTAL A PAGAR:* *R$ {valor_total:.2f}*\n\n"
        f"🔑 *Chave PIX Oficial (Telefone/WhatsApp):*\n`{PIX_KEY}`\n\n"
        "📲 *Instruções de Liberação Automática:*\n"
        "1️⃣ Toque na Chave PIX acima ou no código abaixo para copiar.\n"
        f"2️⃣ Faça o PIX no valor exato de *R$ {valor_total:.2f}*.\n"
        "3️⃣ O sistema liberará em até 10 segundos!\n\n"
        "*Código PIX Copia e Cola:*\n"
        f"`{pix_code}`\n\n"
        "*(Simulação: Clique no botão verde abaixo para aprovar instantaneamente)*"
    )
    keyboard = [
        [InlineKeyboardButton(bump_label, callback_data=f"toggle_bump_{nome_plano}_{valor}")],
        [InlineKeyboardButton(f"🛒 Adicionar ao Carrinho", callback_data=f"addcart_{nome_plano}_{valor_total}")],
        [InlineKeyboardButton("✅ Simular Pagamento Aprovado", callback_data=f"pay_app_{nome_plano}_{valor_total:.2f}")],
        [InlineKeyboardButton("🔄 Já Paguei / Verificar Status", callback_data=f"pay_app_{nome_plano}_{valor_total:.2f}")],
        [InlineKeyboardButton("❌ Cancelar / Desistir", callback_data=f"downsell_{nome_plano}")],
        [InlineKeyboardButton("⬅️ Escolher Outro Plano", callback_data="assinar")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def toggle_bump(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    parts = data.split("_")
    context.user_data["order_bump"] = not context.user_data.get("order_bump", False)
    await fazer_checkout(update, context, f"chk_{parts[2]}_{parts[3]}")

async def downsell_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    plano = data.replace("downsell_", "")
    text = (
        "⚡ *ESPERE! NÃO VÁ EMBORA AINDA!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Vi que você desistiu do *{plano}*.\n\n"
        "Liberamos uma **DOWNSELL EXCLUSIVA** para você não ficar de fora:\n\n"
        "🔥 *PLANO 3 DIAS FULL ACCESS* por apenas *R$ 9,90*\n\n"
        "Aceita testar por 72 horas com risco zero?"
    )
    keyboard = [
        [InlineKeyboardButton("⚡ Sim! Quero Testar por R$ 9,90", callback_data="chk_Plano Trial 3 Dias_9.90")],
        [InlineKeyboardButton("❌ Não, prefiro ficar sem acesso", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def aprovar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    parts = data.split("_")
    nome_plano = parts[2]
    valor = float(parts[3])
    user_id = update.effective_user.id
    
    txid = db.upgrade_user(user_id, nome_plano, valor)
    context.user_data["order_bump"] = False
    
    if "FAN" in nome_plano or "7 Dias" in nome_plano or "3 Dias" in nome_plano:
        db.data["stats"]["upsells_count"] += 1
        db.save()
        upsell_msg = (
            "🎉 *PAGAMENTO CONFIRMADO!*\n\n"
            f"Recibo: #{txid}\n\n"
            "🚀 *VOCÊ DESBLOQUEOU UM UPSELL:* Faça agora o Upgrade para o **PLANO VIP VITALÍCIO** com 60% OFF pagando apenas a diferença de **+R$ 39,90**!"
        )
        key_up = [
            [InlineKeyboardButton("🚀 Fazer Upsell VIP (+R$ 39,90)", callback_data="chk_Upsell VIP Vitalício_39.90")],
            [InlineKeyboardButton("✅ Não, quero apenas meu plano atual", callback_data="entregar_produtos")]
        ]
        await send_or_edit(update, context, upsell_msg, InlineKeyboardMarkup(key_up))
        return

    await entregar_produtos_finais(update, context, txid, nome_plano)

async def entregar_produtos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    last_p = user["payments"][-1] if user["payments"] else {"id": "PIX", "plan": "VIP"}
    await entregar_produtos_finais(update, context, last_p["id"], last_p["plan"])

async def entregar_produtos_finais(update: Update, context: ContextTypes.DEFAULT_TYPE, txid: str, plano: str):
    text = (
        "🎉 *ACESSO OFICIAL LIBERADO!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ *Recibo:* #{txid}\n"
        f"👑 *Plano Ativado:* {plano}\n\n"
        "🔗 *Canal Oficial VIP:* `https://t.me/+MimosaHotVIP_Exclusivo_2026`\n"
        "📂 *Drive Secreto 4K:* `https://drive.google.com/drive/folders/mimosa_hot_acervo`\n\n"
        "🔒 Salvos permanentemente em *📦 Meus Produtos* no menu principal!"
    )
    keyboard = [
        [InlineKeyboardButton("📦 Ver Meus Produtos", callback_data="produtos")],
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# OUTRAS TELAS E SERVIÇOS
# ────────────────────────────────────────────────────────────────
async def tela_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    cart = user.get("cart", [])

    text = "🛒 *CARRINHO DE COMPRAS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if not cart:
        text += "❌ Carrinho vazio. Adicione planos ou packs!"
        keyboard = [[InlineKeyboardButton("⭐ Escolher Assinatura", callback_data="assinar")], [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]]
    else:
        total = sum(item["price"] for item in cart)
        for idx, item in enumerate(cart, 1):
            text += f"{idx}. {item['name']} — R$ {item['price']:.2f}\n"
        text += f"\n💰 *TOTAL: R$ {total:.2f}*"
        keyboard = [
            [InlineKeyboardButton(f"💳 Pagar PIX (R$ {total:.2f})", callback_data=f"chk_Carrinho_{total:.2f}")],
            [InlineKeyboardButton("🗑️ Esvaziar", callback_data="limpar_carrinho")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]
        ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def addcart_acao(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    parts = data.split("_")
    db.add_to_cart(update.effective_user.id, parts[1], float(parts[2]))
    if update.callback_query:
        await update.callback_query.answer("🛒 Adicionado ao carrinho!", show_alert=True)
    await tela_carrinho(update, context)

async def limpar_carrinho_acao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.clear_cart(update.effective_user.id)
    if update.callback_query:
        await update.callback_query.answer("🗑️ Carrinho esvaziado!")
    await tela_carrinho(update, context)

async def tela_recarga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📱 *RECARGA DE CELULAR*\n\nRecarregue Vivo, Claro ou Tim via PIX:\n"
    keyboard = [[InlineKeyboardButton("📱 Recarregar R$ 20,00", callback_data="chk_Recarga Celular_20.00")], [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def tela_institucional(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"🏢 *INSTITUCIONAL & COMPLIANCE*\n\n🔞 Plataforma estrita +18.\n⚖️ Respeitamos DMCA e LGPD.\n📧 Contato: `{SUPPORT_EMAIL}`"
    keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def submenu_fotos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📷 *FOTOS EXCLUSIVAS*\n\nSelecione o pack:"
    keyboard = [
        [InlineKeyboardButton("📸 Pack Amadoras (R$ 19,90)", callback_data="chk_Pack Amadoras_19.90")],
        [InlineKeyboardButton("📸 Pack Universitárias (R$ 29,90)", callback_data="chk_Pack Universitárias_29.90")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="assinar")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def submenu_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🎥 *VÍDEOS EXCLUSIVOS*\n\nSelecione a coleção:"
    keyboard = [
        [InlineKeyboardButton("🎬 Câmeras Ocultas (R$ 34,90)", callback_data="chk_Vídeos Ocultas_34.90")],
        [InlineKeyboardButton("🎬 Omegle +18 (R$ 39,90)", callback_data="chk_Vídeos Omegle_39.90")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="assinar")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def submenu_chamada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📞 *CHAMADA PREMIUM 1:1*\n\nAgende 15min ao vivo por R$ 149,90:"
    keyboard = [[InlineKeyboardButton("📞 Agendar Chamada (R$ 149,90)", callback_data="chk_Chamada VIP 15min_149.90")], [InlineKeyboardButton("⬅️ Voltar", callback_data="assinar")]]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def submenu_combos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🎁 *COMBOS E PACOTES*"
    keyboard = [
        [InlineKeyboardButton("🔥 Combo DUO (R$ 119,90)", callback_data="chk_Combo DUO_119.90")],
        [InlineKeyboardButton("💎 PRIVÊ COMPLETO (R$ 1.199,90)", callback_data="chk_PRIVÊ COMPLETO_1199.90")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="assinar")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def submenu_oferta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🔥 *OFERTA RELÂMPAGO (50% OFF)*\n\nVIP Vitalício por apenas *R$ 79,90*!"
    keyboard = [[InlineKeyboardButton("🚀 Aproveitar Oferta VIP", callback_data="chk_VIP Oferta Relâmpago_79.90")], [InlineKeyboardButton("⬅️ Voltar", callback_data="assinar")]]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def mostrar_modelos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👱 *MODELOS CADASTRADAS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for m in db.data["models"]:
        text += f"*{m['name']}* — {m['handle']} — R$ {m['price']:.2f}\n"
    await send_or_edit(update, context, text, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="menu")]]))

async def detalhe_modelo(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    mid = int(data.replace("mod_", ""))
    m = next((mod for mod in db.data["models"] if mod["id"] == mid), None)
    if not m: return
    text = f"👱 *PERFIL: {m['name']}*\n\nHandle: {m['handle']}\nPreço: R$ {m['price']:.2f}"
    keyboard = [
        [InlineKeyboardButton(f"❤️ Curtir ({m['likes']})", callback_data=f"like_mod_{m['id']}")],
        [InlineKeyboardButton(f"🛒 Add Carrinho", callback_data=f"addcart_VIP {m['slug']}_{m['price']}")],
        [InlineKeyboardButton(f"🔓 Assinar PIX", callback_data=f"chk_VIP {m['slug']}_{m['price']}")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="modelos")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def curtir_modelo(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    mid = int(data.replace("like_mod_", ""))
    for m in db.data["models"]:
        if m["id"] == mid: m["likes"] += 1; db.save(); break
    if update.callback_query: await update.callback_query.answer("❤️ Curtido!", show_alert=True)
    await detalhe_modelo(update, context, f"mod_{mid}")

async def categorias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📋 *CATEGORIAS DE CONTEÚDO*\n\nExplore nosso acervo:"
    await send_or_edit(update, context, text, get_categorias_menu())

async def categoria_detalhe(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    nome = dict(CATEGORIAS).get(data, "Acervo")
    text = f"📂 *{nome}*\n\nAssine o VIP para desbloquear!"
    keyboard = [[InlineKeyboardButton("⭐ Assinar VIP", callback_data="assinar")], [InlineKeyboardButton("⬅️ Voltar", callback_data="categorias")]]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def minha_conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    st = "👑 VIP ATIVO" if u["is_vip"] else "🆓 Gratuito"
    text = f"👤 *MINHA CONTA*\n\nID: `{u['user_id']}`\nNome: {u['first_name']}\nStatus: {st}\nInvestido: R$ {u['total_spent']:.2f}"
    keyboard = [[InlineKeyboardButton("⭐ Fazer Upgrade", callback_data="assinar")], [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def meus_pagamentos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    pays = u.get("payments", [])
    text = "💳 *MEUS PAGAMENTOS*\n\n" + ("\n".join([f"• #{p['id']} - R$ {p['amount']:.2f} ({p['plan']})" for p in pays]) if pays else "❌ Nenhum pagamento registrado.")
    await send_or_edit(update, context, text, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="minha_conta")]]))

async def meus_produtos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    prods = u.get("products", [])
    text = "📦 *MEUS PRODUTOS*\n\n" + ("\n".join([f"✅ {pr}" for prod in prods]) if prods else "❌ Nenhum produto ativo.")
    await send_or_edit(update, context, text, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]]))

async def tela_cupons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🎫 *CUPONS*\n\nEnvie `/cupom CODIGO`\nAtivos: `MIMOSA10`, `VIP2026`, `GRATIS`"
    await send_or_edit(update, context, text, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]]))

async def acao_digitar_cupom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_coupon"] = True
    await send_or_edit(update, context, "🎟️ Digite o código do cupom na mensagem abaixo:", InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="cupons")]]))

async def indique_amigos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = db.get_user(uid)
    link = f"https://t.me/MimosaHotBot?start=ref_{uid}"
    text = f"🤝 *INDIQUE AMIGOS*\n\n🔗 Link: `{link}`\n💰 Saldo: R$ {u['balance']:.2f}"
    await send_or_edit(update, context, text, InlineKeyboardMarkup([[InlineKeyboardButton("💸 Saque PIX", callback_data="saque_pix")], [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]]))

async def solicitar_saque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    if u["balance"] < 30.0:
        msg = "❌ Mínimo para saque: R$ 30,00"
    else:
        u["balance"] = 0.0; db.save()
        msg = f"✅ Saque solicitado para a chave PIX `{PIX_KEY}`!"
    await send_or_edit(update, context, msg, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="indicar")]]))

async def tela_suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"📞 *SUPORTE*\n\n📧 E-mail: `{SUPPORT_EMAIL}`\n💬 WhatsApp: `{PIX_KEY}`"
    await send_or_edit(update, context, text, InlineKeyboardMarkup([[InlineKeyboardButton("❓ FAQ", callback_data="faq")], [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]]))

async def tela_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "❓ *FAQ*\n\n1. Liberação automática via PIX Copia e Cola.\n2. Sigilo 100% garantido no extrato bancário."
    await send_or_edit(update, context, text, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]]))

async def detalhe_faq(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    await tela_faq(update, context)

async def tela_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_or_edit(update, context, "⚙️ *CONFIGURAÇÕES*", get_config_menu())

async def cfg_acao_generica(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    if update.callback_query: await update.callback_query.answer("Ajuste salvo!", show_alert=True)
    await tela_config(update, context)

async def alternar_config(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    u = db.get_user(update.effective_user.id)
    k = data.replace("toggle_", "")
    u[k] = not u.get(k, True); db.save()
    if update.callback_query: await update.callback_query.answer(f"{k} alterado!")
    await tela_config(update, context)

async def conteudo_recente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🎬 *CONTEÚDO RECENTE*\n\n🔥 Novas mídias adicionadas hoje em 4K!"
    await send_or_edit(update, context, text, InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Liberar VIP", callback_data="assinar")], [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]]))

async def tela_amostra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_or_edit(update, context, "🔞 Amostras disponíveis na área VIP.", InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="categorias")]]))

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_CHAT_IDS: return
    await send_or_edit(update, context, "🔓 *PAINEL ADMIN*", get_admin_menu())

async def admin_submenus(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    if update.effective_user.id not in ADMIN_CHAT_IDS: return
    if data == "admin_dashboard":
        msg = f"📊 Vendas: {db.data['stats']['orders_count']} | Receita: R$ {db.data['stats']['total_revenue']:.2f}"
    else: msg = "Opção admin"
    await send_or_edit(update, context, msg, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Painel", callback_data="admin")], [InlineKeyboardButton("🏠 Menu", callback_data="menu")]]))

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_coupon"):
        context.user_data["awaiting_coupon"] = False
        await processar_cupom(update, context, update.message.text.strip())
        return
    await update.message.reply_text("🤖 Digite `/menu` para abrir as opções:", reply_markup=get_main_menu())

async def processar_cupom(update: Update, context: ContextTypes.DEFAULT_TYPE, codigo: str):
    c = db.data["coupons"].get(codigo.strip().upper())
    if c and c["uses"] > 0:
        c["uses"] -= 1; db.save()
        msg = f"✅ Cupom aplicado ({c['discount']}% OFF)!"
    else: msg = "❌ Cupom inválido."
    await send_or_edit(update, context, msg, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="cupons")]]))

# ────────────────────────────────────────────────────────────────
# ROTEADOR MAESTRO DE BOTÕES
# ────────────────────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == "noop": await query.answer(); return
    db.get_user(update.effective_user.id, update.effective_user.first_name)
    if data.startswith("like_mod_"): await curtir_modelo(update, context, data); return
    elif data.startswith("cfg_"): await cfg_acao_generica(update, context, data); return
    await query.answer()

    handlers = {
        "menu": menu_cmd, "categorias": categorias, "assinar": mostrar_assinaturas,
        "entregar_produtos": entregar_produtos, "sub_fotos": submenu_fotos,
        "sub_videos": submenu_videos, "sub_chamada": submenu_chamada,
        "sub_combos": submenu_combos, "sub_oferta": submenu_oferta,
        "promocoes": submenu_oferta, "modelos": mostrar_modelos,
        "minha_conta": minha_conta, "pagamentos": meus_pagamentos,
        "produtos": meus_produtos, "cupons": tela_cupons,
        "acao_digitar_cupom": acao_digitar_cupom, "indicar": indique_amigos,
        "saque_pix": solicitar_saque, "suporte": tela_suporte,
        "faq": tela_faq, "config": tela_config, "carrinho": tela_carrinho,
        "limpar_carrinho": limpar_carrinho_acao, "recarga": tela_recarga,
        "institucional": tela_institucional, "recente": conteudo_recente,
        "amostra_cat": tela_amostra, "admin": admin_panel
    }

    if data in handlers: await handlers[data](update, context)
    elif data.startswith("cat_"): await categoria_detalhe(update, context, data)
    elif data.startswith("chk_"): await fazer_checkout(update, context, data)
    elif data.startswith("toggle_bump_"): await toggle_bump(update, context, data)
    elif data.startswith("downsell_"): await downsell_flow(update, context, data)
    elif data.startswith("pay_app_"): await aprovar_pagamento(update, context, data)
    elif data.startswith("mod_"): await detalhe_modelo(update, context, data)
    elif data.startswith("toggle_"): await alternar_config(update, context, data)
    elif data.startswith("addcart_"): await addcart_acao(update, context, data)
    elif data.startswith("faq_"): await detalhe_faq(update, context, data)
    elif data.startswith("admin_"): await admin_submenus(update, context, data)
    else: await send_or_edit(update, context, "🔄 Processado.", InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]]))

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("modelos", modelos_cmd))
    app.add_handler(CommandHandler("planos", planos_cmd))
    app.add_handler(CommandHandler("faq", faq_cmd))
    app.add_handler(CommandHandler("suporte", suporte_cmd))
    app.add_handler(CommandHandler("add_modelo", add_modelo_cmd))
    app.add_handler(CommandHandler("drop", drop_cmd))
    app.add_handler(CommandHandler("drop_all", drop_all_cmd))
    app.add_handler(CommandHandler("relatorio", relatorio_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    print("🚀 MIMOSA HOT BOT ONLINE!")
    app.run_polling()

if __name__ == "__main__":
    main()
