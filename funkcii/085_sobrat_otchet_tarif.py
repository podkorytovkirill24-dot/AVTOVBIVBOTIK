def build_report_tariff(conn: sqlite3.Connection) -> str:
    rows = conn.execute(
        "SELECT t.name, "
        "SUM(CASE WHEN q.status='success' THEN 1 ELSE 0 END) AS success, "
        "SUM(CASE WHEN q.status='slip' THEN 1 ELSE 0 END) AS slip, "
        "SUM(CASE WHEN q.status='error' THEN 1 ELSE 0 END) AS error, "
        "SUM(CASE WHEN q.status='canceled' THEN 1 ELSE 0 END) AS canceled "
        "FROM tariffs t LEFT JOIN queue_numbers q ON q.tariff_id = t.id "
        "GROUP BY t.id ORDER BY t.id"
    ).fetchall()
    lines = ["📈 Отчёт по тарифам", "Формат: успех | слёт | ошибка | отмена | всего | успех%", ""]
    for r in rows:
        processed = (
            int(r["success"] or 0)
            + int(r["slip"] or 0)
            + int(r["error"] or 0)
            + int(r["canceled"] or 0)
        )
        lines.append(
            f"• {r['name']}: "
            f"{r['success']} | {r['slip']} | {r['error']} | {r['canceled']} | "
            f"{processed} | {pct(int(r['success'] or 0), processed)}"
        )
    return "\n".join(lines)
