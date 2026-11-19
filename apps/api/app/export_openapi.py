import json
from pathlib import Path

from app.main import app

CONTRACT_PATH = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "openapi.json"


def build() -> str:
    """Sorted keys and a fixed indent, so a diff means the API changed."""
    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def main() -> None:
    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(build(), encoding="utf-8")
    print(CONTRACT_PATH)


if __name__ == "__main__":
    main()
