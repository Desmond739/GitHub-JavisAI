from pathlib import Path


class NotesAction:

    def __init__(self):

        self.notes_directory = (
            Path(__file__).resolve().parents[3] / "data" / "notes"
        )

    def read_notes(self) -> str:

        if not self.notes_directory.exists():

            return (
                "No notes directory exists yet."
            )

        note_files = list(
            self.notes_directory.glob("*.txt")
        )

        if not note_files:

            return (
                "No notes found."
            )

        notes = []

        for note_file in note_files:

            try:

                content = note_file.read_text(
                    encoding="utf-8"
                )

                notes.append(
                    f"--- {note_file.name} ---\n"
                    f"{content}"
                )

            except OSError as error:

                notes.append(
                    f"Could not read {note_file.name}: "
                    f"{type(error).__name__}"
                )

        return "\n\n".join(notes)


notes_action = NotesAction()
