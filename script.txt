                    scene = Scene(title="Сцена 1")
                    scenes.append(scene)
                explicit_frame = True
                if value:
                    lines.append(value)
        else:
            if scene is None and line.strip():
                scene = Scene(title="Сцена 1")
                scenes.append(scene)
            lines.append(line)
    flush_frame()
    if not scenes:
        raise ScriptParseError("Сценарий пуст.")
    if any(not item.frames for item in scenes):
        raise ScriptParseError("Каждая сцена должна содержать хотя бы один кадр.")
    return Script(scenes=scenes)


def _read_docx(path: Path) -> str:
    try:
        with ZipFile(path) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
        body = root.find(f"{_W}body")
        if body is None:
            raise ScriptParseError("В DOCX отсутствует основной текст.")
        paragraphs = []
        for paragraph in body.iter(f"{_W}p"):
            parts = []
            for element in paragraph.iter():
                if element.tag == f"{_W}t":
                    parts.append(element.text or "")
                elif element.tag in {f"{_W}br", f"{_W}cr"}:
                    parts.append("\n")
                elif element.tag == f"{_W}tab":
                    parts.append("\t")
            paragraphs.append("".join(parts))
        return "\n".join(paragraphs)
    except (BadZipFile, KeyError, ElementTree.ParseError) as exc:
        raise ScriptParseError("Не удалось прочитать DOCX: файл повреждён или имеет неверный формат.") from exc


def parse_script(path: str | Path) -> Script:
    """Read TXT (UTF-8, optionally BOM) or DOCX. Does not modify the input."""
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix not in {".txt", ".docx"}:
        raise ScriptParseError("Поддерживаются только файлы .txt и .docx.")
    try:
        text = source.read_text(encoding="utf-8-sig") if suffix == ".txt" else _read_docx(source)
    except UnicodeDecodeError as exc:
        raise ScriptParseError("Сохраните TXT в кодировке UTF-8.") from exc
    except OSError as exc:
        raise ScriptParseError(f"Не удалось открыть файл: {source}") from exc
    return parse_text(text)
