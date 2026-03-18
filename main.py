# -*- coding: utf-8 -*-
from pathlib import Path

_PAPKA_FUNKCIY = Path(__file__).resolve().parent / 'funkcii'

def _zagruzit_blok(imya_fayla: str) -> None:
    put = _PAPKA_FUNKCIY / imya_fayla
    # utf-8-sig автоматически убирает BOM, если он случайно попал в начало файла
    kod = put.read_text(encoding='utf-8-sig')
    exec(compile(kod, str(put), 'exec'), globals(), globals())

import os
import re
import io
import csv
import json
import time
import hmac
import hashlib
import logging
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlparse
from urllib.request import Request, urlopen

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    ForceReply,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InputFile,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


_zagruzit_blok('001_zagruzka_okruzheniya.py')


load_env()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var not set")

DB_PATH = os.getenv("BOT_DB_PATH", "bot.db")
MINI_APP_BASE_URL = os.getenv("MINI_APP_BASE_URL", "").strip().rstrip("/")
MINI_APP_HOST = os.getenv("MINI_APP_HOST", "127.0.0.1").strip() or "127.0.0.1"
MINI_APP_PORT = int(os.getenv("MINI_APP_PORT", "8080"))
BOT_PUBLIC_USERNAME = os.getenv("BOT_USERNAME", "").strip().lstrip("@")


_zagruzit_blok('002_parsing_admin_aydi.py')


ENV_ADMIN_IDS = _parse_admin_ids()

PHONE_RE = re.compile(r"\d{7,}")


_zagruzit_blok('003_format_telefon.py')


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("avtovbiv-bot")
BOT_STARTED_AT = int(time.time())


DEFAULT_CONFIG = {
    "stop_work": "0",
    "block_pm": "0",
    "require_subscription": "0",
    "allow_repeat": "1",
    "use_priorities": "1",
    "issue_by_departments": "0",
    "referral_enabled": "1",
    "repeat_code": "0",
    "qr_request": "0",
    "detail_archive": "0",
    "notify_taken": "1",
    "notify_success": "1",
    "notify_slip": "1",
    "notify_error": "1",
    "auto_success_on": "0",
    "auto_success_minutes": "5",
    "auto_slip_on": "0",
    "auto_slip_minutes": "15",
    "actualization_on": "0",
    "actualization_minutes": "120",
    "i_am_here_on": "0",
    "i_am_here_minutes": "10",
    "limit_per_day": "0",
    "lunch_on": "0",
    "lunch_start": "13:00",
    "lunch_end": "14:00",
    "lunch_text": "",
    "main_menu_text": "рџЏ  Р“Р»Р°РІРЅРѕРµ РјРµРЅСЋ",
    "main_menu_photo_id": "",
    "menu_btn_submit": "рџ“ћ РЎРґР°С‚СЊ РЅРѕРјРµСЂ",
    "menu_btn_queue": "рџ“Љ РўРµРєСѓС‰Р°СЏ РѕС‡РµСЂРµРґСЊ",
    "menu_btn_archive": "рџ—‚ РђСЂС…РёРІ",
    "menu_btn_profile": "рџ‘¤ РњРѕР№ РїСЂРѕС„РёР»СЊ",
    "menu_btn_support": "рџ›  РўРµС…РїРѕРґРґРµСЂР¶РєР°",
    "menu_btn_admin": "рџ›Ў РђРґРјРёРЅ-РјРµРЅСЋ",
    "menu_btn_home": "рџЏ  Р“Р»Р°РІРЅРѕРµ РјРµРЅСЋ",
}

UI_TEXTS = {
    "admin_panel_title": (
        "рџ›Ў РђРґРјРёРЅ-РїР°РЅРµР»СЊ\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ СЂР°Р·РґРµР» РЅРёР¶Рµ."
    ),
    "settings_title": "вљ™ РќР°СЃС‚СЂРѕР№РєРё",
    "service_title": "рџ§° РЎРµСЂРІРёСЃ",
    "no_access": "РќРµС‚ РґРѕСЃС‚СѓРїР°",
    "reports_menu_title": "📈 Отчёты\n\nВыберите формат:",
    "empty_archive": (
        "рџ—‚ РђСЂС…РёРІ\n\n"
        "РџРѕРєР° РїСѓСЃС‚Рѕ.\n"
        "РЎРґР°Р№С‚Рµ РЅРѕРјРµСЂ С‡РµСЂРµР· РіР»Р°РІРЅРѕРµ РјРµРЅСЋ, С‡С‚РѕР±С‹ РїРѕСЏРІРёР»Р°СЃСЊ РёСЃС‚РѕСЂРёСЏ."
    ),
    "empty_withdrawals": "рџ’° Р—Р°РїСЂРѕСЃРѕРІ РЅР° РІС‹РІРѕРґ РїРѕРєР° РЅРµС‚.",
    "empty_requests": "рџ“ќ Р—Р°СЏРІРѕРє РїРѕРєР° РЅРµС‚.",
    "empty_support_tickets": "вњЏ РћС‚РєСЂС‹С‚С‹С… С‚РёРєРµС‚РѕРІ РїРѕРєР° РЅРµС‚.",
    "empty_tariffs": "рџ’І РўР°СЂРёС„РѕРІ РїРѕРєР° РЅРµС‚.",
    "empty_data": "РќРµС‚ РґР°РЅРЅС‹С….",
}


