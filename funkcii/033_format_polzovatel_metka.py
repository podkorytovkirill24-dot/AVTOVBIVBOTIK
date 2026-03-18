def format_user_label(user_id: int, username: Optional[str] = None) -> str:
    username = (username or "").strip()
    user_part = f"@{username}" if username else "без username"
    return f"Пользователь: {user_part} | ID: {user_id}"
