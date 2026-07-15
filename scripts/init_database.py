from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.database import CableRepository, create_database_engine


def main() -> None:
    engine = create_database_engine()
    CableRepository(engine).create_schema()
    print(f"database_initialized: {engine.url.render_as_string(hide_password=True)}")


if __name__ == "__main__":
    main()
