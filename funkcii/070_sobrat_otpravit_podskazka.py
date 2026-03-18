def build_submit_hint(tariff_name: str, duration_min: int, price: float) -> str:
    dur = f"{duration_min} мин" if duration_min else "-"
    price_text = f"${price}" if price else "$0"
    return (
        f"Тариф: {tariff_name}\n"
        f"Длительность: {dur} | Цена: {price_text}\n\n"
        f"{SUBMIT_RULES_TEXT}"
    )
