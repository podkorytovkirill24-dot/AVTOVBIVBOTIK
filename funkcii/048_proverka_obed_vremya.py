def is_lunch_time(conn: sqlite3.Connection) -> bool:
    if not get_config_bool(conn, "lunch_on"):
        return False
    start_raw = get_config(conn, "lunch_start", "13:00")
    end_raw = get_config(conn, "lunch_end", "14:00")
    try:
        start_h, start_m = [int(x) for x in start_raw.split(":", 1)]
        end_h, end_m = [int(x) for x in end_raw.split(":", 1)]
    except Exception:
        return False
    tz = get_kz_tz() if "get_kz_tz" in globals() else None
    now = datetime.now(tz) if tz else datetime.now()
    start_dt = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end_dt = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    if end_dt <= start_dt:
        end_dt = end_dt + timedelta(days=1)
    return start_dt <= now <= end_dt
