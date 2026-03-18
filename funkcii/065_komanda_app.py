async def cmd_app(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type != "private":
        return
    if not MINI_APP_BASE_URL:
        await update.message.reply_text(
            "Мини-приложение не настроено. Укажите MINI_APP_BASE_URL в .env (https URL)."
        )
        return
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("💻 Открыть мини-кабинет", web_app=WebAppInfo(url=f"{MINI_APP_BASE_URL}/miniapp"))]]
    )
    await update.message.reply_text("Откройте мини-кабинет:", reply_markup=keyboard)
