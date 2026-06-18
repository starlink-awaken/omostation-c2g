from pathlib import Path

def get_omo_dir(base_dir: Path) -> Path:
    current = base_dir.resolve()
    found: list[Path] = []
    while current != current.parent:
        if (current / ".omo").is_dir():
            found.append(current / ".omo")
        current = current.parent
    if found:
        return found[-1]
    return base_dir / ".omo"
