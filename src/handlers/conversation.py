from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.config import Config
from src.sheets import GoogleSheetsClient
from src.utils import is_valid_url
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# States
NAMA, TWITTER, DISCORD, TELEGRAM, LINK, TYPE, DEADLINE, REWARD, NETWORK, CONFIRM = range(10)

sheets_client = GoogleSheetsClient()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Halo! Mari tambahkan airdrop baru. Silakan masukkan NAMA:')
    return NAMA

async def get_nama(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['nama'] = update.message.text.strip()
    await update.message.reply_text('Masukkan LINK TWITTER:')
    return TWITTER

async def get_twitter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text.strip()
    if not is_valid_url(url):
        await update.message.reply_text("❌ Format URL Twitter tidak valid!")
        return TWITTER
    context.user_data['twitter'] = url
    await update.message.reply_text('Masukkan LINK DISCORD:')
    return DISCORD

async def get_discord(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text.strip()
    if not is_valid_url(url):
        await update.message.reply_text("❌ Format URL Discord tidak valid!")
        return DISCORD
    context.user_data['discord'] = url
    await update.message.reply_text('Masukkan LINK TELEGRAM:')
    return TELEGRAM

async def get_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text.strip()
    if not is_valid_url(url):
        await update.message.reply_text("❌ Format URL Telegram tidak valid!")
        return TELEGRAM
    context.user_data['telegram'] = url
    await update.message.reply_text('Masukkan LINK AIRDROP:')
    return LINK

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text.strip()
    if not is_valid_url(url):
        await update.message.reply_text("❌ Format URL Airdrop tidak valid!")
        return LINK
    context.user_data['link'] = url
    
    reply_keyboard = [['Galxe', 'Testnet', 'Layer3'], ['Waitlist', 'Node']]
    await update.message.reply_text(
        'Pilih TYPE AIRDROP:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return TYPE

async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['type'] = update.message.text.strip()
    await update.message.reply_text('Masukkan DEADLINE (contoh: 2025-12-31) atau ketik "skip" jika tidak ada:')
    return DEADLINE

async def get_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().lower()
    if text == 'skip':
        context.user_data['deadline'] = ''
    else:
        try:
            datetime.strptime(text, '%Y-%m-%d')
            context.user_data['deadline'] = text
        except ValueError:
            await update.message.reply_text('❌ Format tanggal salah! Gunakan YYYY-MM-DD atau "skip"')
            return DEADLINE
    await update.message.reply_text('Masukkan REWARD (contoh: 1000 XYZ) atau ketik "skip" jika tidak ada:')
    return REWARD

async def get_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().lower()
    context.user_data['reward'] = '' if text == 'skip' else text
    await update.message.reply_text('Masukkan NETWORK (contoh: Ethereum) atau ketik "skip" jika tidak ada:')
    return NETWORK

async def get_network(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().lower()
    context.user_data['network'] = '' if text == 'skip' else text.capitalize()  # Kapitalisasi pertama
    context.user_data['status'] = 'Active'  # Default status
    data = context.user_data
    confirmation = (
        f"Konfirmasi data:\n"
        f"Nama: {data['nama']}\n"
        f"Twitter: {data['twitter']}\n"
        f"Discord: {data['discord']}\n"
        f"Telegram: {data['telegram']}\n"
        f"Link: {data['link']}\n"
        f"Type: {data['type']}\n"
        f"Deadline: {data['deadline'] or 'Tidak ada'}\n"
        f"Reward: {data['reward'] or 'Tidak ada'}\n"
        f"Network: {data['network'] or 'Tidak ada'}\n"
        f"Status: {data['status']}\n"
        "Kirim 'ya' untuk simpan, 'tidak' untuk batalkan"
    )
    await update.message.reply_text(confirmation)
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text.lower().strip()
    if response == 'ya':
        worksheet = sheets_client.get_worksheet()
        row = [
            context.user_data['nama'],
            context.user_data['twitter'],
            context.user_data['discord'],
            context.user_data['telegram'],
            context.user_data['link'],
            context.user_data['type'],
            context.user_data['deadline'],
            context.user_data['reward'],
            str(update.effective_user.id),
            context.user_data['status'],
            context.user_data['network']
        ]
        if sheets_client.append_row(worksheet, row):
            await update.message.reply_text('✅ Data berhasil disimpan!')
        else:
            await update.message.reply_text('🔧 Gagal menyimpan data, coba lagi nanti')
    else:
        await update.message.reply_text('❌ Input dibatalkan')
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('❌ Input dibatalkan')
    context.user_data.clear()
    return ConversationHandler.END
