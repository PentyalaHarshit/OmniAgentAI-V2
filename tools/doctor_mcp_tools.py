import html
import sqlite3
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


DEFAULT_DOCTORS = [
    {
        "specialty": "General Physician",
        "doctor_name": "Dr. Sarah Johnson",
        "urgency": "Within 24-48 hours if symptoms worsen",
        "hospital": "CityCare Clinic",
        "city": "Dallas",
        "available_days": "Mon-Fri",
        "available_hours": "09:00 AM - 05:00 PM",
    },
    {
        "specialty": "Cardiologist / Emergency Physician",
        "doctor_name": "Dr. Emergency Care",
        "urgency": "Urgent",
        "hospital": "OmniCare Emergency",
        "city": "Dallas",
        "available_days": "Every day",
        "available_hours": "24 hours",
    },
    {
        "specialty": "General Physician",
        "doctor_name": "Dr. General Care",
        "urgency": "Routine",
        "hospital": "OmniCare Clinic",
        "city": "Dallas",
        "available_days": "Mon-Fri",
        "available_hours": "10:00 AM - 04:00 PM",
    },
    {
        "specialty": "Neurology",
        "doctor_name": "Dr. Emily Chen",
        "urgency": "Within 24-48 hours",
        "hospital": "OmniCare Neuro Center",
        "city": "Dallas",
        "available_days": "Mon-Thu",
        "available_hours": "09:30 AM - 04:30 PM",
    },
    {
        "specialty": "Endocrinology",
        "doctor_name": "Dr. Anita Rao",
        "urgency": "Routine",
        "hospital": "OmniCare Endocrine Center",
        "city": "Dallas",
        "available_days": "Tue-Fri",
        "available_hours": "10:00 AM - 05:00 PM",
    },
]


