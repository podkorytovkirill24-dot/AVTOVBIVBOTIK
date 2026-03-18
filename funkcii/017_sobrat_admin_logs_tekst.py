def build_admin_logs_text(conn: sqlite3.Connection, limit: int = 30) -> str:
    rows = conn.execute(
        "SELECT admin_user_id, admin_username, action, details, created_at "
        "FROM admin_logs ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    lines = ["🧾 Логи админов"]
    if not rows:
        lines.append("Пока пусто.")
        return "\n".join(lines)
    for r in rows:
        actor = format_user_label(r["admin_user_id"], r["admin_username"])
        details = f" | {r['details']}" if r["details"] else ""
        lines.append(f"• {format_ts(r['created_at'])} | {actor} | {r['action']}{details}")
    return "\n".join(lines)
