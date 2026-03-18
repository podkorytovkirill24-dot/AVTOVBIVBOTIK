async def handle_private_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    if not state:
        return
    name = state["name"]
    text = (update.message.text or update.message.caption or "").strip()
    conn = get_conn()

    if name == "submit_numbers":
        numbers = filter_kz_numbers(extract_numbers(text))
        if not numbers:
            conn.close()
            await update.message.reply_text(f"РќРµ РІРёР¶Сѓ KZ РЅРѕРјРµСЂР°.\n\n{SUBMIT_RULES_TEXT}")
            return
        tariff_id = state["data"].get("tariff_id")
        dept_id = state["data"].get("department_id")
        reception_chat_id = state["data"].get("reception_chat_id")
        if not reception_chat_id:
            conn.close()
            clear_state(context)
            await update.message.reply_text("РџСЂРёРµРјРєР° РЅРµ РІС‹Р±СЂР°РЅР°. РћС‚РєСЂРѕР№С‚Рµ РјРµРЅСЋ Рё РІС‹Р±РµСЂРёС‚Рµ С‚Р°СЂРёС„ Р·Р°РЅРѕРІРѕ.")
            return
        allow_repeat = get_config_bool(conn, "allow_repeat", True)
        limit_per_day = get_config_int(conn, "limit_per_day", 0)
        if get_config_bool(conn, "stop_work"):
            conn.close()
            await update.message.reply_text("в›” STOP-WORK\nРџСЂРёРµРјРєР° РІСЂРµРјРµРЅРЅРѕ РЅР° РїР°СѓР·Рµ. РџРѕРїСЂРѕР±СѓР№С‚Рµ РїРѕР·Р¶Рµ.")
            clear_state(context)
            return
        if limit_per_day > 0:
            tz = get_kz_tz() if "get_kz_tz" in globals() else None
            now = datetime.now(tz) if tz else datetime.now()
            start_day = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
            cnt = conn.execute(
                "SELECT COUNT(*) AS cnt FROM queue_numbers "
                "WHERE user_id = ? AND created_at >= ?",
                (update.effective_user.id, int(start_day)),
            ).fetchone()["cnt"]
            if cnt + len(numbers) > limit_per_day:
                conn.close()
                await update.message.reply_text(f"Р›РёРјРёС‚ СЃРґР°С‡Рё РЅР° СЃРµРіРѕРґРЅСЏ: {limit_per_day}.")
                clear_state(context)
                return

        photo_id = None
        if update.message.photo:
            photo_id = update.message.photo[-1].file_id

        pending_before = conn.execute(
            "SELECT COUNT(*) AS cnt FROM queue_numbers WHERE status = 'queued' AND reception_chat_id = ?",
            (reception_chat_id,),
        ).fetchone()["cnt"]
        created_at = now_ts()
        if get_config_bool(conn, "i_am_here_on"):
            conn.execute(
                "UPDATE users SET iam_here_at = CASE WHEN iam_here_at > 0 THEN iam_here_at ELSE ? END, "
                "iam_warned_at = 0 WHERE user_id = ?",
                (created_at, update.effective_user.id),
            )
        accepted = []
        for idx, phone in enumerate(numbers, start=1):
            if not allow_repeat:
                exists = conn.execute(
                    "SELECT id FROM queue_numbers WHERE phone = ? "
                    "AND status IN ('queued','taken','success')",
                    (phone,),
                ).fetchone()
                if exists:
                    continue
            conn.execute(
                "INSERT INTO queue_numbers "
                "(reception_chat_id, user_id, username, phone, status, created_at, tariff_id, department_id, photo_file_id) "
                "VALUES (?, ?, ?, ?, 'queued', ?, ?, ?, ?)",
                (
                    reception_chat_id,
                    update.effective_user.id,
                    update.effective_user.username,
                    phone,
                    created_at + idx,
                    tariff_id,
                    dept_id,
                    photo_id,
                ),
            )
            accepted.append(phone)
        conn.commit()
        conn.close()
        clear_state(context)
        if not accepted:
            await update.message.reply_text("РќРѕРјРµСЂР° РЅРµ РїСЂРёРЅСЏС‚С‹ (РїРѕРІС‚РѕСЂРЅС‹Рµ Р·Р°РїСЂРµС‰РµРЅС‹).")
            return
        await update.message.reply_text(build_accept_text(accepted, pending_before))
        return

    if name == "admin_tariff_add_name":
        if not text:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ С‚Р°СЂРёС„Р°.")
            return
        set_state(context, "admin_tariff_add_price", title=text)
        conn.close()
        await update.message.reply_text("Р’РІРµРґРёС‚Рµ С†РµРЅСѓ (РЅР°РїСЂРёРјРµСЂ 8 РёР»Рё 8.5):")
        return

    if name == "admin_tariff_add_price":
        title = state["data"].get("title")
        if not title:
            conn.close()
            clear_state(context)
            await update.message.reply_text("РќР°Р·РІР°РЅРёРµ РЅРµ РЅР°Р№РґРµРЅРѕ. РќР°С‡РЅРёС‚Рµ РґРѕР±Р°РІР»РµРЅРёРµ С‚Р°СЂРёС„Р° Р·Р°РЅРѕРІРѕ.")
            return
        try:
            price = float(text.replace(",", "."))
        except ValueError:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ С†РµРЅСѓ С‡РёСЃР»РѕРј (РЅР°РїСЂРёРјРµСЂ 8 РёР»Рё 8.5).")
            return
        set_state(context, "admin_tariff_add_duration", title=title, price=price)
        conn.close()
        await update.message.reply_text("Р’РІРµРґРёС‚Рµ РґР»РёС‚РµР»СЊРЅРѕСЃС‚СЊ РІ РјРёРЅСѓС‚Р°С…:")
        return

    if name == "admin_tariff_add_duration":
        title = state["data"].get("title")
        price = float(state["data"].get("price") or 0)
        if not title:
            conn.close()
            clear_state(context)
            await update.message.reply_text("Р”Р°РЅРЅС‹Рµ С‚Р°СЂРёС„Р° РїРѕС‚РµСЂСЏРЅС‹. РќР°С‡РЅРёС‚Рµ РґРѕР±Р°РІР»РµРЅРёРµ С‚Р°СЂРёС„Р° Р·Р°РЅРѕРІРѕ.")
            return
        try:
            duration = int(text)
        except ValueError:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ РґР»РёС‚РµР»СЊРЅРѕСЃС‚СЊ С‡РёСЃР»РѕРј (РІ РјРёРЅСѓС‚Р°С…).")
            return
        conn.execute(
            "INSERT INTO tariffs (name, price, duration_min, priority) VALUES (?, ?, ?, 0)",
            (title, price, duration),
        )
        conn.commit()
        conn.close()
        clear_state(context)
        await update.message.reply_text("РўР°СЂРёС„ РґРѕР±Р°РІР»РµРЅ.")
        return

    if name == "admin_tariff_edit":
        tariff_id = state["data"].get("tariff_id")
        title, price, duration = parse_tariff_text(text)
        if not title:
            conn.close()
            await update.message.reply_text("Р¤РѕСЂРјР°С‚: РќР°Р·РІР°РЅРёРµ | С†РµРЅР° | РјРёРЅСѓС‚С‹")
            return
        conn.execute(
            "UPDATE tariffs SET name = ?, price = ?, duration_min = ? WHERE id = ?",
            (title, price, duration, tariff_id),
        )
        conn.commit()
        conn.close()
        clear_state(context)
        await update.message.reply_text("РўР°СЂРёС„ РѕР±РЅРѕРІР»РµРЅ.")
        return

    if name == "admin_tariff_delete":
        try:
            tariff_id = int(text)
        except ValueError:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ ID С‚Р°СЂРёС„Р°.")
            return
        conn.execute("DELETE FROM tariffs WHERE id = ?", (tariff_id,))
        conn.commit()
        conn.close()
        clear_state(context)
        await update.message.reply_text("РўР°СЂРёС„ СѓРґР°Р»РµРЅ.")
        return

    if name == "admin_department_add":
        if not text:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РїСЂРёРµРјРєРё.")
            return
        conn.execute("INSERT INTO departments (name) VALUES (?)", (text,))
        conn.commit()
        conn.close()
        clear_state(context)
        await update.message.reply_text("РџСЂРёРµРјРєР° РґРѕР±Р°РІР»РµРЅР°.")
        return

    if name == "admin_department_edit":
        dept_id = state["data"].get("department_id")
        if not text:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ РЅР°Р·РІР°РЅРёРµ.")
            return
        conn.execute("UPDATE departments SET name = ? WHERE id = ?", (text, dept_id))
        conn.commit()
        conn.close()
        clear_state(context)
        await update.message.reply_text("РџСЂРёРµРјРєР° РѕР±РЅРѕРІР»РµРЅР°.")
        return

    if name == "admin_department_delete":
        try:
            dept_id = int(text)
        except ValueError:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ ID РїСЂРёРµРјРєРё.")
            return
        conn.execute("DELETE FROM departments WHERE id = ?", (dept_id,))
        conn.commit()
        conn.close()
        clear_state(context)
        await update.message.reply_text("РџСЂРёРµРјРєР° СѓРґР°Р»РµРЅР°.")
        return

    if name == "admin_office_add":
        if not text:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РѕС„РёСЃР°.")
            return
        conn.execute("INSERT INTO offices (name) VALUES (?)", (text,))
        conn.commit()
        conn.close()
        clear_state(context)
        await update.message.reply_text("РћС„РёСЃ РґРѕР±Р°РІР»РµРЅ.")
        return

    if name == "admin_office_edit":
        office_id = state["data"].get("office_id")
        if not text:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ РЅР°Р·РІР°РЅРёРµ.")
            return
        conn.execute("UPDATE offices SET name = ? WHERE id = ?", (text, office_id))
        conn.commit()
        conn.close()
        clear_state(context)
        await update.message.reply_text("РћС„РёСЃ РѕР±РЅРѕРІР»РµРЅ.")
        return

    if name == "admin_office_delete":
        try:
            office_id = int(text)
        except ValueError:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ ID РѕС„РёСЃР°.")
            return
        conn.execute("DELETE FROM offices WHERE id = ?", (office_id,))
        conn.commit()
        conn.close()
        clear_state(context)
        await update.message.reply_text("РћС„РёСЃ СѓРґР°Р»РµРЅ.")
        return

    if name == "admin_set_priority":
        tariff_id = state["data"].get("tariff_id")
        try:
            priority = int(text)
        except ValueError:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ С‡РёСЃР»Рѕ.")
            return
        conn.execute("UPDATE tariffs SET priority = ? WHERE id = ?", (priority, tariff_id))
        conn.commit()
        conn.close()
        clear_state(context)
        await update.message.reply_text("РџСЂРёРѕСЂРёС‚РµС‚ РѕР±РЅРѕРІР»РµРЅ.")
        return

    if name == "admin_limit":
        try:
            limit = int(text)
        except ValueError:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ С‡РёСЃР»Рѕ.")
            return
        set_config(conn, "limit_per_day", str(limit))
        conn.close()
        clear_state(context)
        await update.message.reply_text("Р›РёРјРёС‚ РѕР±РЅРѕРІР»РµРЅ.")
        return

    if name == "admin_i_am_here":
        try:
            minutes = int(text)
        except ValueError:
            conn.close()
            return
        set_config(conn, "i_am_here_minutes", str(minutes))
        set_config(conn, "i_am_here_on", "1" if minutes > 0 else "0")
        conn.close()
        clear_state(context)
        if minutes > 0:
            await update.message.reply_text(f"Р¤СѓРЅРєС†РёСЏ В«РЇ С‚СѓС‚В» РІРєР»СЋС‡РµРЅР°. РРЅС‚РµСЂРІР°Р»: {minutes} РјРёРЅ.")
        else:
            await update.message.reply_text("Р¤СѓРЅРєС†РёСЏ В«РЇ С‚СѓС‚В» РІС‹РєР»СЋС‡РµРЅР°.")
        return



    if name == "admin_auto_slip":
        try:
            minutes = int(text)
        except ValueError:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ С‡РёСЃР»Рѕ РјРёРЅСѓС‚.")
            return
        set_config(conn, "auto_slip_minutes", str(minutes))
        set_config(conn, "auto_slip_on", "1" if minutes > 0 else "0")
        conn.close()
        clear_state(context)
        if minutes > 0:
            await update.message.reply_text(f"РђРІС‚Рѕ-СЃР»С‘С‚ РІРєР»СЋС‡РµРЅ. РРЅС‚РµСЂРІР°Р»: {minutes} РјРёРЅ.")
        else:
            await update.message.reply_text("РђРІС‚Рѕ-СЃР»С‘С‚ РІС‹РєР»СЋС‡РµРЅ.")
        return

    if name == "admin_lunch_text":
        if not text:
            conn.close()
            return
        set_config(conn, "lunch_text", text)
        lunch_on = get_config_bool(conn, "lunch_on")
        conn.close()
        clear_state(context)
        status = "Р’РљР›" if lunch_on else "Р’Р«РљР›"
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("вњЏ Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ С‚РµРєСЃС‚", callback_data="adm:lunch:edit")],
                [
                    InlineKeyboardButton("вњ… Р’РєР»СЋС‡РёС‚СЊ", callback_data="adm:lunch:on"),
                    InlineKeyboardButton("в›” Р’С‹РєР»СЋС‡РёС‚СЊ", callback_data="adm:lunch:off"),
                ],
                [InlineKeyboardButton("в¬… РќР°Р·Р°Рґ", callback_data="adm:settings")],
            ]
        )
        await update.message.reply_text(
            f"рџЌЅ Р Р°СЃРїРёСЃР°РЅРёРµ РѕР±РµРґРѕРІ\nРЎС‚Р°С‚СѓСЃ: {status}\n\n{text}",
            reply_markup=keyboard,
        )
        return

    if name == "admin_add_admin":
        admin_id = resolve_user_id_input(conn, text)
        if admin_id is None:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ Р®Р— (@username) РёР»Рё ID РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ.")
            return
        conn.execute("INSERT INTO admins (user_id) VALUES (?) ON CONFLICT(user_id) DO NOTHING", (admin_id,))
        conn.commit()
        conn.close()
        log_admin_action(update.effective_user.id, update.effective_user.username, "add_admin", f"target_id={admin_id}")
        clear_state(context)
        await update.message.reply_text("РђРґРјРёРЅ РґРѕР±Р°РІР»РµРЅ.")
        return

    if name == "admin_remove_admin":
        admin_id = resolve_user_id_input(conn, text)
        if admin_id is None:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ Р®Р— (@username) РёР»Рё ID РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ.")
            return
        conn.execute("DELETE FROM admins WHERE user_id = ?", (admin_id,))
        conn.commit()
        conn.close()
        log_admin_action(update.effective_user.id, update.effective_user.username, "remove_admin", f"target_id={admin_id}")
        clear_state(context)
        await update.message.reply_text("РђРґРјРёРЅ СѓРґР°Р»РµРЅ.")
        return

    if name == "admin_search_number":
        phone = "".join(extract_numbers(text))
        if not phone:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ.")
            return
        rows = conn.execute(
            "SELECT q.phone, q.status, q.created_at, q.completed_at, t.name AS tariff "
            "FROM queue_numbers q LEFT JOIN tariffs t ON q.tariff_id = t.id "
            "WHERE q.phone LIKE ? ORDER BY q.created_at DESC LIMIT 20",
            (f"%{phone}%",),
        ).fetchall()
        conn.close()
        clear_state(context)
        if not rows:
            await update.message.reply_text("РќРёС‡РµРіРѕ РЅРµ РЅР°Р№РґРµРЅРѕ.")
            return
        lines = ["рџ”Ќ Р РµР·СѓР»СЊС‚Р°С‚С‹ РїРѕРёСЃРєР°:"]
        for r in rows:
            lines.append(
                f"{r['phone']} | {status_human(r['status'])} | {r['tariff']} | {format_ts(r['created_at'])}"
            )
        await update.message.reply_text("\n".join(lines))
        return

    if name == "admin_broadcast":
        if not text and not update.message.photo:
            conn.close()
            await update.message.reply_text("РћС‚РїСЂР°РІСЊС‚Рµ С‚РµРєСЃС‚ РёР»Рё С„РѕС‚Рѕ.")
            return
        photo_id = update.message.photo[-1].file_id if update.message.photo else None
        users = conn.execute("SELECT user_id FROM users WHERE is_blocked = 0").fetchall()
        conn.close()
        sent = 0
        for u in users:
            try:
                if photo_id:
                    await context.bot.send_photo(chat_id=u["user_id"], photo=photo_id, caption=text or "")
                else:
                    await context.bot.send_message(chat_id=u["user_id"], text=text)
                sent += 1
            except Exception:
                continue
        clear_state(context)
        await update.message.reply_text(f"Р Р°СЃСЃС‹Р»РєР° Р·Р°РІРµСЂС€РµРЅР°. РћС‚РїСЂР°РІР»РµРЅРѕ: {sent}.")
        return

    if name == "support_message":
        ticket_id = state["data"].get("ticket_id")
        conn.execute(
            "INSERT INTO support_messages (ticket_id, sender_id, text, created_at) VALUES (?, ?, ?, ?)",
            (ticket_id, update.effective_user.id, text, now_ts()),
        )
        conn.commit()
        admins = conn.execute("SELECT user_id FROM admins").fetchall()
        conn.close()
        for admin in admins:
            try:
                await context.bot.send_message(
                    chat_id=admin["user_id"],
                    text=(
                        f"рџ† РќРѕРІРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ РІ РїРѕРґРґРµСЂР¶РєРµ #{ticket_id} "
                        f"РѕС‚ {format_user_label(update.effective_user.id, update.effective_user.username)}:\n{text}"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("РћС‚РІРµС‚РёС‚СЊ", callback_data=f"adm:support_reply:{ticket_id}")]]
                    ),
                )
            except Exception:
                continue
        clear_state(context)
        await update.message.reply_text("РЎРѕРѕР±С‰РµРЅРёРµ РѕС‚РїСЂР°РІР»РµРЅРѕ РІ РїРѕРґРґРµСЂР¶РєСѓ.")
        return

    if name == "admin_support_reply":
        ticket_id = state["data"].get("ticket_id")
        ticket = conn.execute(
            "SELECT user_id FROM support_tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()
        if not ticket:
            conn.close()
            clear_state(context)
            await update.message.reply_text("РўРёРєРµС‚ РЅРµ РЅР°Р№РґРµРЅ.")
            return
        conn.execute(
            "INSERT INTO support_messages (ticket_id, sender_id, text, created_at) VALUES (?, ?, ?, ?)",
            (ticket_id, update.effective_user.id, text, now_ts()),
        )
        conn.commit()
        conn.close()
        try:
            await context.bot.send_message(
                chat_id=ticket["user_id"],
                text=f"РћС‚РІРµС‚ РїРѕРґРґРµСЂР¶РєРё #{ticket_id}:\n{text}",
            )
        except Exception:
            pass
        clear_state(context)
        await update.message.reply_text("РћС‚РІРµС‚ РѕС‚РїСЂР°РІР»РµРЅ.")
        return

    if name == "user_withdraw":
        try:
            amount = float(text.replace(",", "."))
        except ValueError:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ СЃСѓРјРјСѓ.")
            return
        balance = calculate_user_balance(conn, update.effective_user.id)
        if amount <= 0 or amount > balance:
            conn.close()
            await update.message.reply_text(f"РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ СЃСЂРµРґСЃС‚РІ. Р”РѕСЃС‚СѓРїРЅРѕ: ${balance:.2f}")
            return
        conn.execute(
            "INSERT INTO withdrawal_requests (user_id, amount, status, created_at) "
            "VALUES (?, ?, 'pending', ?)",
            (update.effective_user.id, amount, now_ts()),
        )
        req_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        conn.commit()
        admins = conn.execute("SELECT user_id FROM admins").fetchall()
        conn.close()
        for admin in admins:
            try:
                await context.bot.send_message(
                    chat_id=admin["user_id"],
                    text=(
                        "рџ’° РќРѕРІС‹Р№ Р·Р°РїСЂРѕСЃ РІС‹РІРѕРґР°:\n"
                        f"{format_user_label(update.effective_user.id, update.effective_user.username)}\n"
                        f"РЎСѓРјРјР°: ${amount:.2f}"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton(f"вњ… РћРїР»Р°С‡РµРЅРѕ #{req_id}", callback_data=f"adm:withdraw:pay:{req_id}")],
                            [InlineKeyboardButton(f"вќЊ РћС€РёР±РєР° #{req_id}", callback_data=f"adm:withdraw:error:{req_id}")],
                        ]
                    ),
                )
            except Exception:
                continue
        clear_state(context)
        await update.message.reply_text("Р—Р°РїСЂРѕСЃ РЅР° РІС‹РІРѕРґ РѕС‚РїСЂР°РІР»РµРЅ.")
        return

    if name == "admin_payout_user":
        user_id = resolve_user_id_input(conn, text)
        if user_id is None:
            conn.close()
            await update.message.reply_text("РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ РЅР°Р№РґРµРЅ. Р’РІРµРґРёС‚Рµ @username РёР»Рё ID.")
            return
        row = conn.execute("SELECT username FROM users WHERE user_id = ?", (user_id,)).fetchone()
        label = format_user_label(user_id, row["username"] if row else None)
        set_state(context, "admin_payout_amount", user_id=user_id)
        conn.close()
        await update.message.reply_text(f"Р’РІРµРґРёС‚Рµ СЃСѓРјРјСѓ РІС‹РїР»Р°С‚С‹ РґР»СЏ {label}:")
        return

    if name == "admin_payout_amount":
        user_id = state["data"].get("user_id")
        if not user_id:
            conn.close()
            clear_state(context)
            await update.message.reply_text("РќРµ РЅР°Р№РґРµРЅ РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ. РќР°С‡РЅРёС‚Рµ Р·Р°РЅРѕРІРѕ.")
            return
        try:
            amount = float(text.replace(",", "."))
        except ValueError:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ СЃСѓРјРјСѓ С‡РёСЃР»РѕРј (РЅР°РїСЂРёРјРµСЂ 110 РёР»Рё 110.5).")
            return
        if amount <= 0:
            conn.close()
            await update.message.reply_text("РЎСѓРјРјР° РґРѕР»Р¶РЅР° Р±С‹С‚СЊ Р±РѕР»СЊС€Рµ РЅСѓР»СЏ.")
            return
        row = conn.execute("SELECT username FROM users WHERE user_id = ?", (user_id,)).fetchone()
        conn.execute(
            "INSERT INTO payouts (user_id, amount, note, created_at) VALUES (?, ?, ?, ?)",
            (user_id, amount, "", now_ts()),
        )
        conn.commit()
        conn.close()
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"рџ’ё Р’Р°Рј РЅР°С‡РёСЃР»РµРЅР° РІС‹РїР»Р°С‚Р°: ${amount:.2f}",
            )
        except Exception:
            pass
        clear_state(context)
        label = format_user_label(user_id, row["username"] if row else None)
        await update.message.reply_text(f"Р’С‹РїР»Р°С‚Р° РѕС‚РїСЂР°РІР»РµРЅР°: {label} РЅР° ${amount:.2f}.")
        return


    if name == "mainmenu_text":
        set_config(conn, "main_menu_text", text)
        conn.close()
        clear_state(context)
        await update.message.reply_text("РўРµРєСЃС‚ РіР»Р°РІРЅРѕРіРѕ РјРµРЅСЋ РѕР±РЅРѕРІР»РµРЅ.")
        return

    if name == "mainmenu_photo":
        if not update.message.photo:
            conn.close()
            await update.message.reply_text("РћС‚РїСЂР°РІСЊС‚Рµ С„РѕС‚Рѕ.")
            return
        photo_id = update.message.photo[-1].file_id
        set_config(conn, "main_menu_photo_id", photo_id)
        conn.close()
        clear_state(context)
        await update.message.reply_text("Р¤РѕС‚Рѕ РіР»Р°РІРЅРѕРіРѕ РјРµРЅСЋ РѕР±РЅРѕРІР»РµРЅРѕ.")
        return

    if name == "mainmenu_btn":
        key = state["data"].get("key")
        if key:
            set_config(conn, key, text)
        conn.close()
        clear_state(context)
        await update.message.reply_text("РљРЅРѕРїРєР° РѕР±РЅРѕРІР»РµРЅР°.")
        return

    if name == "admin_report_date":
        try:
            dt = datetime.strptime(text, "%d.%m.%Y")
        except ValueError:
            conn.close()
            await update.message.reply_text("Неверный формат. Пример: 04.02.2026")
            return
        tz = get_kz_tz() if "get_kz_tz" in globals() else None
        if tz:
            dt = dt.replace(tzinfo=tz)
        start_ts = int(dt.timestamp())
        end_ts = int((dt + timedelta(days=1)).timestamp())
        rows = conn.execute(
            "SELECT COUNT(*) AS cnt FROM queue_numbers WHERE completed_at BETWEEN ? AND ? AND status IN ('success','slip','error','canceled')",
            (start_ts, end_ts),
        ).fetchone()
        success = conn.execute(
            "SELECT COUNT(*) AS cnt FROM queue_numbers WHERE status='success' AND completed_at BETWEEN ? AND ?",
            (start_ts, end_ts),
        ).fetchone()
        slip = conn.execute(
            "SELECT COUNT(*) AS cnt FROM queue_numbers WHERE status='slip' AND completed_at BETWEEN ? AND ?",
            (start_ts, end_ts),
        ).fetchone()
        error = conn.execute(
            "SELECT COUNT(*) AS cnt FROM queue_numbers WHERE status='error' AND completed_at BETWEEN ? AND ?",
            (start_ts, end_ts),
        ).fetchone()
        conn.close()
        clear_state(context)
        await update.message.reply_text(
            f"Отчёт за {text}\n"
            f"Сдано: {rows['cnt']}\n"
            f"Встал: {success['cnt']} | Слет: {slip['cnt']} | Ошибки: {error['cnt']}"
        )
        return

    if name == "admin_user_search":
        user_id = resolve_user_id_input(conn, text)
        if user_id is None:
            conn.close()
            await update.message.reply_text("Р’РІРµРґРёС‚Рµ РєРѕСЂСЂРµРєС‚РЅС‹Р№ Р®Р— (@username) РёР»Рё ID.")
            return
        user = conn.execute(
            "SELECT user_id, username, last_seen, is_approved FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        conn.close()
        clear_state(context)
        if not user:
            await update.message.reply_text("РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ РЅР°Р№РґРµРЅ.")
            return
        await update.message.reply_text(
            f"{format_user_label(user['user_id'], user['username'])}\n"
            f"РђРєС‚РёРІРЅРѕСЃС‚СЊ: {format_ts(user['last_seen'])}\n"
            f"РћРґРѕР±СЂРµРЅ: {'РґР°' if user['is_approved'] else 'РЅРµС‚'}"
        )
        return

    conn.close()




