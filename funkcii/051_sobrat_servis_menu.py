def build_service_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("ℹ️ Информация", callback_data="adm:service:info")],
            [InlineKeyboardButton("🧾 Логи", callback_data="adm:service:logs")],
            [InlineKeyboardButton("🧹 Очистить очередь", callback_data="adm:service:clear_queue")],
            [InlineKeyboardButton("📤 Экспорт очереди", callback_data="adm:service:export_queue")],
            [InlineKeyboardButton("⬅ Назад", callback_data="adm:panel")],
        ]
    )
