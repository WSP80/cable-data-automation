from pathlib import Path
import sys

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.database import CableRepository, create_database_engine


SQL_PATH = Path("sql/power_bi_views.sql")


def main() -> None:
    engine = create_database_engine()

    if engine.dialect.name != "postgresql":
        raise RuntimeError(
            "Power BI views require PostgreSQL. Set DATABASE_URL before running."
        )

    CableRepository(engine).create_schema()
    statements = [
        statement.strip()
        for statement in SQL_PATH.read_text(encoding="utf-8").split(";")
        if statement.strip()
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

    print("power_bi_views_created:")
    print("  bi_offer_features")
    print("  bi_offer_features_history")
    print("  bi_model_runs")
    print("  bi_model_runs_history")
    print("  bi_predictions")
    print("  bi_prediction_history")


if __name__ == "__main__":
    main()
