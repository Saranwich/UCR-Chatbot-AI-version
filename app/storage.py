import csv
from datetime import datetime
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "reports.csv"
FIELDS = ["timestamp", "user_id", "location", "category", "severity", "notes"]


def save_report(user_id: str, location: str, category: str, severity: str, notes: str) -> None:
    """append เรื่องร้องเรียน 1 แถวลง CSV (mock storage แทน DB จริงไปก่อน)"""
    is_new = not CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "user_id": user_id,
            "location": location,
            "category": category,
            "severity": severity,
            "notes": notes,
        })


if __name__ == "__main__":
    save_report("U_test", location="ตลาดเก่า", category="ขยะ", severity="กลิ่นแรง", notes="ขยะตกค้าง")
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[-1]["user_id"] == "U_test"
    assert rows[-1]["category"] == "ขยะ"
    assert rows[-1]["location"] == "ตลาดเก่า"
    print("OK:", rows[-1])
