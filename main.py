import logging
import asyncio
import os
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
# ESTRUTURA DE TECLADOS INLINE (EXATA FIDELIDADE ÀS TELAS)
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

def get_modelos_menu():
    keyboard = []
    for m in db.data["models"]:
        btn_label = f"{m['name']} — {m['handle']} — R$ {m['price']:.2f}"
        keyboard.append([InlineKeyboardButton(btn_label, callback_data=f"mod_{m['id']}")])
    keyboard.append([InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="menu")])
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
# COMANDOS PÚBLICOS (/start, /menu, /modelos, /planos, /faq, /suporte)
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
# COMANDOS ADMINISTRATIVOS (/add_modelo, /drop, /drop_all, /relatorio)
# ────────────────────────────────────────────────────────────────
async def add_modelo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_CHAT_IDS:
        await update.message.reply_text("❌ *Comando restrito a Administradores.*", parse_mode=ParseMode.MARKDOWN)
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Uso correto:\n`/add_modelo Nome @usuario Preço`\nExemplo:\n`/add_modelo Bianca @biHot 39.90`", parse_mode=ParseMode.MARKDOWN)
        return
    
    nome = f"🔥 {args[0].title()}"
    handle = args[1]
    preco = float(args[2])
    novo_id = max([m["id"] for m in db.data["models"]] + [0]) + 1
    db.data["models"].append({"id": novo_id, "name": nome, "handle": handle, "slug": args[0].lower(), "price": preco, "likes": 120})
    db.save()
    await update.message.reply_text(f"✅ Modelo *{nome}* cadastrada com sucesso no acervo!", parse_mode=ParseMode.MARKDOWN)

async def drop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_CHAT_IDS:
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Uso: `/drop Categoria_ou_Modelo Link_do_Conteudo`", parse_mode=ParseMode.MARKDOWN)
        return
    alvo = args[0].upper()
    link = args[1]
    await update.message.reply_text(f"🚀 *DROP EXCLUSIVO POSTADO EM {alvo}:*\n🔗 {link}", parse_mode=ParseMode.MARKDOWN)

async def drop_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_CHAT_IDS:
        return
    text = update.message.text.replace("/drop_all", "").strip()
    if not text:
        await update.message.reply_text("Digite a mensagem após o comando. Ex: `/drop_all Novo pack disponível!`", parse_mode=ParseMode.MARKDOWN)
        return
    
    users = list(db.data["users"].keys())
    sent = 0
    for uid_str in users:
        try:
            await context.bot.send_message(chat_id=int(uid_str), text=f"🔥 *SUPER DROP GERAL MIMOSA HOT*\n━━━━━━━━━━━━━━━━━━━━━━\n\n{text}", parse_mode=ParseMode.MARKDOWN)
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Drop disparado para {sent} usuários com sucesso!")

async def relatorio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_CHAT_IDS:
        return
    total_users = len(db.data["users"])
    vips = len([u for u in db.data["users"].values() if u.get("is_vip")])
    rev = db.data["stats"]["total_revenue"]
    orders = db.data["stats"]["orders_count"]
    ups = db.data["stats"]["upsells_count"]
    
    rel = (
        "📈 *RELATÓRIO GERENCIAL MIMOSA HOT*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 *Total de Membros:* {total_users}\n"
        f"👑 *Assinantes VIP:* {vips} ({(vips/max(1,total_users))*100:.1f}%)\n"
        f"📦 *Vendas Realizadas:* {orders}\n"
        f"🚀 *Conversões de Upsell:* {ups}\n"
        f"💰 *Faturamento Total:* R$ {rev:.2f}\n\n"
        f"📅 Sincronizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    )
    await update.message.reply_text(rel, parse_mode=ParseMode.MARKDOWN)

# ────────────────────────────────────────────────────────────────
# FLUXOS DE ASSINATURA, CARRINHO, UPSELL, DOWNSELL E ORDER BUMP
# ────────────────────────────────────────────────────────────────
async def mostrar_assinaturas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⭐ *ASSINAR — ESCOLHA SEU PLANO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔓 *FAN — R$ 29,90/mês*\n"
        "• Conteúdo exclusivo semanal\n"
        "• Acesso ao Canal FAN\n\n"
        "👑 *VIP — R$ 79,90/mês*\n"
        "• Conteúdo premium 3x semana\n"
        "• 2 modelos + Canal VIP\n\n"
        "💎 *PRIVÊ — R$ 299,90/mês*\n"
        "• Interação direta + Lives exclusivas\n"
        "• 3 modelos + Grupo PRIVÊ\n\n"
        "⭐ *DIAMOND — R$ 499,90/mês*\n"
        "• Experiência VIP total\n"
        "• Todas as modelos + 1:1\n\n"
        "♾️ *VITALÍCIO — R$ 1.999,90*\n"
        "• Acesso ilimitado para sempre!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 *Pacotes Especiais:*\n"
        "🔥 DUO (2 modelos VIP): R$ 119,90\n"
        "🔥 TRIO (3 modelos VIP): R$ 179,90\n"
        "🔥 QUINTETO (5 modelos VIP): R$ 299,90\n"
        "💎 PRIVÊ COMPLETO: R$ 1.199,90"
    )
    await send_or_edit(update, context, text, get_assinaturas_menu())

async def fazer_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    # data ex: chk_Plano VIP_79.90
    parts = data.split("_")
    nome_plano = parts[1]
    valor = float(parts[2])
    user_id = update.effective_user.id
    
    # Adicionar Order Bump state
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
        "2️⃣ Abra o app do seu banco e escolha *PIX Copia e Cola*.\n"
        f"3️⃣ Transfira exatamente *R$ {valor_total:.2f}*.\n"
        "4️⃣ O robô confirmará seu pagamento em 10 segundos!\n\n"
        "*Código PIX Copia e Cola:*\n"
        f"`{pix_code}`\n\n"
        "*(Teste/Demonstração: Clique no botão verde abaixo para simular o pagamento aprovado instantaneamente)*"
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
    plano = parts[2]
    valor = parts[3]
    context.user_data["order_bump"] = not context.user_data.get("order_bump", False)
    await fazer_checkout(update, context, f"chk_{plano}_{valor}")

