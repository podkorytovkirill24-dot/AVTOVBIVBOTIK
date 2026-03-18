def is_lunch_time(conn: sqlite3.Connection) -> bool:
    # Расписание обедов теперь используется как информационная кнопка,
    # блокировки по времени нет.
    return False
