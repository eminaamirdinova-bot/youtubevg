import tempfile
from pathlib import Path
import unittest
from xml.sax.saxutils import escape
from zipfile import ZipFile

from youtubevg.services.script_parser import ScriptParseError, parse_script, parse_text


class ScriptParserTests(unittest.TestCase):
    def test_scenes_frames_and_multiline(self):
        result = parse_text("СЦЕНА: Начало\nКАДР: Один\nПродолжение\nКАДР: Два\nSCENE: End\nFRAME: Three")
        self.assertEqual([s.title for s in result.scenes], ["Начало", "End"])
        self.assertEqual([f.text for f in result.scenes[0].frames], ["Один\nПродолжение", "Два"])
        self.assertEqual(result.scenes[1].frames[0].text, "Three")

    def test_plain_text(self):
        result = parse_text("Обычный текст\nВторая строка")
        self.assertEqual(result.scenes[0].title, "Сцена 1")
        self.assertEqual(result.scenes[0].frames[0].text, "Обычный текст\nВторая строка")

    def test_empty_content_rejected(self):
        for text in ("  ", "СЦЕНА: Название", "СЦЕНА:\nтекст", "КАДР:\nКАДР: текст"):
            with self.subTest(text=text), self.assertRaises(ScriptParseError):
                parse_text(text)

    def test_txt_and_docx_match(self):
        paragraphs = ["СЦЕНА: Пример", "КАДР: Город & люди", "Продолжение", "КАДР: Финал"]
        with tempfile.TemporaryDirectory() as directory:
            txt = Path(directory) / "script.TXT"
            txt.write_text("\n".join(paragraphs), encoding="utf-8-sig")
            docx = Path(directory) / "script.docx"
            body = "".join(f"<w:p><w:r><w:t>{escape(p)}</w:t></w:r></w:p>" for p in paragraphs)
            xml = f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}</w:body></w:document>'
            with ZipFile(docx, "w") as archive:
                archive.writestr("word/document.xml", xml)
            self.assertEqual(parse_script(txt), parse_script(docx))

    def test_invalid_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            broken = root / "broken.docx"
            broken.write_bytes(b"not a docx")
            invalid = root / "invalid.txt"
            invalid.write_bytes(b"\xff")
            for path in (broken, invalid, root / "missing.txt", root / "file.pdf"):
                with self.subTest(path=path), self.assertRaises(ScriptParseError):
                    parse_script(path)


if __name__ == "__main__":
    unittest.main()
