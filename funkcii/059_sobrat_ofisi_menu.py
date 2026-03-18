def _short_title(text: str, limit: int = 26) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def build_offices_menu(conn: sqlite3.Connection) -> Tuple[str, InlineKeyboardMarkup]:
    rows = conn.execute(
        "SELECT p.chat_id, p.thread_id, p.reception_chat_id, p.chat_title, "
        "r.chat_title AS reception_title, t.name AS tariff_name "
        "FROM processing_topics p "
        "LEFT JOIN reception_groups r ON p.reception_chat_id = r.chat_id "
        "LEFT JOIN tariffs t ON r.tariff_id = t.id "
        "ORDER BY p.chat_id, p.thread_id"
    ).fetchall()
    lines = ["🏢 Привязки (/set)"]
    keyboard: List[List[InlineKeyboardButton]] = []
    if not rows:
        lines.append("(привязок нет)")
        lines.append("Для привязки: напишите /set в нужной группе/теме.")
    else:
        for r in rows:
            title = r["chat_title"] or str(r["chat_id"])
            topic = f"тема {r['thread_id']}" if r["thread_id"] else "без темы"
            target = r["tariff_name"] or r["reception_title"] or "не назначено"
            lines.append(f"• {title} ({topic}) → {target}")
            keyboard.append(
                [InlineKeyboardButton(f"🗑 Удалить { _short_title(title) }", callback_data=f"adm:topic:delete:{r['chat_id']}:{r['thread_id']}")]
            )
    keyboard.append([InlineKeyboardButton("⬅ Назад", callback_data="adm:settings")])
    return "\n".join(lines), InlineKeyboardMarkup(keyboard)
