def build_main_menu_inline(conn: sqlite3.Connection, is_admin_user: bool) -> InlineKeyboardMarkup:
    submit = get_config(conn, "menu_btn_submit", DEFAULT_CONFIG["menu_btn_submit"])
    queue_btn = get_config(conn, "menu_btn_queue", DEFAULT_CONFIG["menu_btn_queue"])
    archive = get_config(conn, "menu_btn_archive", DEFAULT_CONFIG["menu_btn_archive"])
    profile = get_config(conn, "menu_btn_profile", DEFAULT_CONFIG["menu_btn_profile"])
    support = get_config(conn, "menu_btn_support", DEFAULT_CONFIG["menu_btn_support"])
    admin = get_config(conn, "menu_btn_admin", DEFAULT_CONFIG["menu_btn_admin"])
    iam_on = get_config_bool(conn, "i_am_here_on")
    lunch_on = get_config_bool(conn, "lunch_on")
    rows = [
        [
            InlineKeyboardButton(submit, callback_data="menu:submit"),
            InlineKeyboardButton(queue_btn, callback_data="menu:queue"),
        ],
    ]
    if iam_on:
        rows.append([InlineKeyboardButton("✅ Я тут", callback_data="user:i_am_here")])
    rows.extend([
        [
            InlineKeyboardButton(archive, callback_data="menu:archive"),
            InlineKeyboardButton(profile, callback_data="menu:profile"),
        ],
        [InlineKeyboardButton(support, callback_data="menu:support")],
    ])
    if lunch_on:
        rows.append([InlineKeyboardButton("🍽 Обед", callback_data="user:lunch")])
    if MINI_APP_BASE_URL:
        rows.append([InlineKeyboardButton("💻 Мини-кабинет", web_app=WebAppInfo(url=f"{MINI_APP_BASE_URL}/miniapp"))])
    if is_admin_user:
        rows.append([InlineKeyboardButton(admin, callback_data="menu:admin")])
    return InlineKeyboardMarkup(rows)
