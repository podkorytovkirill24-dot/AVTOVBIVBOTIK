def _short_title(text: str, limit: int = 26) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def build_departments_menu(conn: sqlite3.Connection) -> Tuple[str, InlineKeyboardMarkup]:
    rows = conn.execute(
        "SELECT r.chat_id, r.chat_title, r.is_active, t.name AS tariff_name, t.duration_min, t.price "
        "FROM reception_groups r "
        "LEFT JOIN tariffs t ON r.tariff_id = t.id "
        "ORDER BY r.chat_title"
    ).fetchall()
    lines = ["🏷 Приёмки (/num)"]
    keyboard: List[List[InlineKeyboardButton]] = []
    if not rows:
        lines.append("Пока нет приёмок.")
        lines.append("Используйте /num в группе, чтобы добавить приёмку.")
    else:
        for r in rows:
            title = r["chat_title"] or str(r["chat_id"])
            tariff = r["tariff_name"] or ""
            duration = f"{int(r['duration_min'] or 0)}" if r["duration_min"] is not None else ""
            price = f"${float(r['price'] or 0):.2f}" if r["price"] is not None else ""
            status = "ВКЛ" if int(r["is_active"] or 0) == 1 else "ВЫКЛ"
            duration_label = f"{duration} мин" if duration else "-"
            lines.append(f"• {title} | {tariff} | {duration_label} | {price} | {status}")
            keyboard.append(
                [InlineKeyboardButton(f"🗑 Удалить { _short_title(title) }", callback_data=f"adm:reception:delete:{r['chat_id']}")]
            )
    keyboard.append([InlineKeyboardButton("⬅ Назад", callback_data="adm:settings")])
    return "\n".join(lines), InlineKeyboardMarkup(keyboard)
