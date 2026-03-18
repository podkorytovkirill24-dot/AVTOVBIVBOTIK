def merge_status_text(existing: str, status_line: str, keep_success: bool = False) -> str:
    lines = (existing or "").splitlines()
    cleaned: List[str] = []
    for ln in lines:
        if ln.strip().startswith("Статус:"):
            if keep_success and ("Встал" in ln or "✅" in ln):
                cleaned.append(ln)
            continue
        cleaned.append(ln)
    lines = cleaned
    lines.append(f"Статус: {status_line}")
    return "\n".join([ln for ln in lines if ln]).strip()
