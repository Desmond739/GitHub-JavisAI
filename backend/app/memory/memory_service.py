from pathlib import Path


class MemoryService:

    def __init__(self):

        self.base_path = Path("data/memory")

    def read_memory(self, category: str) -> str:

        category_path = self.base_path / category

        if not category_path.exists():
            return ""

        memories = []

        for file_path in sorted(category_path.iterdir()):

            if not file_path.is_file():
                continue

            try:

                content = file_path.read_text(
                    encoding="utf-8-sig"
                ).strip()

                if content:

                    memories.append(
                        f"--- {file_path.name} ---\n"
                        f"{content}"
                    )

            except (OSError, UnicodeDecodeError):

                continue

        return "\n\n".join(memories)

    def read_file(
        self,
        category: str,
        filename: str
    ) -> str:

        file_path = (
            self.base_path
            / category
            / filename
        )

        if not file_path.exists():
            return ""

        try:

            return file_path.read_text(
                encoding="utf-8-sig"
            ).strip()

        except (OSError, UnicodeDecodeError):

            return ""

    def memory_exists(
        self,
        category: str
    ) -> bool:

        category_path = self.base_path / category

        return category_path.exists()


memory_service = MemoryService()