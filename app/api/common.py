from fastapi import HTTPException


def found(item, what: str):
    if item is None:
        raise HTTPException(status_code=404, detail=f"{what} not found")
    return item


def require_status(item: dict, allowed: set[str], action: str) -> None:
    if item["status"] not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot {action} while status is '{item['status']}' "
                   f"(needs one of: {', '.join(sorted(allowed))})",
        )
