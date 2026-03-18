def status_human(status: str) -> str:
    mapping = {
        "queued": "В очереди",
        "taken": "В работе",
        "success": "Встал",
        "slip": "Слетел",
        "error": "Ошибка",
        "canceled": "Отменён",
        "pending": "В ожидании",
        "paid": "Оплачено",
    }
    return mapping.get(status, status)
