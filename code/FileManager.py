from typing import List, Dict, Any
import json


class FileManager:
    @staticmethod
    def write_json(filepath: str, data: Any) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def read_text(filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write_text(filepath: str, content: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            print(content, file=f)