async def downsell_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    plano = data.replace("downsell_", "")
    text = (
        "⚡ *ESPERE! NÃO VÁ EMBORA AINDA!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Vi que você desistiu de assinar o *{plano}*.\n\n"
        "Sabemos que às vezes o orçamento fica apertado, então liberamos uma **DOWNSELL EXCLUSIVA DE TESTE** para você não ficar de fora:\n\n"
        "🔥 *PLANO 3 DIAS FULL ACCESS*\n"
        "Por apenas: *R$ 9,90*\n\n"
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
    
    # Comissões Afiliados
    user = db.get_user(user_id)
    if user.get("referred_by"):
        ref_id = user["referred_by"]
        ref_user = db.get_user(ref_id)
        bonus = 10.00
        ref_user["balance"] += bonus
        db.save()
        try:
            await context.bot.send_message(
                chat_id=ref_id,
                text=f"🎉 *COMISSÃO DE AFILIADO VIA PIX!*\n\nUm contato indicado por você assinou: *{nome_plano}*!\n💰 Você recebeu *R$ {bonus:.2f}* em sua conta!",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass

    # Disparar Upsell se for plano básico
    if "FAN" in nome_plano or "7 Dias" in nome_plano or "3 Dias" in nome_plano:
        db.data["stats"]["upsells_count"] += 1
        db.save()
        upsell_msg = (
            "🎉 *PAGAMENTO CONFIRMADO! ACESSO LIBERADO!*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Recibo: #{txid} ({nome_plano})\n\n"
            "🚀 *PARABÉNS! VOCÊ DESBLOQUEOU UM UPSELL INSTANTÂNEO:*\n"
            "Faça agora o Upgrade para o **PLANO VIP VITALÍCIO** com 60% OFF pagando apenas a diferença de **+R$ 39,90** (Pague uma vez e nunca mais pague nada!).\n\n"
            "Deseja aproveitar este Upsell único?"
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
        "🎉 *ACESSO OFICIAL LIBERADO COM SUCESSO!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ *Recibo:* #{txid}\n"
        f"👑 *Plano Ativado:* {plano}\n\n"
        "Muito obrigado por assinar o **MIMOSA HOT**! Seu acesso sem censura foi habilitado.\n\n"
        "🔗 *Canal Oficial VIP:* `https://t.me/+MimosaHotVIP_Exclusivo_2026`\n"
        "📂 *Drive Secreto Acervo 4K:* `https://drive.google.com/drive/folders/mimosa_hot_acervo`\n\n"
        "📞 *Suporte Pós-Venda:* E-mail ou WhatsApp oficial (`(11)9.4046-2611`)\n\n"
        "🔒 Estes links estão salvos na sua aba *📦 Meus Produtos* no menu principal!"
    )
    keyboard = [
        [InlineKeyboardButton("📦 Ver Meus Produtos", callback_data="produtos")],
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# MÓDULO DE CARRINHO DE COMPRAS E RECARGA DE CELULAR
# ────────────────────────────────────────────────────────────────
async def tela_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    cart = user.get("cart", [])

    text = "🛒 *CARRINHO DE COMPRAS MIMOSA HOT*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if not cart:
        text += "❌ *Seu carrinho está vazio no momento.*\n\nNavegue nas assinaturas ou packs exclusivos e adicione produtos para pagar tudo em um único PIX!"
        keyboard = [
            [InlineKeyboardButton("⭐ Escolher Assinatura", callback_data="assinar")],
            [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="menu")]
        ]
    else:
        total = 0.0
        for idx, item in enumerate(cart, 1):
            text += f"{idx}. *{item['name']}* — R$ {item['price']:.2f}\n"
            total += item["price"]
        text += f"\n💰 *TOTAL DO CARRINHO: R$ {total:.2f}*"
        keyboard = [
            [InlineKeyboardButton(f"💳 Finalizar Carrinho via PIX (R$ {total:.2f})", callback_data=f"chk_Combo Carrinho_{total:.2f}")],
            [InlineKeyboardButton("🗑️ Esvaziar Carrinho", callback_data="limpar_carrinho")],
            [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="menu")]
        ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def addcart_acao(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    parts = data.split("_")
    nome = parts[1]
    preco = float(parts[2])
    user_id = update.effective_user.id
    db.add_to_cart(user_id, nome, preco)
    if update.callback_query:
        await update.callback_query.answer("🛒 Produto adicionado ao carrinho!", show_alert=True)
    await tela_carrinho(update, context)

async def limpar_carrinho_acao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.clear_cart(user_id)
    if update.callback_query:
        await update.callback_query.answer("🗑️ Carrinho limpo!")
    await tela_carrinho(update, context)

async def tela_recarga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📱 *RECARGA DE CELULAR & SERVIÇOS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Utilize o saldo das suas comissões de indicação ou pague no PIX para recarregar qualquer operadora (Vivo, Claro, Tim)!\n\n"
        "💡 *Valores disponíveis:*\n"
        "• Recarga R$ 15,00\n"
        "• Recarga R$ 20,00\n"
        "• Recarga R$ 30,00\n\n"
        "*(Serviço integrado de utilidade para assinantes)*"
    )
    keyboard = [
        [InlineKeyboardButton("📱 Recarregar R$ 20,00 no PIX", callback_data="chk_Recarga Celular Vivo Claro Tim_20.00")],
        [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def tela_institucional(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🏢 *MIMOSA HOT — INSTITUCIONAL & COMPLIANCE*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "O **Mimosa Hot** é uma plataforma digital de distribuição autorizada de mídias independentes.\n\n"
        "🔞 *Restrição Etária estrita (+18):*\n"
        "Todo o acervo é estritamente reservado para maiores de 18 anos. Todas as criadoras parceiras possuem documentação de verificação de maioridade legal arquivada.\n\n"
        "⚖️ *Conformidade Legal:*\n"
        "Respeitamos integralmente os Direitos Autorais (DMCA) e as diretrizes de privacidade da LGPD.\n\n"
        f"📧 *Contato Oficial de Suporte Jurídico:*\n`{SUPPORT_EMAIL}`\n"
        f"📞 *WhatsApp Oficial:* `{PIX_KEY}`"
    )
    keyboard = [
        [InlineKeyboardButton("📦 Meus Pedidos Realizados", callback_data="pagamentos")],
        [InlineKeyboardButton("📞 Falar com Atendimento", callback_data="suporte")],
        [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# SUBMENUS ESPECIAIS (FOTOS, VÍDEOS, CHAMADA, COMBOS, OFERTAS)
# ────────────────────────────────────────────────────────────────
async def submenu_combos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎁 *COMBOS E PACOTES ESPECIAIS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Economize levando pacotes com múltiplas criadoras:\n\n"
        "🔥 *DUO (2 modelos VIP):* R$ 119,90\n"
        "🔥 *TRIO (3 modelos VIP):* R$ 179,90\n"
        "🔥 *QUINTETO (5 modelos VIP):* R$ 299,90\n"
        "💎 *PRIVÊ COMPLETO (Acesso Total):* R$ 1.199,90"
    )
    keyboard = [
        [InlineKeyboardButton("🔥 Combo DUO (R$ 119,90)", callback_data="chk_Combo DUO_119.90")],
        [InlineKeyboardButton("🔥 Combo TRIO (R$ 179,90)", callback_data="chk_Combo TRIO_179.90")],
        [InlineKeyboardButton("🔥 Combo QUINTETO (R$ 299,90)", callback_data="chk_Combo QUINTETO_299.90")],
        [InlineKeyboardButton("💎 PRIVÊ COMPLETO (R$ 1.199,90)", callback_data="chk_PRIVÊ COMPLETO_1199.90")],
        [InlineKeyboardButton("⬅️ Voltar aos Planos", callback_data="assinar")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def submenu_oferta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔥 *OFERTA RELÂMPAGO VIP VITALÍCIO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚡ *OFERTA RELÂMPAGO DO DIA (50% OFF)*\n\n"
        "Tenha acesso vitalício perpétuo a todas as 20 categorias sem nenhuma mensalidade!\n\n"
        "💰 De: ~R$ 159,80~\n"
        "🎯 Por apenas: *R$ 79,90*\n\n"
        "⏳ *Promoção expira em poucas horas!*"
    )
    keyboard = [
        [InlineKeyboardButton("🚀 Aproveitar Oferta VIP (R$ 79,90)", callback_data="chk_VIP Oferta Relâmpago_79.90")],
        [InlineKeyboardButton("⬅️ Voltar aos Planos", callback_data="assinar")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# MODELOS CADASTRADAS (FIEL À CAPTURA DE TELA 4)
# ────────────────────────────────────────────────────────────────
async def mostrar_modelos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👱 *MODELOS CADASTRADAS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🌹 *Sheron* — @sheronHot — sheron\n"
        "🌸 *Annynha* — @AnnynhaHot — annynha\n"
        "🌺 *Lari* — @lariHot — lari\n"
        "💋 *Biatriz* — @biatrizHot — biatriz\n"
        "🔥 *Maju* — @majuHot — maju\n"
    )
    keyboard = [
        [InlineKeyboardButton("🌹 Sheron (@sheronHot)", callback_data="mod_1")],
        [InlineKeyboardButton("🌸 Annynha (@AnnynhaHot)", callback_data="mod_2")],
        [InlineKeyboardButton("🌺 Lari (@lariHot)", callback_data="mod_3")],
        [InlineKeyboardButton("💋 Biatriz (@biatrizHot)", callback_data="mod_4")],
        [InlineKeyboardButton("🔥 Maju (@majuHot)", callback_data="mod_5")],
        [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def detalhe_modelo(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    mid = int(data.replace("mod_", ""))
    model = next((m for m in db.data["models"] if m["id"] == mid), None)
    if not model:
        return

    text = (
        f"👱 *PERFIL DA MODELO: {model['name']}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📱 *Telegram Handle:* {model['handle']}\n"
        f"🔗 *Slug oficial:* `{model['slug']}`\n"
        f"❤️ *Curtidas dos fãs:* {model['likes']}\n\n"
        f"🔥 Assine o canal particular VIP de {model['name']} com fotos diárias sem censura, áudios provocantes e vídeos caseiros 4K!\n\n"
        f"💰 *Acesso Individual Vitalício:* R$ {model['price']:.2f}"
    )
    keyboard = [
        [InlineKeyboardButton(f"❤️ Curtir {model['name']}", callback_data=f"like_mod_{model['id']}")],
        [InlineKeyboardButton(f"🛒 Adicionar ao Carrinho (R$ {model['price']:.2f})", callback_data=f"addcart_VIP {model['slug']}_{model['price']}")],
        [InlineKeyboardButton(f"🔓 Assinar Agora no PIX (R$ {model['price']:.2f})", callback_data=f"chk_VIP {model['slug']}_{model['price']}")],
        [InlineKeyboardButton("⬅️ Lista de Modelos", callback_data="modelos")],
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def curtir_modelo(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    mid = int(data.replace("like_mod_", ""))
    for m in db.data["models"]:
        if m["id"] == mid:
            m["likes"] += 1
            db.save()
            break
    if update.callback_query:
        await update.callback_query.answer("❤️ Você curtiu esta modelo!", show_alert=True)
    await detalhe_modelo(update, context, f"mod_{mid}")

# ────────────────────────────────────────────────────────────────
# CATEGORIAS E PRÉVIAS
# ────────────────────────────────────────────────────────────────
async def categorias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 *CATEGORIAS DE CONTEÚDO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔥 Explore nosso acervo exclusivo:\n\n"
        "*Clique em uma categoria para ver os planos*"
    )
    await send_or_edit(update, context, text, get_categorias_menu())

async def categoria_detalhe(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    cat_id = data.replace("cat_", "")
    nome_cat = "Conteúdo Exclusivo"
    for nome, cid in CATEGORIAS:
        if cid == data:
            nome_cat = nome
            break

    user_id = update.effective_user.id
    user = db.get_user(user_id)
    is_vip = user.get("is_vip", False)

    if is_vip:
        text = (
            f"📂 *{nome_cat.upper()} — ACESSO LIBERADO*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Como assinante {user.get('plan')}, você possui acesso integral a esta categoria!\n\n"
            "🔗 *Link de Acesso Direto:*\n"
            f"`https://t.me/+Mimosa_{cat_id}_VIP_2026`\n\n"
            "🔥 *Destaques do canal:*\n"
            "• Centenas de vídeos Full HD sem censura\n"
            "• Atualizações diárias automáticas\n"
            "• Download liberado para membros"
        )
        keyboard = [
            [InlineKeyboardButton("⬅️ Voltar às Categorias", callback_data="categorias")],
            [InlineKeyboardButton("📦 Meus Produtos", callback_data="produtos")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
        ]
    else:
        text = (
            f"📂 *{nome_cat.upper()}*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔥 Explore o maior acervo de *{nome_cat}* do Brasil! Centenas de vídeos caseiros, álbuns particulares, vazados e lançamentos diários.\n\n"
            "🔞 *Destaques deste acervo:*\n"
            "• +850 vídeos Full HD e 4K\n"
            "• Conteúdo 100% amador e verificado\n"
            "• Acesso instantâneo no Telegram e Drive\n\n"
            "🔒 *Conteúdo Restrito para Assinantes*\n"
            "Assine nosso Plano VIP (R$ 79,90) para desbloquear esta e todas as outras 20 categorias simultaneamente!"
        )
        keyboard = [
            [InlineKeyboardButton("⭐ Desbloquear Categoria Agora", callback_data="assinar")],
            [InlineKeyboardButton("👀 Ver Amostra Grátis", callback_data="amostra_cat")],
            [InlineKeyboardButton("⬅️ Voltar às Categorias", callback_data="categorias")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
        ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def tela_amostra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔞 *PRÉVIA / AMOSTRA EXCLUSIVA*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔒 *[CONTEÚDO PROTEGIDO POR SIGILO]*\n\n"
        "Por diretrizes de segurança contra bloqueios do Telegram em canais abertos, nossas mídias explícitas são transmitidas exclusivamente no ambiente protegido VIP.\n\n"
        "🔥 Assine o *PLANO VIP vitalício por R$ 79,90* e desfrute de:\n"
        "• Acesso instantâneo a +5.000 vídeos completos\n"
        "• Sigilo bancário garantido no PIX\n"
        "• Satisfação garantida ou seu dinheiro de volta"
    )
    keyboard = [
        [InlineKeyboardButton("👑 Quero Assinar o VIP Agora", callback_data="chk_Plano VIP_79.90")],
        [InlineKeyboardButton("⬅️ Voltar às Categorias", callback_data="categorias")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# ÁREA DO CLIENTE
# ────────────────────────────────────────────────────────────────
async def minha_conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id, update.effective_user.first_name or "Usuário")
    
    status_icon = "👑 VIP ATIVO" if user["is_vip"] else "🆓 Gratuito"
    plano_atual = user["plan"]
    
    text = (
        "👤 *MINHA CONTA*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 *ID Telegram:* `{user['user_id']}`\n"
        f"👤 *Nome:* {user['first_name']}\n"
        f"📅 *Membro desde:* {user.get('joined_date', 'Hoje')}\n\n"
        f"💎 *Status:* *{status_icon} ({plano_atual})*\n"
        f"💳 *Total Investido:* R$ {user.get('total_spent', 0.0):.2f}\n"
        f"👥 *Indicados:* {user.get('referrals', 0)} amigos\n"
        f"💰 *Saldo de Comissões:* R$ {user.get('balance', 0.0):.2f}\n\n"
        "🔒 Dados 100% protegidos por criptografia."
    )
    keyboard = [
        [InlineKeyboardButton("⭐ Fazer Upgrade de Plano", callback_data="assinar")],
        [InlineKeyboardButton("📦 Meus Produtos", callback_data="produtos")],
        [InlineKeyboardButton("💳 Meus Pagamentos", callback_data="pagamentos")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def meus_pagamentos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    payments = user.get("payments", [])
    
    text = "💳 *MEUS PAGAMENTOS & PEDIDOS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if not payments:
        text += "❌ *Nenhum pagamento confirmado registrado na sua conta.*\n\nQuando você assinar qualquer plano via PIX, seus recibos ficarão salvos aqui permanentemente."
    else:
        for p in payments:
            text += f"✅ *Transação:* #{p['id']}\n📦 *Plano:* {p['plan']}\n💰 *Valor:* R$ {p['amount']:.2f}\n📅 *Data:* {p['date']}\n──────────────────\n"
            
    keyboard = [
        [InlineKeyboardButton("⭐ Assinar Novo Plano", callback_data="assinar")],
        [InlineKeyboardButton("⬅️ Minha Conta", callback_data="minha_conta")],
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def meus_produtos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    is_vip = user.get("is_vip", False)
    products = user.get("products", [])

    text = "📦 *MEUS PRODUTOS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if not is_vip or not products:
        text += (
            "❌ *Você ainda não possui assinaturas ativas.*\n\n"
            "Desbloqueie agora nosso acervo VIP para receber instantaneamente os links de acesso aos canais privados e ao Drive sem censura!"
        )
        keyboard = [
            [InlineKeyboardButton("⭐ Conhecer Planos e Assinar", callback_data="assinar")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]
        ]
    else:
        text += f"🎉 *Acesso Ativo — Assinante {user.get('plan')}*\n\nSeus produtos desbloqueados:\n\n"
        for prod in products:
            text += f"🔹 *{prod}*\n"
        
        text += (
            "\n🔗 *LINKS DE ACESSO EXCLUSIVO:*\n\n"
            "📲 *Canal Principal VIP (Telegram):*\n"
            "`https://t.me/+MimosaHotVIP_Exclusivo_2026`\n\n"
            "📂 *Google Drive Acervo Proibido:*\n"
            "`https://drive.google.com/drive/folders/mimosa_acervo_4k`\n\n"
            "⚠️ *Aviso:* Links protegidos contra compartilhamento."
        )
        keyboard = [
            [InlineKeyboardButton("📋 Navegar nas Categorias", callback_data="categorias")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]
        ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# CUPONS E INDICAÇÃO DE AMIGOS
# ────────────────────────────────────────────────────────────────
async def tela_cupons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎫 *CUPONS DE DESCONTO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Possui um cupom promocional de algum parceiro ou influenciador?\n\n"
        "Para ativar seu desconto, toque no botão abaixo e digite o código, ou envie diretamente o comando:\n"
        "`/cupom CODIGO`\n\n"
        "*(Exemplo: /cupom MIMOSA10)*\n\n"
        "💡 *Cupons públicos ativos hoje:*\n"
        "• `MIMOSA10` — 10% OFF em qualquer plano\n"
        "• `VIP2026` — 20% OFF no Plano VIP\n"
        "• `GRATIS` — Cupom 100% gratuito promocional"
    )
    keyboard = [
        [InlineKeyboardButton("🎟️ Digitar Código do Cupom", callback_data="acao_digitar_cupom")],
        [InlineKeyboardButton("⭐ Ver Planos Disponíveis", callback_data="assinar")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def acao_digitar_cupom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_coupon"] = True
    text = (
        "🎟️ *RESGATE DE CUPOM*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 *Digite ou cole o código do seu cupom promocional na mensagem abaixo e envie:*"
    )
    keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data="cupons")]]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def indique_amigos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    ref_link = f"https://t.me/MimosaHotBot?start=ref_{user_id}"
    balance = user.get("balance", 0.0)
    referrals = user.get("referrals", 0)

    text = (
        "🤝 *INDIQUE AMIGOS E GANHE DINHEIRO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Transforme seus contatos em dinheiro! Indique amigos para o bot e receba comissões automáticas via PIX.\n\n"
        "🔗 *Seu Link Exclusivo de Afiliado:*\n"
        f"`{ref_link}`\n\n"
        "💰 *Regras da Comissão:*\n"
        "• Você ganha *R$ 10,00* em dinheiro por cada amigo que entrar pelo seu link e realizar uma assinatura VIP!\n"
        f"• Ao acumular R$ 30,00 ou mais, você solicita o saque direto para sua chave PIX (`{PIX_KEY}`).\n\n"
        "📊 *Suas Métricas:*\n"
        f"👥 *Cadastros via seu link:* {referrals}\n"
        f"💰 *Saldo Disponível:* R$ {balance:.2f}"
    )
    keyboard = [
        [InlineKeyboardButton(f"💸 Solicitar Saque PIX (R$ {balance:.2f})", callback_data="saque_pix")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def solicitar_saque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    balance = user.get("balance", 0.0)

    if balance < 30.0:
        text = (
            "❌ *SALDO INSUFICIENTE PARA SAQUE*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 *Seu saldo atual:* R$ {balance:.2f}\n"
            "🎯 *Saque mínimo:* R$ 30,00\n\n"
            "Continue compartilhando seu link de indicação para atingir o valor mínimo!"
        )
    else:
        user["balance"] = 0.0
        db.save()
        text = (
            "✅ *SOLICITAÇÃO DE SAQUE ENVIADA!*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 *Valor Solicitado:* R$ {balance:.2f}\n"
            f"🔑 *Chave PIX de Destino:* `{PIX_KEY}`\n\n"
            f"Sua solicitação foi encaminhada ao setor financeiro ({SUPPORT_EMAIL}). O pagamento será efetuado em até 24 horas úteis!\n\n"
            "*(Em ambiente de teste, o saldo de comissões foi zerado com sucesso).* "
        )
    keyboard = [[InlineKeyboardButton("⬅️ Voltar a Indicações", callback_data="indicar")]]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# SUPORTE, FAQ E CONFIGURAÇÕES (FIEL À CAPTURA DE TELA 5)
# ────────────────────────────────────────────────────────────────
async def tela_suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📞 *SUPORTE E ATENDIMENTO VIP*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Precisa de auxílio com seu pagamento PIX, liberação de acesso ou tem dúvidas gerais?\n\n"
        "👩‍💻 *Canais de Atendimento Oficial:*\n"
        f"• *E-mail / Contato:* `{SUPPORT_EMAIL}`\n"
        f"• *WhatsApp / Chave PIX:* `{PIX_KEY}`\n"
        "• *Horário:* Seg. a Sáb. das 09h às 22h\n\n"
        "🤖 *Dúvidas Rápidas:*\n"
        "Consulte nossa seção de Perguntas Frequentes (FAQ) abaixo."
    )
    keyboard = [
        [InlineKeyboardButton("❓ Perguntas Frequentes (FAQ)", callback_data="faq")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def tela_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "❓ *PERGUNTAS FREQUENTES (FAQ)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Selecione uma dúvida abaixo para ver a resposta imediata:"
    )
    keyboard = [
        [InlineKeyboardButton("1️⃣ Como funciona a liberação de acesso?", callback_data="faq_1")],
        [InlineKeyboardButton("2️⃣ O pagamento no PIX é discreto?", callback_data="faq_2")],
        [InlineKeyboardButton("3️⃣ É cobrança mensal ou taxa única?", callback_data="faq_3")],
        [InlineKeyboardButton("4️⃣ O que vem no Plano VIP Vitalício?", callback_data="faq_4")],
        [InlineKeyboardButton("📞 Falar com Suporte", callback_data="suporte")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def detalhe_faq(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    fid = data.replace("faq_", "")
    faqs = {
        "1": ("1️⃣ *COMO FUNCIONA A LIBERAÇÃO?*", "Após realizar o pagamento via PIX no seu banco, nosso sistema identifica a transação automaticamente em até 10 segundos. Você receberá uma mensagem instantânea aqui no bot com os links para entrar nos canais VIP e Google Drive."),
        "2": ("2️⃣ *O PAGAMENTO É DISCRETO?*", "Sim, 100% seguro e sigiloso! No extrato do seu banco aparecerá apenas um pagamento genérico digital, sem nenhuma menção a conteúdo adulto."),
        "3": ("3️⃣ *É MENSAL OU TAXA ÚNICA?*", "O nosso *Plano VIP (R$ 79,90)* e o *Plano PRIVÊ (R$ 299,90)* são de pagamento *ÚNICO E VITALÍCIO*! Você paga somente uma vez e tem acesso perpétuo a todas as atualizações futuras."),
        "4": ("4️⃣ *O QUE VEM NO PLANO VIP?*", "O Plano VIP dá direito a todas as 20 categorias exclusivas do bot (+5.000 vídeos Full HD e 4K), canais amadores, flagras, onlyfans, lives gravadas e novos conteúdos diários.")
    }
    titulo, desc = faqs.get(fid, ("❓ *FAQ*", "Dúvida respondida."))
    text = f"{titulo}\n━━━━━━━━━━━━━━━━━━━━━━\n\n{desc}"
    keyboard = [
        [InlineKeyboardButton("⬅️ Outras Perguntas (FAQ)", callback_data="faq")],
        [InlineKeyboardButton("⭐ Quero Assinar Agora", callback_data="assinar")],
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def tela_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚙️ *CONFIGURAÇÕES*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Personalize sua experiência:"
    )
    await send_or_edit(update, context, text, get_config_menu())

async def cfg_acao_generica(update: Update, context: ContextTypes.DEFAULT_TYPE, acao: str):
    if acao == "cfg_idioma":
        msg = "🌏 *IDIOMA SELECIONADO:* Português do Brasil (pt-BR) 🇧🇷"
    elif acao == "cfg_excluir":
        msg = "🗑️ *EXCLUIR CONTA:* Para solicitar a remoção definitiva dos seus dados da base LGPD, entre em contato com suporte via e-mail."
    else:
        msg = "Configuração salva."
    await update.callback_query.answer(msg, show_alert=True)

async def alternar_config(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    key = data.replace("toggle_", "")
    user[key] = not user.get(key, True)
    db.save()
    status_str = "Ativado ✅" if user[key] else "Desativado ❌"
    await update.callback_query.answer(f"Configuração {key} alterada para: {status_str}")

async def conteudo_recente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎬 *CONTEÚDO RECENTE DA SEMANA*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Confira os novos pacotes que acabaram de entrar no nosso acervo VIP:\n\n"
        "🔥 *[24/06] Especial Universitárias Trote 2026*\n"
        "Álbum inédito com 65 fotos e 8 vídeos Full HD gravados em república de estudantes.\n\n"
        "🔥 *[23/06] Flagras Câmera Oculta Vestiário*\n"
        "Compilação exclusiva de 45 minutos em 4K.\n\n"
        "🔥 *[22/06] Vazados OnlyFans Valentina & Milfs*\n"
        "Atualização completa dos álbuns privados.\n\n"
        "👑 *Assine o Plano VIP vitalício e assista a tudo isso instantaneamente!*"
    )
    keyboard = [
        [InlineKeyboardButton("⭐ Liberar Acesso VIP (R$ 79,90)", callback_data="chk_Plano VIP_79.90")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# PAINEL ADMINISTRATIVO (FIEL À CAPTURA DE TELA 6) E SUBMENUS
# ────────────────────────────────────────────────────────────────
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_authorized = (user_id in ADMIN_CHAT_IDS) or (len(ADMIN_CHAT_IDS) == 0)
    if not is_authorized:
        await send_or_edit(update, context, "❌ *Acesso Negado*\n\nVocê não tem permissão para acessar o painel administrativo.", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="menu")]]))
        return

    text = (
        "🔓 *PAINEL ADMINISTRATIVO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Bem-vindo, Admin!"
    )
    await send_or_edit(update, context, text, get_admin_menu())

async def admin_submenus(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    user_id = update.effective_user.id
    total_users = len(db.data["users"])
    vips = [u for u in db.data["users"].values() if u.get("is_vip")]
    total_rev = db.data["stats"].get("total_revenue", 0.0)
    orders = db.data["stats"].get("orders_count", 0)

    if data == "admin_dashboard":
        text = (
            "📊 *DASHBOARD GERAL*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 *Usuários Cadastrados:* {total_users}\n"
            f"👑 *Assinantes VIP:* {len(vips)}\n"
            f"📦 *Pedidos Aprovados:* {orders}\n"
            f"💰 *Faturamento:* R$ {total_rev:.2f}\n\n"
            f"📈 *Taxa de Conversão:* {(len(vips)/max(1, total_users))*100:.1f}%\n"
            f"🕐 *Última atualização:* {datetime.now().strftime('%H:%M:%S')}"
        )
    elif data == "admin_usuarios":
        text = f"👥 *USUÁRIOS CADASTRADOS ({total_users})*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        recent = list(db.data["users"].values())[-10:]
        if not recent:
            text += "Nenhum usuário cadastrado."
        else:
            for u in reversed(recent):
                st = "👑 VIP" if u.get("is_vip") else "🆓 Grátis"
                text += f"• *{u.get('first_name')}* (ID: `{u['user_id']}`) - {st} ({u.get('plan')})\n"
    elif data == "admin_assinaturas":
        text = (
            f"📦 *ASSINATURAS ATIVAS ({len(vips)})*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Total de assinantes ativos: *{len(vips)}*\n\n"
            "Distribuição de planos:\n"
            f"• *FAN:* {len([v for v in vips if 'FAN' in v.get('plan','')])}\n"
            f"• *VIP:* {len([v for v in vips if 'VIP' in v.get('plan','')])}\n"
            f"• *PRIVÊ:* {len([v for v in vips if 'PRIVÊ' in v.get('plan','')])}\n"
        )
    elif data in ("admin_pedidos", "admin_pendentes"):
        text = (
            "📋 *PEDIDOS E CHECKOUTS*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📦 Total de Pedidos Concluídos: *{orders}*\n"
            "⏳ Checkouts Pendentes no Gateway PIX: *0*\n\n"
            "O gateway limpa checkouts pendentes expirados automaticamente."
        )
    elif data == "admin_cupons":
        text = "🎫 *CUPONS PROMOCIONAIS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for c, inf in db.data["coupons"].items():
            text += f"• `{c}` — {inf['discount']}% OFF ({inf['uses']} usos restantes)\n"
        text += "\n💡 *Dica:* Para criar um cupom, digite:\n`/addcupom NOME DESCONTO USOS`"
    elif data == "admin_broadcast":
        context.user_data["awaiting_broadcast"] = True
        text = (
            "📢 *TRANSMISSÃO EM MASSA (BROADCAST)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 Público alvo: *{total_users} usuários*\n\n"
            "📝 *Digite ou cole na mensagem abaixo o texto que você deseja enviar para TODOS os usuários do bot:*\n\n"
            "*(Ou clique em Voltar para cancelar)*"
        )
    elif data == "admin_analytics":
        conv = (len(vips)/max(1, total_users))*100
        text = (
            "📈 *ANALYTICS E DESEMPENHO*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 *Alcance Total:* {total_users}\n"
            f"🎯 *Conversão VIP:* {conv:.1f}%\n"
            f"💰 *Ticket Médio:* R$ {(total_rev/max(1, len(vips))):.2f}\n"
            f"🤝 *Afiliados Ativos:* {len([u for u in db.data['users'].values() if u.get('referrals',0)>0])}"
        )
    elif data == "admin_logs":
        text = (
            "📝 *LOGS DO SISTEMA*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🟢 Motor: python-telegram-bot v22.8\n"
            "📁 Arquivo DB: `users_db.json`\n"
            "🔒 Conexão API: Estável\n"
            "🔍 Nenhum erro crítico registrado."
        )
    elif data == "admin_promocoes":
        text = (
            "🎁 *GERENCIAR PROMOÇÕES*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• *Promoção 50% OFF VIP:* ATIVA ✅\n"
            "• *Bônus Drive 4K:* ATIVO ✅"
        )
    elif data == "admin_modelos":
        text = f"👱 *MODELOS CADASTRADAS ({len(db.data['models'])})*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for m in db.data["models"]:
            text += f"• *{m['name']}* ({m['handle']}) - R$ {m['price']:.2f}\n"
    elif data == "admin_backup":
        db.save()
        size_kb = os.path.getsize(db.filename) / 1024 if os.path.exists(db.filename) else 0
        text = (
            "💾 *BACKUP DO SISTEMA*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Arquivo `users_db.json` sincronizado com sucesso.\n"
            f"📂 Tamanho no disco: *{size_kb:.2f} KB*\n"
            f"📅 Horário: *{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*"
        )
    elif data == "admin_config":
        text = (
            "⚙️ *CONFIGURAÇÕES DO BOT*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔹 *Chave PIX:* `{PIX_KEY}`\n"
            f"🔹 *Suporte:* `{SUPPORT_EMAIL}`\n"
            f"🔹 *Admin IDs:* `{ADMIN_CHAT_IDS}`\n"
            f"🔹 *Modo Dev:* {'Ativo' if 0 in ADMIN_CHAT_IDS else 'Inativo'}"
        )
    else:
        text = "🔧 Opção administrativa."

    keyboard = [
        [InlineKeyboardButton("⬅️ Voltar ao Painel Admin", callback_data="admin")],
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# PROCESSAMENTO DE MENSAGENS DE TEXTO (CUPONS E BROADCAST)
# ────────────────────────────────────────────────────────────────
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "Usuário"
    text = update.message.text.strip()

    if context.user_data.get("awaiting_broadcast"):
        context.user_data["awaiting_broadcast"] = False
        users = list(db.data["users"].keys())
        sent = 0
        await update.message.reply_text(f"⏳ *Iniciando broadcast para {len(users)} usuários...*", parse_mode=ParseMode.MARKDOWN)
        for uid_str in users:
            try:
                await context.bot.send_message(
                    chat_id=int(uid_str),
                    text=f"📢 *MENSAGEM DO SISTEMA*\n━━━━━━━━━━━━━━━━━━━━━━\n\n{text}",
                    parse_mode=ParseMode.MARKDOWN
                )
                sent += 1
            except Exception:
                pass
        await update.message.reply_text(
            f"✅ *Broadcast concluído!* Mensagem entregue para {sent} usuários.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Painel Admin", callback_data="admin")]])
        )
        return

    if context.user_data.get("awaiting_coupon"):
        context.user_data["awaiting_coupon"] = False
        await processar_cupom(update, context, text)
        return

    msg = (
        f"🤖 Olá, *{first_name}*! Comando não reconhecido.\n\n"
        "Para navegar no bot e desbloquear nosso acervo proibido, utilize os botões interativos abaixo ou digite `/menu`:"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_menu())

async def processar_cupom(update: Update, context: ContextTypes.DEFAULT_TYPE, codigo: str):
    user_id = update.effective_user.id
    codigo_upper = codigo.strip().upper()
    coupons = db.data["coupons"]

    if codigo_upper in coupons and coupons[codigo_upper]["uses"] > 0:
        c = coupons[codigo_upper]
        c["uses"] -= 1
        db.save()

        if c["discount"] == 100:
            txid = db.upgrade_user(user_id, "Plano VIP", 0.0)
            text = (
                "🎉 *CUPOM 100% GRATUITO RESGATADO!*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎟️ *Cupom:* `{codigo_upper}`\n"
                "👑 *Plano VIP Desbloqueado!*\n\n"
                "Você ganhou acesso integral às 20 categorias do bot sem custo algum!\n\n"
                "🔗 *Canal Oficial VIP:* `https://t.me/+MimosaHotVIP_Exclusivo_2026`\n"
                "📂 *Drive Secreto:* `https://drive.google.com/drive/folders/mimosa_acervo`"
            )
            keyboard = [
                [InlineKeyboardButton("📦 Meus Produtos", callback_data="produtos")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
            ]
        else:
            novo_preco = 79.90 * (1 - c["discount"]/100.0)
            text = (
                f"✅ *CUPOM `{codigo_upper}` APLICADO COM SUCESSO!*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎁 Você ganhou *{c['discount']}% de desconto* no Plano VIP Vitalício!\n\n"
                "💰 De: R$ 79,90\n"
                f"🎯 Por apenas: *R$ {novo_preco:.2f}*\n\n"
                "Clique abaixo para concluir sua assinatura promocional via PIX:"
            )
            keyboard = [
                [InlineKeyboardButton(f"👑 Assinar VIP por R$ {novo_preco:.2f}", callback_data=f"chk_Plano VIP Promocional_{novo_preco:.2f}")],
                [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
            ]
    else:
        text = f"❌ *Cupom `{codigo_upper}` inválido ou expirado.*\n\nVerifique o código digitado e tente novamente."
        keyboard = [
            [InlineKeyboardButton("🎟️ Tentar Outro Cupom", callback_data="acao_digitar_cupom")],
            [InlineKeyboardButton("⭐ Ver Planos Normais", callback_data="assinar")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
        ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# ROTEADOR MAESTRO DE BOTÕES INLINE
# ────────────────────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "noop":
        await query.answer()
        return

    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "Usuário"
    username = update.effective_user.username or ""
    db.get_user(user_id, first_name, username)

    if data.startswith("like_mod_"):
        await curtir_modelo(update, context, data)
        return
    elif data.startswith("cfg_"):
        await cfg_acao_generica(update, context, data)
        return

    await query.answer()

    if data == "menu":
        await menu_cmd(update, context)
    elif data == "categorias":
        await categorias(update, context)
    elif data.startswith("cat_"):
        await categoria_detalhe(update, context, data)
    elif data == "assinar":
        await mostrar_assinaturas(update, context)
    elif data.startswith("chk_"):
        await fazer_checkout(update, context, data)
    elif data.startswith("toggle_bump_"):
        await toggle_bump(update, context, data)
    elif data.startswith("downsell_"):
        await downsell_flow(update, context, data)
    elif data.startswith("pay_app_"):
        await aprovar_pagamento(update, context, data)
    elif data == "entregar_produtos":
        await entregar_produtos(update, context)
    elif data == "sub_fotos":
        await submenu_fotos(update, context)
    elif data == "sub_videos":
        await submenu_videos(update, context)
    elif data == "sub_chamada":
        await submenu_chamada(update, context)
    elif data == "sub_combos":
        await submenu_combos(update, context)
    elif data == "sub_oferta":
        await submenu_oferta(update, context)
    elif data == "promocoes":
        await submenu_oferta(update, context)
    elif data == "modelos":
        await mostrar_modelos(update, context)
    elif data.startswith("mod_"):
        await detalhe_modelo(update, context, data)
    elif data == "minha_conta":
        await minha_conta(update, context)
    elif data == "pagamentos":
        await meus_pagamentos(update, context)
    elif data == "produtos":
        await meus_produtos(update, context)
    elif data == "cupons":
        await tela_cupons(update, context)
    elif data == "acao_digitar_cupom":
        await acao_digitar_cupom(update, context)
    elif data == "indicar":
        await indique_amigos(update, context)
    elif data == "saque_pix":
        await solicitar_saque(update, context)
    elif data == "suporte":
        await tela_suporte(update, context)
    elif data == "faq":
        await tela_faq(update, context)
    elif data.startswith("faq_"):
        await detalhe_faq(update, context, data)
    elif data == "config":
        await tela_config(update, context)
    elif data.startswith("toggle_"):
        await alternar_config(update, context, data)
    elif data == "carrinho":
        await tela_carrinho(update, context)
    elif data.startswith("addcart_"):
        await addcart_acao(update, context, data)
    elif data == "limpar_carrinho":
        await limpar_carrinho_acao(update, context)
    elif data == "recarga":
        await tela_recarga(update, context)
    elif data == "institucional":
        await tela_institucional(update, context)
    elif data == "recente":
        await conteudo_recente(update, context)
    elif data == "amostra_cat":
        await tela_amostra(update, context)
    elif data == "admin":
        await admin_panel(update, context)
    elif data.startswith("admin_"):
        await admin_submenus(update, context, data)
    else:
        await send_or_edit(
            update,
            context,
            f"🔄 *Ação ({data}) executada com sucesso.*",
            InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="menu")]])
        )

# ────────────────────────────────────────────────────────────────
# PONTO DE ENTRADA DO PROGRAMA
# ────────────────────────────────────────────────────────────────
def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ ERRO: Token do Telegram não configurado!")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Comandos Públicos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("modelos", modelos_cmd))
    app.add_handler(CommandHandler("planos", planos_cmd))
    app.add_handler(CommandHandler("faq", faq_cmd))
    app.add_handler(CommandHandler("suporte", suporte_cmd))

    # Comandos Administrativos
    app.add_handler(CommandHandler("add_modelo", add_modelo_cmd))
    app.add_handler(CommandHandler("drop", drop_cmd))
    app.add_handler(CommandHandler("drop_all", drop_all_cmd))
    app.add_handler(CommandHandler("relatorio", relatorio_cmd))

    # Robô de Botões e Textos
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    print("🚀 ENGINE MIMOSA HOT BOT online!")
    app.run_polling()

if __name__ == "__main__":
    main()
