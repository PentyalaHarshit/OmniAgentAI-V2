import html
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET


DEFAULT_FLIGHTS = [
    {
        "trip_id": "FLT-001",
        "type": "flight",
        "provider": "American Airlines",
        "from": "Dallas",
        "to": "New York",
        "date": "2026-07-10",
        "departure_time": "08:00",
        "arrival_time": "12:15",
        "price": 220,
        "available_seats": ["12A", "12B", "14C", "15D"],
        "seats_available": 12,
    },
    {
        "trip_id": "FLT-002",
        "type": "flight",
        "provider": "Delta Airlines",
        "from": "Dallas",
        "to": "New York",
        "date": "2026-07-10",
        "departure_time": "14:30",
        "arrival_time": "18:45",
        "price": 245,
        "available_seats": ["16A", "16B", "18C", "18D"],
        "seats_available": 8,
    },
]

DEFAULT_RAIL = [
    {
        "trip_id": "RAIL-001",
        "type": "rail",
        "provider": "Texas Express",
        "from": "Dallas",
        "to": "Austin",
        "date": "2026-07-10",
        "departure_time": "09:00",
        "arrival_time": "12:30",
        "price": 45,
        "available_seats": ["A1", "A2", "B1", "B2"],
        "seats_available": 30,
    }
]


