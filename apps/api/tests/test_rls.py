from sqlalchemy import text


def _set_user(conn, user_id: str) -> None:
    conn.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": user_id})


def test_two_user_rls_isolation(app_engine) -> None:
    with app_engine.begin() as conn:
        user_a = conn.execute(
            text("SELECT ensure_user(:c, :e)"),
            {"c": "rls_clerk_a", "e": "rls-a@example.com"},
        ).scalar_one()
        user_b = conn.execute(
            text("SELECT ensure_user(:c, :e)"),
            {"c": "rls_clerk_b", "e": "rls-b@example.com"},
        ).scalar_one()

    with app_engine.begin() as conn:
        _set_user(conn, str(user_a))
        semester_a = conn.execute(
            text(
                """
                INSERT INTO semesters (user_id, name, start_date, end_date, is_current)
                VALUES (:uid, 'A Fall', '2026-08-01', '2026-12-15', true)
                RETURNING id
                """
            ),
            {"uid": user_a},
        ).scalar_one()
        conn.execute(
            text(
                """
                INSERT INTO subjects (user_id, semester_id, name, code)
                VALUES (:uid, :sid, 'Operating Systems', 'COOS')
                """
            ),
            {"uid": user_a, "sid": semester_a},
        )

    with app_engine.begin() as conn:
        _set_user(conn, str(user_b))
        semester_b = conn.execute(
            text(
                """
                INSERT INTO semesters (user_id, name, start_date, end_date, is_current)
                VALUES (:uid, 'B Fall', '2026-08-01', '2026-12-15', true)
                RETURNING id
                """
            ),
            {"uid": user_b},
        ).scalar_one()
        conn.execute(
            text(
                """
                INSERT INTO subjects (user_id, semester_id, name, code)
                VALUES (:uid, :sid, 'Databases', 'DBMS')
                """
            ),
            {"uid": user_b, "sid": semester_b},
        )

    with app_engine.begin() as conn:
        _set_user(conn, str(user_a))
        names = [
            row[0]
            for row in conn.execute(text("SELECT name FROM subjects ORDER BY name")).fetchall()
        ]
        assert names == ["Operating Systems"]

        unscoped = conn.execute(
            text("SELECT name FROM subjects WHERE name = 'Databases'")
        ).fetchall()
        assert unscoped == []

    with app_engine.begin() as conn:
        _set_user(conn, str(user_b))
        names = [
            row[0]
            for row in conn.execute(text("SELECT name FROM subjects ORDER BY name")).fetchall()
        ]
        assert names == ["Databases"]

    with app_engine.begin() as conn:
        conn.execute(text("SELECT set_config('app.current_user_id', '', true)"))
        rows = conn.execute(text("SELECT name FROM subjects")).fetchall()
        assert rows == []
