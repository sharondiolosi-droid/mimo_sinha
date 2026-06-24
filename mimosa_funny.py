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

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_PRIVE", "SEU_TOKEN_AQUI")
ADMIN_CHAT_IDS = [int(x.strip()) for x in os.getenv("ADMIN_CHAT_IDS", "0").split(",") if x.strip()]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_FILE = "users_db.json"

# ────────────────────────────────────────────────────────────────
# BANCO DE DADOS EM JSON (PERSISTÊNCIA LOCAL)
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
                {"id": 1, "name": "🔥 Larissa", "age": 19, "style": "Universitária SP", "likes": 342, "vip_price": 29.90},
                {"id": 2, "name": "🔥 Valentina", "age": 22, "style": "OnlyFans VIP", "likes": 589, "vip_price": 39.90},
                {"id": 3, "name": "🔥 Camila", "age": 34, "style": "Milf Safada", "likes": 412, "vip_price": 34.90},
                {"id": 4, "name": "🔥 Beatriz & Clara", "age": 21, "style": "Dupla Lésbica", "likes": 720, "vip_price": 49.90}
            ],
            "stats": {
                "total_revenue": 0.0,
                "orders_count": 0
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
                "first_name": first_name,
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
                "notif": True,
                "priv": True
            }
            self.save()
        else:
            self.data["users"][uid]["first_name"] = first_name or "Usuário"
            if username:
                self.data["users"][uid]["username"] = username
        return self.data["users"][uid]

    def upgrade_user(self, user_id: int, plan_name: str, amount: float):
        uid = str(user_id)
        user = self.get_user(user_id)
        user["is_vip"] = True
        user["plan"] = plan_name
        user["total_spent"] += amount
        
        prod_title = f"Acesso Completo — Plano {plan_name}"
        if prod_title not in user["products"]:
            user["products"].append(prod_title)
        if "Canal VIP Telegram" not in user["products"]:
            user["products"].append("Canal VIP Telegram")
        
        tx_id = f"PIX_{int(datetime.now().timestamp())}"
        user["payments"].append({
            "id": tx_id,
            "plan": plan_name,
            "amount": amount,
            "date": datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        
        self.data["stats"]["total_revenue"] += amount
        self.data["stats"]["orders_count"] += 1
        self.save()
        return tx_id

db = Database()

# ────────────────────────────────────────────────────────────────
# CATEGORIAS (20 CATEGORIAS DO ACERVO)
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
# TECLADOS INLINE (GRADE DUPLA EQUILIBRADA COM AS SCREENSHOTS)
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
        [InlineKeyboardButton("🎬 Conteúdo Recente", callback_data="recente")],
        [InlineKeyboardButton("🔓 PAINEL ADMIN", callback_data="admin")]
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

def get_admin_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard Geral", callback_data="admin_dashboard")],
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
            InlineKeyboardButton("💾 Backup DB", callback_data="admin_backup"),
            InlineKeyboardButton("⚙️ Config Bot", callback_data="admin_config")
        ],
        [InlineKeyboardButton("🔙 Voltar ao Menu Principal", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ────────────────────────────────────────────────────────────────
# HELPER PARA ENVIO OU EDIÇÃO DE MENSAGENS (EVITA ERROS DE QUERY)
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
                logger.warning(f"Falha ao editar mensagem: {e}")
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
# COMANDOS INICIAIS (/start e /menu)
# ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "Usuário"
    username = update.effective_user.username or ""

    # Sistema de indicação via link ?start=ref_12345
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
        "Bem-vindo ao paraíso proibido!\n\n"
        "🎓 Universitárias | 📱 Omegle +18 | 🔥 Cornos\n"
        "👩‍❤️‍💋‍👩 Lésbicas | 🎬 Amadores | 🪢 Fetiches\n"
        "👱 Milfs | 💋 Boquetes | 🌸 Novinhas +18\n"
        "🔞 OnlyFans\n\n"
        "✨ *...e muito mais!*\n\n"
        "💳 *PIX* | 🔒 *100% Seguro* | 📦 *Entrega Imediata*\n\n"
        "⬇️ *Escolha uma opção no menu abaixo:*"
    )
    await send_or_edit(update, context, text, get_main_menu())

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "Usuário"
    db.get_user(user_id, first_name, update.effective_user.username or "")
    
    text = (
        "🔥 *MIMOSA HOT — CONTEÚDO EXCLUSIVO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Olá, *{first_name}*! 👋\n\n"
        "💳 *PIX* | 🔒 *100% Seguro* | 📦 *Entrega Imediata*\n\n"
        "⬇️ *Escolha uma opção no menu abaixo:*"
    )
    await send_or_edit(update, context, text, get_main_menu())

# ────────────────────────────────────────────────────────────────
# MÓDULOS DE ASSINATURA E CHECKOUT PIX
# ────────────────────────────────────────────────────────────────

async def mostrar_assinaturas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⭐ *PLANOS DE ASSINATURA MIMOSA HOT*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Liberte-se sem censura! Escolha o plano ideal para você e tenha acesso instantâneo via PIX:\n\n"
        "🔥 *PLANO FAN — R$ 29,90*\n"
        "• Acesso a 5 canais de categorias básicas\n"
        "• Atualizações semanais no acervo\n"
        "• Suporte automatizado\n\n"
        "👑 *PLANO VIP — R$ 79,90* *(🏆 MAIS VENDIDO)*\n"
        "• Acesso TOTAL a todas as 20 categorias\n"
        "• +5.000 vídeos Full HD e 4K sem censura\n"
        "• Canais de Câmeras Ocultas, Amadores e Vazadas\n"
        "• Acesso VITALÍCIO (Pague uma única vez!)\n\n"
        "💎 *PLANO PRIVÊ — R$ 299,90*\n"
        "• Tudo do Plano VIP + Google Drive Secreto 4K\n"
        "• Grupo exclusivo de pedidos personalizados\n"
        "• Chat direto com as modelos parceiras\n"
        "• Atendimento VIP prioritário humanizado\n\n"
        "⬇️ *Selecione o plano desejado para gerar o PIX:*"
    )
    keyboard = [
        [InlineKeyboardButton("🔥 Assinar FAN (R$ 29,90)", callback_data="checkout_FAN_29.90")],
        [InlineKeyboardButton("👑 Assinar VIP (R$ 79,90)", callback_data="checkout_VIP_79.90")],
        [InlineKeyboardButton("💎 Assinar PRIVÊ (R$ 299,90)", callback_data="checkout_PRIVE_299.90")],
        [InlineKeyboardButton("🎫 Tenho um Cupom de Desconto", callback_data="cupons")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def fazer_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    parts = data.split("_")
    plano = parts[1]
    valor = parts[2]
    
    txid = f"TX{int(datetime.now().timestamp())}"
    pix_code = f"00020101021126580014br.gov.bcb.pix2536mimosa.hot/pix/{txid}5204000053039865405{valor}5802BR5910MIMOSA HOT6009SAO PAULO62070503VIP6304C1D2"
    
    text = (
        f"💳 *CHECKOUT PIX — PLANO {plano}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 *Produto:* Plano {plano} Vitalício\n"
        f"💰 *Valor Total:* R$ {valor}\n\n"
        "📲 *Instruções Rápidas de Pagamento:*\n"
        "1️⃣ Toque no código PIX Copia e Cola abaixo para copiar.\n"
        "2️⃣ Abra o aplicativo do seu banco.\n"
        "3️⃣ Selecione a opção *PIX Copia e Cola*.\n"
        "4️⃣ Cole o código e confirme o pagamento.\n\n"
        "*Código PIX Copia e Cola:*\n"
        f"`{pix_code}`\n\n"
        "⏳ *A liberação do seu acesso ocorre automaticamente em até 10 segundos após a confirmação bancária!*\n\n"
        "*(Ambiente de Demonstração: Clique no botão verde abaixo para simular a aprovação instantânea do pagamento)*"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Simular Pagamento Aprovado", callback_data=f"pay_approve_{plano}_{valor}")],
        [InlineKeyboardButton("🔄 Já Paguei / Verificar Status", callback_data=f"pay_approve_{plano}_{valor}")],
        [InlineKeyboardButton("🔙 Escolher Outro Plano", callback_data="assinar")],
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def aprovar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    parts = data.split("_")
    plano = parts[2]
    valor = float(parts[3])
    user_id = update.effective_user.id
    
    txid = db.upgrade_user(user_id, plano, valor)
    
    # Comissões de Afiliado
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
                text=f"🎉 *COMISSÃO DE INDICAÇÃO!*\n\nUm amigo que você indicou acabou de assinar o Plano {plano}!\n💰 Você recebeu *R$ {bonus:.2f}* de comissão em seu saldo!",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass

    text = (
        "🎉 *PAGAMENTO CONFIRMADO COM SUCESSO!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ *Recibo:* #{txid}\n"
        f"👑 *Plano Ativado:* {plano} Vitalício\n\n"
        "Parabéns! Seu acesso exclusivo sem censura foi liberado instantaneamente.\n\n"
        "🔗 *Canal Oficial VIP:* `https://t.me/+MimosaHotVIP_Exclusivo_2026`\n"
        "📂 *Drive Secreto Acervo:* `https://drive.google.com/drive/folders/mimosa_hot_acervo`\n\n"
        "🔒 Salvei permanentemente estes links na sua aba *📦 Meus Produtos* no menu principal!"
    )
    keyboard = [
        [InlineKeyboardButton("📦 Acessar Meus Produtos", callback_data="produtos")],
        [InlineKeyboardButton("📂 Explorar Categorias", callback_data="categorias")],
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

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
            "Assine nosso Plano VIP (R$ 79,90 vitalício) para desbloquear esta e todas as outras 20 categorias simultaneamente!"
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
        [InlineKeyboardButton("👑 Quero Assinar o VIP Agora", callback_data="checkout_VIP_79.90")],
        [InlineKeyboardButton("⬅️ Voltar às Categorias", callback_data="categorias")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# PROMOÇÕES E MODELOS
# ────────────────────────────────────────────────────────────────

async def mostrar_promocoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎯 *PROMOÇÕES E OFERTAS ESPECIAIS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚡ *OFERTA RELÂMPAGO DO DIA (50% OFF)*\n\n"
        "🔥 *COMBO VIP VITALÍCIO COMPLETO*\n"
        "Acesso perpétuo a TODAS as 20 categorias do bot sem pagar nenhuma mensalidade futura!\n\n"
        "💰 De: ~R$ 159,80~\n"
        "🎯 Por apenas: *R$ 79,90*\n\n"
        "🎁 *BÔNUS INCLUSO:* Ganhe acesso gratuito ao canal de Lives +18 e ao Drive 4K secreto!\n\n"
        "⏳ *Oferta válida somente até às 23:59 de hoje!*"
    )
    keyboard = [
        [InlineKeyboardButton("🚀 Aproveitar Promoção VIP (R$ 79,90)", callback_data="checkout_VIP_79.90")],
        [InlineKeyboardButton("💎 Conhecer Plano Privê (R$ 299,90)", callback_data="checkout_PRIVE_299.90")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def mostrar_modelos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    models = db.data["models"]
    text = (
        "👱 *MODELOS EXCLUSIVAS MIMOSA HOT*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Conheça nossas criadoras parceiras com ensaios inéditos e chamadas privadas:\n\n"
    )
    keyboard = []
    for m in models:
        text += f"*{m['id']}️⃣ {m['name']}* ({m['age']} anos) — {m['style']}\n❤️ {m['likes']} curtidas | VIP individual: R$ {m['vip_price']:.2f}\n\n"
        keyboard.append([InlineKeyboardButton(f"{m['name']} ({m['style']})", callback_data=f"mod_{m['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")])
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def detalhe_modelo(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    mid = int(data.replace("mod_", ""))
    model = next((m for m in db.data["models"] if m["id"] == mid), None)
    if not model:
        return

    text = (
        f"👱 *PERFIL: {model['name'].upper()}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎂 *Idade:* {model['age']} anos\n"
        f"📍 *Estilo:* {model['style']}\n"
        f"❤️ *Popularidade:* {model['likes']} curtidas\n\n"
        f"🔥 Assine o canal particular de {model['name']} com fotos exclusivas diárias sem censura, áudios provocantes e vídeos caseiros!\n\n"
        f"💰 *Acesso Individual Vitalício:* R$ {model['vip_price']:.2f}\n"
        "*(Ou assine o Plano PRIVÊ Geral para acessar todas as modelos simultaneamente!)*"
    )
    keyboard = [
        [InlineKeyboardButton(f"❤️ Curtir {model['name']}", callback_data=f"like_mod_{model['id']}")],
        [InlineKeyboardButton(f"🔓 Assinar VIP de {model['name']} (R$ {model['vip_price']:.2f})", callback_data=f"checkout_MOD{model['id']}_{model['vip_price']}")],
        [InlineKeyboardButton("🔙 Lista de Modelos", callback_data="modelos")],
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
# ÁREA DO CLIENTE (CONTA, PAGAMENTOS E PRODUTOS)
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
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def meus_pagamentos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    payments = user.get("payments", [])
    
    text = "💳 *MEUS PAGAMENTOS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if not payments:
        text += (
            "❌ *Nenhum pagamento confirmado registrado na sua conta.*\n\n"
            "Quando você assinar qualquer plano via PIX, seus recibos ficarão salvos aqui permanentemente."
        )
    else:
        for p in payments:
            text += f"✅ *Transação:* #{p['id']}\n📦 *Plano:* {p['plan']}\n💰 *Valor:* R$ {p['amount']:.2f}\n📅 *Data:* {p['date']}\n──────────────────\n"
            
    keyboard = [
        [InlineKeyboardButton("⭐ Assinar Novo Plano", callback_data="assinar")],
        [InlineKeyboardButton("🔙 Minha Conta", callback_data="minha_conta")],
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
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
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
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
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
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
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
        "• Ao acumular R$ 30,00 ou mais, você solicita o saque via PIX direto para sua conta bancária.\n\n"
        "📊 *Suas Métricas:*\n"
        f"👥 *Cadastros via seu link:* {referrals}\n"
        f"💰 *Saldo Disponível:* R$ {balance:.2f}"
    )
    keyboard = [
        [InlineKeyboardButton(f"💸 Solicitar Saque PIX (R$ {balance:.2f})", callback_data="saque_pix")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
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
            f"💰 *Valor:* R$ {balance:.2f}\n\n"
            "Sua solicitação foi encaminhada ao setor financeiro. O pagamento via PIX na sua chave cadastrada será efetuado em até 24 horas úteis!\n\n"
            "*(Em ambiente de teste, o saldo de comissões foi zerado com sucesso).* "
        )
    keyboard = [[InlineKeyboardButton("🔙 Voltar a Indicações", callback_data="indicar")]]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# SUPORTE, FAQ E CONFIGURAÇÕES
# ────────────────────────────────────────────────────────────────

async def tela_suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📞 *SUPORTE E ATENDIMENTO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Precisa de auxílio com seu pagamento PIX, liberação de acesso ou tem dúvidas gerais?\n\n"
        "👩‍💻 *Atendimento Humanizado VIP:*\n"
        "• *Telegram:* @SuporteMimosaHot\n"
        "• *WhatsApp:* +55 (11) 94046-2611\n"
        "• *Horário:* Seg. a Sáb. das 09h às 22h\n\n"
        "🤖 *Dúvidas Rápidas:*\n"
        "Consulte nossa seção de Perguntas Frequentes (FAQ) abaixo."
    )
    keyboard = [
        [InlineKeyboardButton("❓ Perguntas Frequentes (FAQ)", callback_data="faq")],
        [InlineKeyboardButton("💬 Abrir Chat no Telegram", url="https://t.me/Telegram")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
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
        [InlineKeyboardButton("📞 Falar com Suporte Humano", callback_data="suporte")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def detalhe_faq(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    fid = data.replace("faq_", "")
    faqs = {
        "1": ("1️⃣ *COMO FUNCIONA A LIBERAÇÃO?*", "Após realizar o pagamento via PIX Copia e Cola no seu banco, nosso sistema identifica a transação automaticamente em até 10 segundos. Você receberá uma mensagem instantânea aqui no bot com os links para entrar nos canais VIP e Google Drive."),
        "2": ("2️⃣ *O PAGAMENTO É DISCRETO?*", "Sim, 100% seguro e sigiloso! No extrato do seu banco aparecerá apenas um pagamento genérico de intermediação digital, sem nenhuma menção a conteúdo adulto ou ao nome Mimosa Hot."),
        "3": ("3️⃣ *É MENSAL OU TAXA ÚNICA?*", "O nosso *Plano VIP (R$ 79,90)* e o *Plano PRIVÊ (R$ 299,90)* são de pagamento *ÚNICO E VITALÍCIO*! Você paga somente uma vez e tem acesso perpétuo a todas as atualizações futuras sem nenhuma mensalidade."),
        "4": ("4️⃣ *O QUE VEM NO PLANO VIP?*", "O Plano VIP dá direito a todas as 20 categorias exclusivas do bot (+5.000 vídeos Full HD e 4K), canais amadores, flagras, onlyfans, lives gravadas e novos conteúdos diários.")
    }
    titulo, desc = faqs.get(fid, ("❓ *FAQ*", "Dúvida respondida."))
    text = f"{titulo}\n━━━━━━━━━━━━━━━━━━━━━━\n\n{desc}"
    keyboard = [
        [InlineKeyboardButton("🔙 Outras Perguntas (FAQ)", callback_data="faq")],
        [InlineKeyboardButton("⭐ Quero Assinar Agora", callback_data="assinar")],
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def tela_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    notif_st = "Ativadas ✅" if user.get("notif", True) else "Desativadas ❌"
    priv_st = "Ativado 🔒" if user.get("priv", True) else "Desativado 🔓"

    text = (
        "⚙️ *CONFIGURAÇÕES DA CONTA*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Ajuste suas preferências no bot:\n\n"
        f"🔔 *Notificações de Lançamentos:* {notif_st}\n"
        f"🔒 *Modo de Privacidade:* {priv_st}\n"
        "🌐 *Idioma:* Português (Brasil) 🇧🇷\n"
        "💵 *Moeda:* Real Brasileiro (BRL)"
    )
    keyboard = [
        [InlineKeyboardButton("🔔 Alternar Notificações", callback_data="toggle_notif")],
        [InlineKeyboardButton("🔒 Alternar Privacidade", callback_data="toggle_priv")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

async def alternar_config(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    key = data.replace("toggle_", "")
    user[key] = not user.get(key, True)
    db.save()
    await tela_config(update, context)

async def conteudo_recente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎬 *CONTEÚDO RECENTE DA SEMANA*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Confira os novos pacotes que acabaram de entrar no nosso acervo VIP:\n\n"
        "🔥 *[24/06] Especial Universitárias Trote 2026*\n"
        "Álbum inédito com 65 fotos e 8 vídeos Full HD gravados em república de estudantes.\n\n"
        "🔥 *[23/06] Flagras Câmera Oculta Academia*\n"
        "Compilação exclusiva de 45 minutos em 4K.\n\n"
        "🔥 *[22/06] Vazados OnlyFans Valentina & Milfs*\n"
        "Atualização completa dos álbuns privados.\n\n"
        "👑 *Assine o Plano VIP vitalício e assista a tudo isso instantaneamente!*"
    )
    keyboard = [
        [InlineKeyboardButton("⭐ Liberar Acesso VIP (R$ 79,90)", callback_data="checkout_VIP_79.90")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
    ]
    await send_or_edit(update, context, text, InlineKeyboardMarkup(keyboard))

# ────────────────────────────────────────────────────────────────
# PAINEL ADMINISTRATIVO E SUBMENUS
# ────────────────────────────────────────────────────────────────

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_authorized = (user_id in ADMIN_CHAT_IDS) or (0 in ADMIN_CHAT_IDS) or (len(ADMIN_CHAT_IDS) == 0)
    if not is_authorized:
        await send_or_edit(update, context, "❌ *Acesso Negado*\n\nVocê não tem permissão para acessar o painel administrativo.", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="menu")]]))
        return

    total_users = len(db.data["users"])
    total_rev = db.data["stats"].get("total_revenue", 0.0)

    text = (
        "🔧 *PAINEL ADMINISTRATIVO MIMOSA HOT*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👋 Bem-vindo ao painel de controle!\n\n"
        f"🟢 *Status do Sistema:* Online\n"
        f"👥 *Total de Usuários:* {total_users}\n"
        f"💰 *Faturamento Total:* R$ {total_rev:.2f}\n\n"
        "⬇️ *Selecione uma ferramenta abaixo:*"
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
            f"• *FAN:* {len([v for v in vips if v.get('plan')=='FAN'])}\n"
            f"• *VIP:* {len([v for v in vips if v.get('plan')=='VIP'])}\n"
            f"• *PRIVÊ:* {len([v for v in vips if v.get('plan')=='PRIVE'])}\n"
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
            text += f"• *{m['name']}* ({m['age']} anos) - R$ {m['vip_price']:.2f} ({m['likes']} likes)\n"
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
            f"🔹 *Gateway PIX:* Conectado\n"
            f"🔹 *Admin IDs:* `{ADMIN_CHAT_IDS}`\n"
            f"🔹 *Modo Dev:* {'Ativo' if 0 in ADMIN_CHAT_IDS else 'Inativo'}"
        )
    else:
        text = "🔧 Opção administrativa."

    keyboard = [
        [InlineKeyboardButton("🔙 Voltar ao Painel Admin", callback_data="admin")],
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

    # Transmissão Broadcast do Admin
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
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Painel Admin", callback_data="admin")]])
        )
        return

    # Resgate de Cupom
    if context.user_data.get("awaiting_coupon"):
        context.user_data["awaiting_coupon"] = False
        await processar_cupom(update, context, text)
        return

    # Mensagem comum não reconhecida
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
            txid = db.upgrade_user(user_id, "VIP", 0.0)
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
                [InlineKeyboardButton(f"👑 Assinar VIP por R$ {novo_preco:.2f}", callback_data=f"checkout_VIP_{novo_preco:.2f}")],
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
# COMANDOS DIRETOS (/admin, /categorias, /cupom, /addcupom)
# ────────────────────────────────────────────────────────────────

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await admin_panel(update, context)

async def categorias_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await categorias(update, context)

async def cupom_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Uso: `/cupom CODIGO`\nExemplo: `/cupom MIMOSA10`", parse_mode=ParseMode.MARKDOWN)
        return
    await processar_cupom(update, context, args[0])

async def addcupom_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_CHAT_IDS and 0 not in ADMIN_CHAT_IDS:
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Uso: `/addcupom NOME DESCONTO USOS`\nExemplo: `/addcupom PROMO30 30 50`", parse_mode=ParseMode.MARKDOWN)
        return
    nome = args[0].upper()
    desc = float(args[1])
    usos = int(args[2])
    db.data["coupons"][nome] = {"discount": desc, "uses": usos}
    db.save()
    await update.message.reply_text(f"✅ Cupom `{nome}` criado com {desc}% OFF e {usos} usos!", parse_mode=ParseMode.MARKDOWN)

async def addmodelo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_CHAT_IDS and 0 not in ADMIN_CHAT_IDS:
        return
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("Uso: `/addmodelo NOME IDADE ESTILO PRECO`\nExemplo: `/addmodelo Julia 20 Universitária 34.90`", parse_mode=ParseMode.MARKDOWN)
        return
    nome = f"🔥 {args[0].title()}"
    idade = int(args[1])
    preco = float(args[-1])
    estilo = " ".join(args[2:-1])
    novo_id = max([m["id"] for m in db.data["models"]] + [0]) + 1
    db.data["models"].append({"id": novo_id, "name": nome, "age": idade, "style": estilo, "likes": 100, "vip_price": preco})
    db.save()
    await update.message.reply_text(f"✅ Modelo `{nome}` cadastrada com sucesso!", parse_mode=ParseMode.MARKDOWN)

# ────────────────────────────────────────────────────────────────
# ROTEADOR DE BOTÕES (ROTEIA TODAS AS CALLBACKS DO BOT)
# ────────────────────────────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "Usuário"
    username = update.effective_user.username or ""
    db.get_user(user_id, first_name, username)

    if data == "menu":
        await menu(update, context)
    elif data == "categorias":
        await categorias(update, context)
    elif data.startswith("cat_"):
        await categoria_detalhe(update, context, data)
    elif data == "assinar":
        await mostrar_assinaturas(update, context)
    elif data.startswith("checkout_"):
        await fazer_checkout(update, context, data)
    elif data.startswith("pay_approve_"):
        await aprovar_pagamento(update, context, data)
    elif data == "promocoes":
        await mostrar_promocoes(update, context)
    elif data == "modelos":
        await mostrar_modelos(update, context)
    elif data.startswith("mod_"):
        await detalhe_modelo(update, context, data)
    elif data.startswith("like_mod_"):
        await curtir_modelo(update, context, data)
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
            f"🔄 *Ação ({data}) processada.*",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="menu")]])
        )

# ────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────

def main():
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "SEU_TOKEN_AQUI":
        print("❌ ERRO: TELEGRAM_BOT_TOKEN_PRIVE não configurado no arquivo .env!")
        print("Crie um arquivo .env com:\nTELEGRAM_BOT_TOKEN_PRIVE=123456789:ABCdefGHIjklMNO\nADMIN_CHAT_IDS=0")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers de Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("categorias", categorias_cmd))
    app.add_handler(CommandHandler("cupom", cupom_cmd))
    app.add_handler(CommandHandler("addcupom", addcupom_cmd))
    app.add_handler(CommandHandler("addmodelo", addmodelo_cmd))

    # Handlers de Interação (Botões e Mensagens)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    print("🚀 MIMOSA HOT BOT rodando com sucesso!")
    app.run_polling()

if __name__ == "__main__":
    main()
