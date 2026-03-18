def build_settings_menu(conn: sqlite3.Connection) -> InlineKeyboardMarkup:
    stop = "⛔ Stop-Work" + (" ✅" if get_config_bool(conn, "stop_work") else " ❌")
    auto_slip_minutes = get_config_int(conn, "auto_slip_minutes", 15)
    auto_slip = f"🔁 Авто-слёт ({auto_slip_minutes}м)" + (" ✅" if get_config_bool(conn, "auto_slip_on") else " ❌")
    repeat_submit = "🔁 Повторная сдача" + (" ✅" if get_config_bool(conn, "allow_repeat") else " ❌")
    issue_dept = "🗂 Выдача по отделам"
    lunch = "🍽 Расписание обедов" + (" ✅" if get_config_bool(conn, "lunch_on") else " ❌")
    iam_minutes = get_config_int(conn, "i_am_here_minutes", 10)
    iam_here = f"👋 Я тут ({iam_minutes}м)" + (" ✅" if get_config_bool(conn, "i_am_here_on") else " ❌")
    input_type = "🧩 Тип вбива: приоритеты" if get_config_bool(conn, "use_priorities", True) else "🧩 Тип вбива: FIFO"
    referral = "👥 Рефералка" + (" ✅" if get_config_bool(conn, "referral_enabled", True) else " ❌")
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(input_type, callback_data="adm:input_type"),
                InlineKeyboardButton(stop, callback_data="adm:toggle:stop_work"),
            ],
            [
                InlineKeyboardButton("💲 Тарифы", callback_data="adm:tariffs"),
                InlineKeyboardButton("⚡ Приоритеты", callback_data="adm:priorities"),
            ],
            [
                InlineKeyboardButton(auto_slip, callback_data="adm:auto_slip"),
                InlineKeyboardButton(repeat_submit, callback_data="adm:toggle:allow_repeat"),
            ],
            [
                InlineKeyboardButton("🔢 Лимит сдачи", callback_data="adm:limit"),
                InlineKeyboardButton(iam_here, callback_data="adm:i_am_here"),
            ],
            [
                InlineKeyboardButton("📥 Приемки (/num)", callback_data="adm:departments"),
                InlineKeyboardButton("🏢 Привязки (/set)", callback_data="adm:offices"),
            ],
            [
                InlineKeyboardButton(lunch, callback_data="adm:lunch"),
                InlineKeyboardButton("📋 Заявки", callback_data="adm:requests"),
            ],
            [InlineKeyboardButton(issue_dept, callback_data="adm:issue_by_departments")],
            [
                InlineKeyboardButton(referral, callback_data="adm:referral"),
                InlineKeyboardButton("✏️ Саппорт", callback_data="adm:support"),
            ],
            [InlineKeyboardButton("🔔 Уведомления", callback_data="adm:notifications")],
            [InlineKeyboardButton("⬇ Слёт всем", callback_data="adm:slip_all")],
            [InlineKeyboardButton("⬅ Назад", callback_data="adm:panel")],
        ]
    )
