from pathlib import Path


def test_initial_alembic_migration_exists_with_upgrade_and_downgrade() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0001_initial_schema.py"
    )

    assert migration_path.is_file()

    migration_text = migration_path.read_text(encoding="utf-8")

    assert "def upgrade() -> None:" in migration_text
    assert "def downgrade() -> None:" in migration_text
