import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import logging
from typing import List, Optional
from src.config import Config

logger = logging.getLogger(__name__)

class GoogleSheetsClient:
    def __init__(self):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.client = self._authorize()

    def _authorize(self) -> gspread.Client:
        """Mengautentikasi ke Google Sheets"""
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                Config.CREDENTIALS_PATH, self.scope
            )
            return gspread.authorize(creds)
        except Exception as e:
            logger.critical("Gagal mengautentikasi Google Sheets: %s", e, exc_info=True)
            raise

    def get_worksheet(self) -> gspread.Worksheet:
        """Mendapatkan worksheet utama"""
        try:
            sh = self.client.open_by_key(Config.SPREADSHEET_ID)
            return sh.worksheet(Config.SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            logger.warning("Worksheet tidak ditemukan, membuat baru")
            return self._create_worksheet(sh)

    def _create_worksheet(self, spreadsheet: gspread.Spreadsheet) -> gspread.Worksheet:
        """Membuat worksheet baru dengan header"""
        headers = ['Nama', 'Twitter', 'Discord', 'Telegram', 'Link', 'Type', 'Deadline', 'Reward', 'User ID', 'Status', 'Network', 'Timestamp']
        worksheet = spreadsheet.add_worksheet(Config.SHEET_NAME, rows=1000, cols=15)
        worksheet.append_row(headers)
        return worksheet

    def backup(self) -> Optional[str]:
        """Membuat backup spreadsheet"""
        try:
            sh = self.client.open_by_key(Config.SPREADSHEET_ID)
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            sh.duplicate_sheet(
                source_sheet_id=sh.worksheet(Config.SHEET_NAME).id,
                new_sheet_name=backup_name
            )
            logger.info("Backup berhasil: %s", backup_name)
            return backup_name
        except Exception as e:
            logger.error("Gagal membuat backup: %s", e, exc_info=True)
            return None

    def append_row(self, worksheet: gspread.Worksheet, values: List[str]) -> bool:
        """Menambahkan baris ke worksheet dengan pengecekan Deadline"""
        try:
            deadline = values[6]  # Indeks Deadline
            if deadline and datetime.strptime(deadline, '%Y-%m-%d') < datetime.now():
                values[9] = 'Ended'  # Indeks Status
            else:
                values[9] = values[9] or 'Active'  # Pastikan Status default Active
            
            values.append(datetime.now().isoformat())  # Tambah timestamp
            worksheet.append_row(values)
            logger.info("Data berhasil disimpan: %s", values)
            return True
        except gspread.exceptions.APIError as e:
            logger.error("API Error saat menyimpan data: %s", e, exc_info=True)
            return False

    def update_status(self) -> None:
        """Memperbarui status semua entry berdasarkan Deadline"""
        try:
            worksheet = self.get_worksheet()
            all_data = worksheet.get_all_values()
            headers = all_data[0]
            deadline_idx = headers.index('Deadline')
            status_idx = headers.index('Status')
            
            updates = []
            for i, row in enumerate(all_data[1:], start=2):  # Mulai dari baris 2 (setelah header)
                deadline = row[deadline_idx]
                if deadline and datetime.strptime(deadline, '%Y-%m-%d') < datetime.now() and row[status_idx] != 'Ended':
                    updates.append({'range': f'J{i}', 'values': [['Ended']]})
            
            if updates:
                worksheet.batch_update(updates)
                logger.info("Status diperbarui untuk %d baris", len(updates))
        except Exception as e:
            logger.error("Gagal memperbarui status: %s", e, exc_info=True)