class DoctorDirectoryStore:
    def __init__(
        self,
        excel_path: str = "knowledge/healthcare/doctors.xlsx",
        db_path: str = "knowledge/healthcare/doctors.sqlite",
    ):
        self.excel_path = Path(excel_path)
        self.db_path = Path(db_path)

    def ensure_ready(self):
        self.excel_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.excel_path.exists() or self._is_legacy_excel():
            self.write_excel(DEFAULT_DOCTORS)
        self.import_excel_to_db()
        return {"excel_path": str(self.excel_path), "db_path": str(self.db_path)}

    def write_excel(self, rows: list[dict]):
        headers = ["specialty", "doctor_name", "urgency", "hospital", "city", "available_days", "available_hours"]
        sheet_rows = [headers] + [[row.get(header, "") for header in headers] for row in rows]

        shared_strings = []
        string_index = {}
        for row in sheet_rows:
            for value in row:
                value = str(value)
                if value not in string_index:
                    string_index[value] = len(shared_strings)
                    shared_strings.append(value)

        worksheet = self._worksheet_xml(sheet_rows, string_index)
        shared = self._shared_strings_xml(shared_strings)

        with zipfile.ZipFile(self.excel_path, "w", zipfile.ZIP_DEFLATED) as workbook:
            workbook.writestr("[Content_Types].xml", self._content_types_xml())
            workbook.writestr("_rels/.rels", self._root_rels_xml())
            workbook.writestr("xl/workbook.xml", self._workbook_xml())
            workbook.writestr("xl/_rels/workbook.xml.rels", self._workbook_rels_xml())
            workbook.writestr("xl/worksheets/sheet1.xml", worksheet)
            workbook.writestr("xl/sharedStrings.xml", shared)
            workbook.writestr("xl/styles.xml", self._styles_xml())

    def import_excel_to_db(self):
        rows = self.read_excel()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DROP TABLE IF EXISTS doctors")
            conn.execute(
                """
                CREATE TABLE doctors (
                    specialty TEXT NOT NULL,
                    doctor_name TEXT NOT NULL,
                    urgency TEXT NOT NULL,
                    hospital TEXT NOT NULL,
                    city TEXT NOT NULL,
                    available_days TEXT NOT NULL,
                    available_hours TEXT NOT NULL
                )
                """
            )
            conn.executemany(
                """
                INSERT INTO doctors (specialty, doctor_name, urgency, hospital, city, available_days, available_hours)
                VALUES (:specialty, :doctor_name, :urgency, :hospital, :city, :available_days, :available_hours)
                """,
                rows,
            )
            conn.commit()

    def read_excel(self):
        if not self.excel_path.exists():
            return DEFAULT_DOCTORS

        with zipfile.ZipFile(self.excel_path) as workbook:
            shared_strings = self._read_shared_strings(workbook)
            sheet_xml = workbook.read("xl/worksheets/sheet1.xml")

        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        root = ET.fromstring(sheet_xml)
        raw_rows = []
        for row in root.findall(".//x:sheetData/x:row", ns):
            values = []
            for cell in row.findall("x:c", ns):
                cell_type = cell.attrib.get("t", "")
                value_node = cell.find("x:v", ns)
                if value_node is None:
                    values.append("")
                    continue
                raw_value = value_node.text or ""
                if cell_type == "s":
                    values.append(shared_strings[int(raw_value)])
                else:
                    values.append(raw_value)
            raw_rows.append(values)

        if not raw_rows:
            return DEFAULT_DOCTORS

        headers = raw_rows[0]
        doctors = []
        for row in raw_rows[1:]:
            record = {headers[index]: row[index] if index < len(row) else "" for index in range(len(headers))}
            if record.get("doctor_name"):
                doctors.append(record)
        return doctors or DEFAULT_DOCTORS

    def find_doctor(self, specialty: str):
        self.ensure_ready()
        normalized = (specialty or "").strip().lower()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT specialty, doctor_name, urgency, hospital, city, available_days, available_hours
                FROM doctors
                WHERE lower(specialty) = ?
                ORDER BY rowid
                LIMIT 1
                """,
                (normalized,),
            ).fetchone()
            if not row and "emergency" in normalized:
                row = conn.execute(
                    """
                    SELECT specialty, doctor_name, urgency, hospital, city, available_days, available_hours
                    FROM doctors
                    WHERE lower(specialty) LIKE '%emergency%'
                    ORDER BY rowid
                    LIMIT 1
                    """
                ).fetchone()
            if not row:
                row = conn.execute(
                    """
                    SELECT specialty, doctor_name, urgency, hospital, city, available_days, available_hours
                    FROM doctors
                    WHERE lower(specialty) = 'general physician'
                    ORDER BY rowid
                    LIMIT 1
                    """
                ).fetchone()

        return dict(row) if row else DEFAULT_DOCTORS[0]

    def _is_legacy_excel(self):
        try:
            rows = self.read_excel()
        except Exception:
            return True
        if not rows:
            return True
        required = {"city", "available_days", "available_hours"}
        return not required.issubset(rows[0].keys())

    @staticmethod
    def _column_name(index: int):
        name = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            name = chr(65 + remainder) + name
        return name

    def _worksheet_xml(self, rows: list[list[str]], string_index: dict[str, int]):
        row_xml = []
        for row_number, row in enumerate(rows, start=1):
            cells = []
            for col_number, value in enumerate(row, start=1):
                cell_ref = f"{self._column_name(col_number)}{row_number}"
                cells.append(f'<c r="{cell_ref}" t="s"><v>{string_index[str(value)]}</v></c>')
            row_xml.append(f'<row r="{row_number}">{"".join(cells)}</row>')

        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
            '<cols><col min="1" max="4" width="28" customWidth="1"/></cols>'
            f'<sheetData>{"".join(row_xml)}</sheetData>'
            '<autoFilter ref="A1:D1"/>'
            "</worksheet>"
        )

    @staticmethod
    def _shared_strings_xml(strings: list[str]):
        items = "".join(f"<si><t>{html.escape(value)}</t></si>" for value in strings)
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">'
            f"{items}</sst>"
        )

    @staticmethod
    def _read_shared_strings(workbook: zipfile.ZipFile):
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
        strings = []
        for item in root.findall("x:si", ns):
            parts = [node.text or "" for node in item.findall(".//x:t", ns)]
            strings.append("".join(parts))
        return strings

    @staticmethod
    def _content_types_xml():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            "</Types>"
        )

    @staticmethod
    def _root_rels_xml():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>"
        )

    @staticmethod
    def _workbook_xml():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Doctors" sheetId="1" r:id="rId1"/></sheets>'
            "</workbook>"
        )

    @staticmethod
    def _workbook_rels_xml():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>"
        )

    @staticmethod
    def _styles_xml():
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


class DoctorDatabaseLookupTool:
    name = "doctor_database_lookup"
    description = "Looks up a doctor by specialty from the local doctor SQLite DB synced from Excel."

    def __init__(self, store: DoctorDirectoryStore | None = None):
        self.store = store or DoctorDirectoryStore()

    def run(self, specialty: str):
        doctor = self.store.find_doctor(specialty)
        paths = self.store.ensure_ready()
        return {
            "found": bool(doctor),
            "doctor": doctor,
            "source": "sqlite_db_synced_from_excel",
            "excel_path": paths["excel_path"],
            "db_path": paths["db_path"],
        }


class DoctorMCPToolRunner:
    def __init__(self, store: DoctorDirectoryStore | None = None):
        self.tool = DoctorDatabaseLookupTool(store=store)

    def run(self, specialty: str):
        result = self.tool.run(specialty)
        doctor = result.get("doctor") or {}
        return {
            "answer": (
                f"{doctor.get('doctor_name', 'Doctor not found')} "
                f"({doctor.get('specialty', specialty)})"
            ),
            "tool_used": self.tool.name,
            "doctor": doctor,
            "all_results": [result],
        }
