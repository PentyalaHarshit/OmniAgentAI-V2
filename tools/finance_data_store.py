import html
import json
import re
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET


class FinanceDataStore:
    def __init__(self, data_dir: str = "finance_data"):
        self.data_dir = Path(data_dir)
        self.expenses_json = self.data_dir / "expenses.json"
        self.expenses_xlsx = self.data_dir / "expenses.xlsx"

    def ensure_ready(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.expenses_json.exists():
            self.write_json(self.expenses_json, [])
        self.export_expenses_xlsx()
        return {
            "expenses_json": str(self.expenses_json),
            "expenses_xlsx": str(self.expenses_xlsx),
        }

    def add_expense(self, category: str, amount: float, expense_date: str | None = None):
        self.ensure_ready()
        rows = self.load_expenses()
        record = {
            "date": expense_date or date.today().isoformat(),
            "category": category.title(),
            "amount": round(float(amount), 2),
        }
        rows.append(record)
        self.write_json(self.expenses_json, rows)
        self.export_expenses_xlsx()
        return record

    def load_expenses(self):
        try:
            return json.loads(self.expenses_json.read_text(encoding="utf-8"))
        except Exception:
            return []

    def monthly_summary(self):
        rows = self.load_expenses()
        total = sum(float(row.get("amount", 0)) for row in rows)
        by_category = {}
        for row in rows:
            category = row.get("category", "Other")
            by_category[category] = by_category.get(category, 0) + float(row.get("amount", 0))
        return {"total": round(total, 2), "by_category": by_category, "count": len(rows)}

    def write_json(self, path: Path, rows: list[dict]):
        path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def export_expenses_xlsx(self):
        rows = self.load_expenses()
        headers = ["date", "category", "amount"]
        table = [headers] + [[row.get(header, "") for header in headers] for row in rows]
        self.write_xlsx({"Expenses": table})

    def write_xlsx(self, sheets: dict[str, list[list]]):
        shared_strings = []
        string_index = {}
        for table in sheets.values():
            for row in table:
                for value in row:
                    value = str(value)
                    if value not in string_index:
                        string_index[value] = len(shared_strings)
                        shared_strings.append(value)

        with zipfile.ZipFile(self.expenses_xlsx, "w", zipfile.ZIP_DEFLATED) as workbook:
            workbook.writestr("[Content_Types].xml", self.content_types_xml(len(sheets)))
            workbook.writestr("_rels/.rels", self.root_rels_xml())
            workbook.writestr("xl/workbook.xml", self.workbook_xml(list(sheets.keys())))
            workbook.writestr("xl/_rels/workbook.xml.rels", self.workbook_rels_xml(len(sheets)))
            workbook.writestr("xl/sharedStrings.xml", self.shared_strings_xml(shared_strings))
            workbook.writestr("xl/styles.xml", self.styles_xml())
            for index, table in enumerate(sheets.values(), start=1):
                workbook.writestr(f"xl/worksheets/sheet{index}.xml", self.worksheet_xml(table, string_index))

    @staticmethod
    def parse_money(text: str):
        match = re.search(r"\$?\s*(\d[\d,]*(?:\.\d+)?)", text)
        return float(match.group(1).replace(",", "")) if match else 0.0

    @staticmethod
    def read_sheet_names(path: Path):
        with zipfile.ZipFile(path) as workbook:
            root = ET.fromstring(workbook.read("xl/workbook.xml"))
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        return [sheet.attrib["name"] for sheet in root.findall(".//x:sheet", ns)]

    @staticmethod
    def column_name(index: int):
        name = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            name = chr(65 + remainder) + name
        return name

    def worksheet_xml(self, rows: list[list], string_index: dict[str, int]):
        row_xml = []
        for row_number, row in enumerate(rows, start=1):
            cells = []
            for col_number, value in enumerate(row, start=1):
                cell_ref = f"{self.column_name(col_number)}{row_number}"
                cells.append(f'<c r="{cell_ref}" t="s"><v>{string_index[str(value)]}</v></c>')
            row_xml.append(f'<row r="{row_number}">{"".join(cells)}</row>')
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
            '<cols><col min="1" max="3" width="22" customWidth="1"/></cols>'
            f'<sheetData>{"".join(row_xml)}</sheetData>'
            "</worksheet>"
        )

    @staticmethod
    def shared_strings_xml(strings: list[str]):
        items = "".join(f"<si><t>{html.escape(value)}</t></si>" for value in strings)
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">{items}</sst>'
        )

    @staticmethod
    def content_types_xml(sheet_count: int):
        sheets = "".join(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for i in range(1, sheet_count + 1)
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            f"{sheets}"
            '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            "</Types>"
        )

    @staticmethod
    def root_rels_xml():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>"
        )

    @staticmethod
    def workbook_xml(sheet_names: list[str]):
        sheets = "".join(
            f'<sheet name="{html.escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
            for index, name in enumerate(sheet_names, start=1)
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f"<sheets>{sheets}</sheets>"
            "</workbook>"
        )

    @staticmethod
    def workbook_rels_xml(sheet_count: int):
        rels = []
        for index in range(1, sheet_count + 1):
            rels.append(
                f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
            )
        rels.append(
            f'<Relationship Id="rId{sheet_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
        )
        rels.append(
            f'<Relationship Id="rId{sheet_count + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{''.join(rels)}"
            "</Relationships>"
        )

    @staticmethod
    def styles_xml():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            "</styleSheet>"
        )
