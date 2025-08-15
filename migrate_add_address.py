# migrate_add_address.py
from sqlalchemy import text
from app import app, db

with app.app_context():
    # Detect table name (default is 'store' for SQLAlchemy models without __tablename__)
    table_name = None
    for candidate in ("store", "stores"):
        row = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
            {"n": candidate}
        ).first()
        if row:
            table_name = candidate
            break

    if not table_name:
        raise SystemExit("Table not found. Run the app once so the DB/tables are created.")

    # Add 'address' column if missing
    existing_cols = [r[1] for r in db.session.execute(text(f"PRAGMA table_info({table_name})"))]
    if "address" in existing_cols:
        print("Column 'address' already exists. Nothing to do.")
    else:
        db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN address VARCHAR(200)"))
        db.session.commit()
        print("Added 'address' column. Done.")
