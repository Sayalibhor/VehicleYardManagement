from app import create_app
from models import db
from sqlalchemy import inspect, text


app = create_app()


def migrate_vehicle_entry_vin():

    print("\n" + "=" * 70)
    print("VEHICLE ENTRY VIN MIGRATION")
    print("=" * 70)

    with app.app_context():

        inspector = inspect(db.engine)

        # ---------------------------------------------------------
        # CHECK TABLES
        # ---------------------------------------------------------

        tables = inspector.get_table_names()

        print("\nExisting tables:")
        for table in tables:
            print(" -", table)

        # ---------------------------------------------------------
        # CASE 1:
        # Migration was already started and old table exists
        # ---------------------------------------------------------

        if "vehicle_entries_old" in tables:

            print("\nFound: vehicle_entries_old")

            old_columns = inspector.get_columns(
                "vehicle_entries_old"
            )

            print("\nOld table columns:")
            for column in old_columns:
                print(
                    f" - {column['name']} "
                    f"(nullable={column['nullable']})"
                )

            # -----------------------------------------------------
            # REMOVE LEFTOVER INDEXES FROM OLD TABLE
            # -----------------------------------------------------

            print("\nRemoving old vehicle_entries indexes...")

            with db.engine.begin() as conn:

                old_indexes = conn.execute(
                    text(
                        """
                        SELECT name
                        FROM sqlite_master
                        WHERE type = 'index'
                        AND tbl_name = 'vehicle_entries_old'
                        """
                    )
                ).fetchall()

                for row in old_indexes:

                    index_name = row[0]

                    if index_name:

                        print(
                            "Dropping old index:",
                            index_name
                        )

                        conn.execute(
                            text(
                                f'DROP INDEX IF EXISTS "{index_name}"'
                            )
                        )

            # Refresh inspector
            inspector = inspect(db.engine)

        # ---------------------------------------------------------
        # CASE 2:
        # vehicle_entries already exists
        # ---------------------------------------------------------

        if "vehicle_entries" in inspector.get_table_names():

            current_columns = inspector.get_columns(
                "vehicle_entries"
            )

            vin_column = next(
                (
                    c
                    for c in current_columns
                    if c["name"] == "vin"
                ),
                None
            )

            if vin_column:

                print(
                    "\nCurrent VIN nullable:",
                    vin_column["nullable"]
                )

                if vin_column["nullable"]:

                    print(
                        "\nVIN is already nullable."
                    )

                    print(
                        "Migration already completed."
                    )

                    print("=" * 70)

                    return

        # ---------------------------------------------------------
        # CREATE NEW TABLE
        # ---------------------------------------------------------

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if "vehicle_entries" not in tables:

            print(
                "\nCreating new vehicle_entries table..."
            )

            # Remove any leftover index with the same name
            with db.engine.begin() as conn:

                conn.execute(
                    text(
                        """
                        DROP INDEX IF EXISTS
                        ix_vehicle_entries_rfid_tag
                        """
                    )
                )

                conn.execute(
                    text(
                        """
                        DROP INDEX IF EXISTS
                        ix_vehicle_entries_vehicle_id
                        """
                    )
                )

                conn.execute(
                    text(
                        """
                        DROP INDEX IF EXISTS
                        ix_vehicle_entries_vin
                        """
                    )
                )

            # -----------------------------------------------------
            # IMPORTANT
            #
            # models.py MUST already have:
            #
            # vin = db.Column(
            #     db.String(17),
            #     nullable=True,
            #     index=True
            # )
            # -----------------------------------------------------

            db.create_all()

            print(
                "New vehicle_entries table created."
            )

        # ---------------------------------------------------------
        # COPY OLD DATA
        # ---------------------------------------------------------

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if "vehicle_entries_old" not in tables:

            print(
                "\nNo vehicle_entries_old table found."
            )

            print(
                "Nothing to copy."
            )

            print("=" * 70)

            return

        print(
            "\nCopying existing VehicleEntry records..."
        )

        old_columns = inspector.get_columns(
            "vehicle_entries_old"
        )

        new_columns = inspector.get_columns(
            "vehicle_entries"
        )

        old_column_names = {
            column["name"]
            for column in old_columns
        }

        new_column_names = {
            column["name"]
            for column in new_columns
        }

        common_columns = [
            name
            for name in [
                "entry_id",
                "vehicle_id",
                "rfid_tag",
                "vin",
                "vehicle_class",
                "driver_id",
                "driver_name",
                "license_number",
                "parking_area_id",
                "entry_source",
                "entry_time",
                "notes"
            ]
            if name in old_column_names
            and name in new_column_names
        ]

        print(
            "\nColumns being copied:"
        )

        for column in common_columns:
            print(" -", column)

        if not common_columns:

            raise RuntimeError(
                "No common columns found between old "
                "and new vehicle_entries tables."
            )

        column_list = ", ".join(
            f'"{column}"'
            for column in common_columns
        )

        print(
            "\nInserting old records into new table..."
        )

        with db.engine.begin() as conn:

            conn.execute(
                text(
                    f"""
                    INSERT INTO vehicle_entries
                    ({column_list})
                    SELECT
                    {column_list}
                    FROM vehicle_entries_old
                    """
                )
            )

            print(
                "Existing records copied successfully."
            )

            # -----------------------------------------------------
            # DROP OLD TABLE
            # -----------------------------------------------------

            print(
                "\nRemoving old vehicle_entries_old table..."
            )

            conn.execute(
                text(
                    """
                    DROP TABLE vehicle_entries_old
                    """
                )
            )

        # ---------------------------------------------------------
        # FINAL CHECK
        # ---------------------------------------------------------

        inspector = inspect(db.engine)

        final_columns = inspector.get_columns(
            "vehicle_entries"
        )

        final_vin = next(
            (
                c
                for c in final_columns
                if c["name"] == "vin"
            ),
            None
        )

        print("\n" + "=" * 70)

        if final_vin:

            print(
                "Final VIN nullable:",
                final_vin["nullable"]
            )

            if final_vin["nullable"]:

                print(
                    "\nSUCCESS!"
                )

                print(
                    "VehicleEntry VIN is now OPTIONAL."
                )

                print(
                    "Existing records were preserved."
                )

            else:

                print(
                    "\nERROR:"
                )

                print(
                    "VIN is still NOT nullable."
                )

        else:

            print(
                "\nERROR:"
            )

            print(
                "VIN column was not found."
            )

        print("=" * 70)


if __name__ == "__main__":

    migrate_vehicle_entry_vin()