import json
from pathlib import Path
from typing import Any


class JsonRepository:
    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)

    def load_list(self, file_name: str) -> list[dict[str, Any]]:
        path = self.data_dir / file_name
        if not path.exists():
            return []

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(f"Expected {file_name} to contain a JSON array.")

        return data
