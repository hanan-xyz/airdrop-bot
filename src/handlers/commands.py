from telegram import Update
from telegram.ext import ContextTypes
from src.sheets import GoogleSheetsClient
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
📚 Panduan:
/start - Mulai input data
/help - Bantuan
/cancel - Batalkan
/list - Lihat semua airdrop aktif
/list <type> [page] - Filter berdasarkan tipe (contoh: /list Galxe 1)
/list --deadline <date> [page] - Filter berdasarkan deadline (contoh: /list --deadline 2025-12-31 1)
/list --network <network> [page] - Filter berdasarkan network (contoh: /list --network Ethereum 1)
🔍 Format:
- URL harus valid (https://example.com)
- Tipe: Galxe, Testnet, Layer3, Waitlist, Node (case insensitive)
- Deadline: YYYY-MM-DD
- Network: Ethereum, Binance, Polygon, dll. (case insensitive)
- Page: Nomor halaman (opsional, default 1)
    """
    await update.message.reply_text(help_text)

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sheets_client = GoogleSheetsClient()
    backup_name = sheets_client.backup()
    if backup_name:
        await update.message.reply_text(f"✅ Backup berhasil: {backup_name}")
    else:
        await update.message.reply_text("❌ Gagal membuat backup")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menampilkan daftar airdrop dengan Status=Active, dengan filter dan pagination"""
    sheets_client = GoogleSheetsClient()
    
    # Valid types (case insensitive)
    valid_types = ['galxe', 'testnet', 'layer3', 'waitlist', 'node']
    ITEMS_PER_PAGE = 5

    # Parsing argumen
    filter_type = None
    filter_deadline = None
    filter_network = None
    page = 1

    args = context.args
    if args:
        if args[0].lower() == '--deadline':
            if len(args) < 2:
                await update.message.reply_text("❌ Harap masukkan tanggal setelah --deadline (contoh: /list --deadline 2025-12-31)")
                return
            try:
                filter_deadline = datetime.strptime(args[1], '%Y-%m-%d').date()
                if len(args) > 2 and args[2].isdigit():
                    page = int(args[2])
            except ValueError:
                await update.message.reply_text("❌ Format tanggal salah, gunakan YYYY-MM-DD")
                return
        elif args[0].lower() == '--network':
            if len(args) < 2:
                await update.message.reply_text("❌ Harap masukkan network setelah --network (contoh: /list --network Ethereum)")
                return
            filter_network = args[1].lower()
            if len(args) > 2 and args[2].isdigit():
                page = int(args[2])
        else:
            filter_type = args[0].lower()
            if filter_type not in valid_types:
                await update.message.reply_text(
                    f"❌ Tipe '{args[0]}' tidak valid. Gunakan: {', '.join([t.capitalize() for t in valid_types])}"
                )
                return
            if len(args) > 1 and args[1].isdigit():
                page = int(args[1])

    try:
        worksheet = sheets_client.get_worksheet()
        all_data = worksheet.get_all_values()
        if len(all_data) <= 1:  # Hanya header atau kosong
            await update.message.reply_text("📋 Tidak ada airdrop aktif saat ini.")
            return

        headers = all_data[0]
        status_idx = headers.index('Status')
        nama_idx = headers.index('Nama')
        link_idx = headers.index('Link')
        type_idx = headers.index('Type')
        deadline_idx = headers.index('Deadline')
        network_idx = headers.index('Network')

        # Filter airdrop aktif
        active_airdrops = [
            row for row in all_data[1:]  # Lewati header
            if row[status_idx] == 'Active'
        ]

        # Terapkan filter berdasarkan Type
        if filter_type:
            active_airdrops = [
                row for row in active_airdrops
                if row[type_idx].lower() == filter_type
            ]

        # Terapkan filter berdasarkan Deadline
        if filter_deadline:
            active_airdrops = [
                row for row in active_airdrops
                if row[deadline_idx] and datetime.strptime(row[deadline_idx], '%Y-%m-%d').date() == filter_deadline
            ]

        # Terapkan filter berdasarkan Network
        if filter_network:
            active_airdrops = [
                row for row in active_airdrops
                if row[network_idx].lower() == filter_network
            ]

        if not active_airdrops:
            msg = (
                f"📋 Tidak ada airdrop aktif dengan tipe '{filter_type.capitalize()}'."
                if filter_type else
                f"📋 Tidak ada airdrop aktif dengan deadline '{filter_deadline}'."
                if filter_deadline else
                f"📋 Tidak ada airdrop aktif dengan network '{filter_network.capitalize()}'."
                if filter_network else
                "📋 Tidak ada airdrop aktif saat ini."
            )
            await update.message.reply_text(msg)
            return

        # Pagination
        total_items = len(active_airdrops)
        total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        page = max(1, min(page, total_pages))  # Pastikan page valid
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, total_items)
        paginated_airdrops = active_airdrops[start_idx:end_idx]

        # Format pesan
        filter_text = (
            f" ({filter_type.capitalize()})" if filter_type else
            f" (Deadline: {filter_deadline})" if filter_deadline else
            f" (Network: {filter_network.capitalize()})" if filter_network else ""
        )
        response = f"📋 Daftar Airdrop Aktif{filter_text} - Halaman {page}/{total_pages}:\n\n"
        for i, row in enumerate(paginated_airdrops, start=start_idx + 1):
            response += (
                f"{i}. **{row[nama_idx]}**\n"
                f"   Link: {row[link_idx]}\n"
                f"   Type: {row[type_idx]}\n"
                f"   Deadline: {row[deadline_idx] or 'Tidak ada'}\n"
                f"   Network: {row[network_idx] or 'Tidak ada'}\n\n"
            )

        # Tambahkan info pagination
        if total_pages > 1:
            filter_arg = filter_type or (f"--deadline {filter_deadline}" if filter_deadline else f"--network {filter_network}" if filter_network else "")
            response += f"Gunakan '/list {filter_arg} <page>' untuk halaman lain (contoh: /list {filter_arg} 2)"

        # Bagi pesan jika terlalu panjang (batas Telegram 4096 karakter)
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(response)

        logger.info("Daftar airdrop aktif ditampilkan untuk user %s, filter: %s, page: %d", 
                   update.effective_user.id, filter_type or filter_deadline or filter_network or "tanpa filter", page)
    except Exception as e:
        logger.error("Gagal mengambil daftar airdrop: %s", e, exc_info=True)
        await update.message.reply_text("🔧 Gagal memuat daftar airdrop, coba lagi nanti.")