SUBMIT_RULES_TEXT = (
    "рџ“Њ РџСЂРёРЅРёРјР°РµРј С‚РѕР»СЊРєРѕ KZ РЅРѕРјРµСЂР°.\n"
    "Р¤РѕСЂРјР°С‚: 7XXXXXXXXX (10 С†РёС„СЂ), Р±РµР· РїСЂРѕР±РµР»РѕРІ Рё В«+В».\n"
    "РџСЂРёРјРµСЂ: 77071234567\n"
    "РњРѕР¶РЅРѕ РЅРµСЃРєРѕР»СЊРєРѕ РЅРѕРјРµСЂРѕРІ РІ РѕРґРЅРѕРј СЃРѕРѕР±С‰РµРЅРёРё (РєР°Р¶РґС‹Р№ СЃ РЅРѕРІРѕР№ СЃС‚СЂРѕРєРё).\n"
    "Р•СЃР»Рё РµСЃС‚СЊ С„РѕС‚Рѕ РєРѕРґР° вЂ” РїСЂРёРєСЂРµРїРёС‚Рµ."
)

WORKER_RULES_TEXT = (
    "рџ“‹ РџСЂР°РІРёР»Р° РґР»СЏ РѕРїРµСЂР°С‚РѕСЂРѕРІ:\n"
    "1) Р§С‚РѕР±С‹ РІР·СЏС‚СЊ РЅРѕРјРµСЂ, РЅР°Р¶РјРёС‚Рµ РєРЅРѕРїРєСѓ В«Р’Р·СЏС‚СЊ РЅРѕРјРµСЂВ» РІ СЂР°Р±РѕС‡РµР№ РїР°РЅРµР»Рё.\n"
    "2) РџРѕСЃР»Рµ РѕР±СЂР°Р±РѕС‚РєРё РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ РїРѕСЃС‚Р°РІСЊС‚Рµ СЃС‚Р°С‚СѓСЃ: вњ… Р’СЃС‚Р°Р» / вќЊ РћС€РёР±РєР° / вљ  РЎР»РµС‚РµР».\n"
    "3) Р”Р»СЏ СЃРІСЏР·Рё СЃ РІР»Р°РґРµР»СЊС†РµРј РёСЃРїРѕР»СЊР·СѓР№С‚Рµ РєРЅРѕРїРєСѓ В«РЎРѕРѕР±С‰РµРЅРёРµ РІР»Р°РґРµР»СЊС†СѓВ» РїРѕРґ РЅРѕРјРµСЂРѕРј."
)


_zagruzit_blok('004_interfeys.py')


_zagruzit_blok('005_poluchit_soedinenie.py')


_zagruzit_blok('006_inicializaciya_baza.py')


_zagruzit_blok('007_kolonka_est.py')


_zagruzit_blok('008_dobavit_kolonka.py')


_zagruzit_blok('009_migraciya_baza.py')


_zagruzit_blok('010_seychas_vremya.py')


_zagruzit_blok('011_format_vremya.py')


_zagruzit_blok('012_format_dlitelnost.py')


_zagruzit_blok('013_procent.py')


_zagruzit_blok('014_status_ponyatno.py')


_zagruzit_blok('015_log_admin_deystvie.py')


_zagruzit_blok('016_uvedomit_polzovatel_napryamuyu.py')


_zagruzit_blok('017_sobrat_admin_logs_tekst.py')



_zagruzit_blok('018_format_msk.py')

_zagruzit_blok('019_ubrat_status_stroki.py')

_zagruzit_blok('020_obedinit_status_tekst.py')

_zagruzit_blok('021_sobrat_prinyatie_tekst.py')
_zagruzit_blok('022_poluchit_config.py')


_zagruzit_blok('023_ustanovit_config.py')


_zagruzit_blok('024_poluchit_config_bulevo.py')


_zagruzit_blok('025_poluchit_config_celoe.py')


_zagruzit_blok('026_proverka_admin.py')


_zagruzit_blok('027_proverka_chat_admin.py')


