import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.travel_data_store import TravelDataStore


if __name__ == "__main__":
    paths = TravelDataStore().refresh_live_data()
    print({
        "status": "success",
        "message": "Live travel data saved to JSON and Excel.",
        "paths": paths,
    })
