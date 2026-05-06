from io import StringIO


class StdoutSpy(StringIO):
    def __init__(self, initial_value: str | None = "", newline: str | None = "\n") -> None:
        self.output: list[str] = []
        super().__init__(initial_value, newline)

    def write(self, s):
        self.output.append(s)
        return super().write(s)

    def writelines(self, lines):
        self.output += lines
        return super().writelines(lines)