_zagruzit_blok('028_obnovit_ili_dobavit_polzovatel.py')


_zagruzit_blok('029_obespechit_ref_kod.py')


_zagruzit_blok('030_izvlech_nomera.py')


_zagruzit_blok('031_filtr_kz_nomera.py')


_zagruzit_blok('032_upomyanut_polzovatel.py')


_zagruzit_blok('033_format_polzovatel_metka.py')


_zagruzit_blok('034_opredelit_polzovatel_aydi_vvod.py')


_zagruzit_blok('035_poluchit_bot_username.py')


_zagruzit_blok('036_proverit_telegram_vebapp_inicializaciya_dannie.py')


_zagruzit_blok('037_sobrat_miniapp_polzovatel_nagruzka.py')


_zagruzit_blok('038_sozdat_viplata_iz_miniapp_admin.py')


_zagruzit_blok('039_otpravit_nomera_iz_miniapp.py')


_zagruzit_blok('040_sozdat_vivod_zapros_iz_miniapp.py')


_zagruzit_blok('041_sobrat_miniapp_html.py')


_zagruzit_blok('042_mini_app_obrabotchik.py')


_zagruzit_blok('043_start_miniapp_server.py')


_zagruzit_blok('044_sobrat_glavniy_menu_inline.py')


_zagruzit_blok('045_ustanovit_sostoyanie.py')


_zagruzit_blok('046_poluchit_sostoyanie.py')


_zagruzit_blok('047_ochistit_sostoyanie.py')


_zagruzit_blok('048_proverka_obed_vremya.py')


_zagruzit_blok('049_poluchit_period_diapazon.py')


_zagruzit_blok('050_sobrat_admin_panel.py')


_zagruzit_blok('051_sobrat_servis_menu.py')


_zagruzit_blok('052_sobrat_servis_tekst.py')

_zagruzit_blok('053_sobrat_ochered_csv.py')


_zagruzit_blok('054_sobrat_nastroiki_menu.py')


_zagruzit_blok('055_parsing_tarif_tekst.py')


_zagruzit_blok('056_sobrat_notifications_menu.py')


_zagruzit_blok('057_sobrat_tarifi_menu.py')


_zagruzit_blok('058_sobrat_otdeli_menu.py')


_zagruzit_blok('059_sobrat_ofisi_menu.py')


_zagruzit_blok('060_sobrat_glavniy_menu_nastroiki.py')


_zagruzit_blok('061_otpravit_glavniy_menu_chat.py')


_zagruzit_blok('062_otpravit_glavniy_menu.py')


_zagruzit_blok('063_komanda_start.py')


_zagruzit_blok('064_komanda_admin.py')


_zagruzit_blok('065_komanda_app.py')


_zagruzit_blok('066_komanda_ustanovit.py')


_zagruzit_blok('067_komanda_num.py')


_zagruzit_blok('068_obrabotat_lichka_menu.py')


_zagruzit_blok('069_rasschitat_polzovatel_balans.py')


_zagruzit_blok('070_sobrat_otpravit_podskazka.py')


_zagruzit_blok('071_menu_pokazat_tarifi.py')


_zagruzit_blok('072_menu_pokazat_ochered.py')


_zagruzit_blok('073_menu_pokazat_arhiv.py')


_zagruzit_blok('074_menu_pokazat_profil.py')


_zagruzit_blok('075_menu_start_podderzhka.py')


_zagruzit_blok('076_obrabotat_lichka_sostoyanie.py')


_zagruzit_blok('077_obrabotat_operator_kod_otvet.py')


_zagruzit_blok('078_obrabotat_gruppa_operator_sostoyanie.py')


_zagruzit_blok('079_obrabotat_gruppa_zapros_nomer.py')


_zagruzit_blok('080_obrabotat_gruppa_submission.py')


_zagruzit_blok('081_fetch_sleduyushiy_ochered.py')


_zagruzit_blok('082_otpravit_nomer_to_operator.py')


_zagruzit_blok('083_obrabotat_callback.py')


_zagruzit_blok('084_sobrat_statistika_tekst.py')


_zagruzit_blok('085_sobrat_otchet_tarif.py')


_zagruzit_blok('086_sobrat_otchet_obschiy.py')


_zagruzit_blok('087_sobrat_otchet_detalniy.py')


_zagruzit_blok('088_sobrat_topi.py')


_zagruzit_blok('089_sobrat_topi_csv.py')


_zagruzit_blok('090_sobrat_csv.py')


_zagruzit_blok('091_obrabotat_foto_qr.py')


_zagruzit_blok('092_zadacha_tik.py')


_zagruzit_blok('093_glavniy.py')


if __name__ == "__main__":
    main()


