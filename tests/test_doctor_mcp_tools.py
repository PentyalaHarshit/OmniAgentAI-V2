import sqlite3

from tools.doctor_mcp_tools import DoctorDirectoryStore, DoctorMCPToolRunner


def test_doctor_directory_creates_excel_and_sqlite(tmp_path):
    store = DoctorDirectoryStore(
        excel_path=str(tmp_path / "doctors.xlsx"),
        db_path=str(tmp_path / "doctors.sqlite"),
    )

    paths = store.ensure_ready()

    assert paths["excel_path"].endswith("doctors.xlsx")
    assert paths["db_path"].endswith("doctors.sqlite")
    assert (tmp_path / "doctors.xlsx").exists()
    assert (tmp_path / "doctors.sqlite").exists()

    with sqlite3.connect(tmp_path / "doctors.sqlite") as conn:
        doctor_name = conn.execute(
            "SELECT doctor_name FROM doctors WHERE specialty = ?",
            ("General Physician",),
        ).fetchone()[0]

    assert doctor_name == "Dr. Sarah Johnson"


def test_doctor_mcp_runner_gets_doctor_from_db(tmp_path):
    store = DoctorDirectoryStore(
        excel_path=str(tmp_path / "doctors.xlsx"),
        db_path=str(tmp_path / "doctors.sqlite"),
    )
    runner = DoctorMCPToolRunner(store=store)

    result = runner.run("General Physician")

    assert result["tool_used"] == "doctor_database_lookup"
    assert result["doctor"]["doctor_name"] == "Dr. Sarah Johnson"
    assert result["doctor"]["hospital"] == "CityCare Clinic"
    assert result["doctor"]["city"] == "Dallas"
    assert result["doctor"]["available_days"] == "Mon-Fri"
    assert result["doctor"]["available_hours"] == "09:00 AM - 05:00 PM"
    assert result["all_results"][0]["source"] == "sqlite_db_synced_from_excel"
