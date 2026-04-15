from typing import Any


def normalize_table_data(table_data: list[list[Any]] | None) -> list[list[Any]] | None:
    """Pad rows to rectangular shape and fill empty cells from merged-like patterns."""
    if not table_data:
        return table_data

    max_cols = max(len(row) for row in table_data)
    normalized: list[list[Any]] = []
    for row in table_data:
        padded = list(row) + [""] * (max_cols - len(row))
        normalized.append(padded)

    def is_empty(value: Any) -> bool:
        return value is None or str(value).strip() == ""

    for row_index in range(len(normalized)):
        last_value = None
        for col_index in range(max_cols):
            if not is_empty(normalized[row_index][col_index]):
                last_value = normalized[row_index][col_index]
            elif last_value is not None:
                normalized[row_index][col_index] = last_value

    for col_index in range(max_cols):
        last_value = None
        for row_index in range(len(normalized)):
            if not is_empty(normalized[row_index][col_index]):
                last_value = normalized[row_index][col_index]
            elif last_value is not None:
                normalized[row_index][col_index] = last_value

    return normalized


def unique_headers(headers: list[Any]) -> list[str]:
    seen: dict[str, int] = {}
    values: list[str] = []
    for header in headers:
        base = str(header).strip() if header not in (None, "") else "Column"
        if not base:
            base = "Column"
        count = seen.get(base, 0) + 1
        seen[base] = count
        values.append(base if count == 1 else f"{base}_{count}")
    return values