class TravelDataStore:
    def __init__(self, data_dir: str = "travel_data"):
        self.data_dir = Path(data_dir)
        self.flight_path = self.data_dir / "live_flights.json"
        self.rail_path = self.data_dir / "live_rail.json"
        self.bookings_path = self.data_dir / "bookings.json"
        self.excel_path = self.data_dir / "travel_live_data.xlsx"

    def ensure_ready(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.flight_path.exists():
            self.write_json(self.flight_path, DEFAULT_FLIGHTS)
        if not self.rail_path.exists():
            self.write_json(self.rail_path, DEFAULT_RAIL)
        if not self.bookings_path.exists():
            self.write_json(self.bookings_path, [])
        self.export_excel()
        return {
            "flight_json": str(self.flight_path),
            "rail_json": str(self.rail_path),
            "bookings_json": str(self.bookings_path),
            "excel_path": str(self.excel_path),
        }

    def refresh_live_data(self, flights: list[dict] | None = None, rail: list[dict] | None = None):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.write_json(self.flight_path, flights or DEFAULT_FLIGHTS)
        self.write_json(self.rail_path, rail or DEFAULT_RAIL)
        if not self.bookings_path.exists():
            self.write_json(self.bookings_path, [])
        self.export_excel()
        return self.ensure_ready()

    def search(self, source: str, destination: str, date: str):
        self.ensure_ready()
        normalized_date = self.normalize_date(date)
        trips = self.load_json(self.flight_path) + self.load_json(self.rail_path)
        exact = [
            self.normalize_trip(trip)
            for trip in trips
            if self.matches_trip(trip, source, destination, normalized_date, require_date=True)
        ]
        if exact:
            return exact
        return [
            self.normalize_trip(trip)
            for trip in trips
            if self.matches_trip(trip, source, destination, normalized_date, require_date=False)
        ]

    def create_booking(
        self,
        trip: dict,
        seats: list[str],
        passenger: str = "Harshit P.",
        amount: int | None = None,
        payment_status: str = "paid",
        ticket_status: str = "generated",
        delivery_method: str = "",
        delivery_target: str = "",
    ):
        self.ensure_ready()
        bookings = self.load_json(self.bookings_path)
        booking_id = f"TRIP-{datetime.now().strftime('%Y%m%d')}-{len(bookings) + 1:03d}"
        total = amount if amount is not None else int(trip["price"]) * len(seats)
        booking = {
            "booking_id": booking_id,
            "status": "confirmed",
            "passenger_name": passenger,
            "trip_type": trip.get("type", ""),
            "from": trip.get("from", ""),
            "to": trip.get("to", ""),
            "date": trip.get("date", ""),
            "seat": ", ".join(seats),
            "amount": total,
            "payment_status": payment_status,
            "ticket_status": ticket_status,
            "delivery_method": delivery_method,
            "delivery_target": delivery_target,
            "trip": trip,
            "seats": seats,
            "total_price": total,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        bookings.append(booking)
        self.write_json(self.bookings_path, bookings)
        return booking

    def load_json(self, path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def write_json(self, path: Path, rows: list[dict]):
        path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def matches_trip(self, trip: dict, source: str, destination: str, date: str, require_date: bool):
        source_ok = self.clean_city(trip.get("from", "")) == self.clean_city(source)
        destination_ok = self.clean_city(trip.get("to", "")) == self.clean_city(destination)
        date_ok = str(trip.get("date", "")) == date
        return source_ok and destination_ok and (date_ok or not require_date)

    def normalize_trip(self, trip: dict):
        provider = trip.get("provider") or trip.get("airline") or trip.get("train_name") or "Unknown Provider"
        normalized = {
            "trip_id": trip.get("trip_id", ""),
            "type": trip.get("type", "flight"),
            "provider": provider,
            "from": trip.get("from", ""),
            "to": trip.get("to", ""),
            "date": trip.get("date", ""),
            "departure_time": trip.get("departure_time", ""),
            "arrival_time": trip.get("arrival_time", ""),
            "price": int(trip.get("price", 0)),
            "available_seats": trip.get("available_seats") or [],
            "seats_available": int(trip.get("seats_available", len(trip.get("available_seats") or []))),
        }
        normalized["duration_minutes"] = self.duration_minutes(
            normalized["departure_time"],
            normalized["arrival_time"],
        )
        return normalized

    def best_trip(self, trips: list[dict]):
        if not trips:
            return None
        return min(trips, key=lambda item: (int(item.get("price", 0)), int(item.get("duration_minutes", 99999))))

    def normalize_date(self, value: str):
        text = str(value or "").strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return text

        current_year = datetime.now().year
        candidates = [
            "%B %d %Y",
            "%b %d %Y",
            "%B %d",
            "%b %d",
            "%m/%d/%Y",
            "%m/%d",
        ]
        cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", text, flags=re.I)
        for fmt in candidates:
            try:
                parsed = datetime.strptime(cleaned, fmt)
                if "%Y" not in fmt:
                    parsed = parsed.replace(year=current_year)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return text

    @staticmethod
    def clean_city(value: str):
        return re.sub(r"\s+", " ", str(value or "").strip().lower())

    @staticmethod
    def duration_minutes(start: str, end: str):
        try:
            departure = datetime.strptime(start, "%H:%M")
            arrival = datetime.strptime(end, "%H:%M")
            minutes = int((arrival - departure).total_seconds() // 60)
            return minutes if minutes >= 0 else minutes + 24 * 60
        except ValueError:
            return 99999

    def export_excel(self):
        flights = self.load_json(self.flight_path) or DEFAULT_FLIGHTS
        rail = self.load_json(self.rail_path) or DEFAULT_RAIL
        bookings = self.load_json(self.bookings_path)
        workbook = {
            "Flights": [self.flatten_row(row) for row in flights],
            "Rail": [self.flatten_row(row) for row in rail],
            "Bookings": [self.flatten_row(row) for row in bookings],
        }
        self.write_xlsx(workbook)

    def flatten_row(self, row: dict):
        flat = {}
        for key, value in row.items():
            if isinstance(value, (list, dict)):
                flat[key] = json.dumps(value)
            else:
                flat[key] = value
        return flat

    def write_xlsx(self, sheets: dict[str, list[dict]]):
        shared_strings = []
        string_index = {}
        sheet_payloads = {}
        for sheet_name, rows in sheets.items():
            headers = sorted({key for row in rows for key in row.keys()})
            table = [headers] + [[row.get(header, "") for header in headers] for row in rows]
            sheet_payloads[sheet_name] = table
            for row in table:
                for value in row:
                    value = str(value)
                    if value not in string_index:
                        string_index[value] = len(shared_strings)
                        shared_strings.append(value)

        with zipfile.ZipFile(self.excel_path, "w", zipfile.ZIP_DEFLATED) as workbook:
            workbook.writestr("[Content_Types].xml", self.content_types_xml(len(sheet_payloads)))
            workbook.writestr("_rels/.rels", self.root_rels_xml())
            workbook.writestr("xl/workbook.xml", self.workbook_xml(list(sheet_payloads.keys())))
            workbook.writestr("xl/_rels/workbook.xml.rels", self.workbook_rels_xml(len(sheet_payloads)))
            workbook.writestr("xl/sharedStrings.xml", self.shared_strings_xml(shared_strings))
            workbook.writestr("xl/styles.xml", self.styles_xml())
            for index, table in enumerate(sheet_payloads.values(), start=1):
                workbook.writestr(
                    f"xl/worksheets/sheet{index}.xml",
                    self.worksheet_xml(table, string_index),
                )

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
                value = str(value)
                cells.append(f'<c r="{cell_ref}" t="s"><v>{string_index[value]}</v></c>')
            row_xml.append(f'<row r="{row_number}">{"".join(cells)}</row>')
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
            '<cols><col min="1" max="20" width="22" customWidth="1"/></cols>'
            f'<sheetData>{"".join(row_xml)}</sheetData>'
            "</worksheet>"
        )

    @staticmethod
    def shared_strings_xml(strings: list[str]):
        items = "".join(f"<si><t>{html.escape(value)}</t></si>" for value in strings)
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">'
            f"{items}</sst>"
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

    def read_excel_sheet_names(self):
        with zipfile.ZipFile(self.excel_path) as workbook:
            root = ET.fromstring(workbook.read("xl/workbook.xml"))
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        return [sheet.attrib["name"] for sheet in root.findall(".//x:sheet", ns)]
