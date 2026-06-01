from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Body
from sqlalchemy import inspect, text
from ..database.session import engine

router = APIRouter(prefix="/admin/api")


def _get_inspector():
    return inspect(engine)


def _get_pk_columns(table_name: str) -> list[str]:
    inspector = _get_inspector()
    pk = inspector.get_pk_constraint(table_name)
    return pk.get("constrained_columns", [])


def _validate_table(table_name: str):
    inspector = _get_inspector()
    if table_name not in inspector.get_table_names():
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")


@router.get("/tables")
async def list_tables():
    inspector = _get_inspector()
    tables = []
    for name in sorted(inspector.get_table_names()):
        with engine.connect() as conn:
            count = conn.execute(text(f"SELECT COUNT(*) FROM [{name}]")).scalar()
        tables.append({"name": name, "row_count": count})
    return {"tables": tables}


@router.get("/tables/{table_name}/schema")
async def table_schema(table_name: str):
    _validate_table(table_name)
    inspector = _get_inspector()

    columns = []
    for col in inspector.get_columns(table_name):
        columns.append({
            "name": col["name"],
            "type": str(col["type"]),
            "nullable": col.get("nullable", True),
            "default": str(col.get("default")) if col.get("default") else None,
            "primary_key": col.get("primary_key", False),
            "autoincrement": bool(col.get("autoincrement", False)),
        })

    pks = inspector.get_pk_constraint(table_name)
    fks = inspector.get_foreign_keys(table_name)

    return {"table": table_name, "columns": columns,
            "primary_keys": pks.get("constrained_columns", []), "foreign_keys": fks}


@router.get("/tables/{table_name}/rows")
async def table_rows(
    table_name: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    search: str = Query(""),
    order_by: str = Query(""),
    order_dir: str = Query("asc", pattern="^(asc|desc)$"),
):
    _validate_table(table_name)
    inspector = _get_inspector()
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    cols_joined = ", ".join(f"[{c}]" for c in columns)

    base_sql = f"SELECT {cols_joined} FROM [{table_name}]"
    count_sql = f"SELECT COUNT(*) FROM [{table_name}]"
    params = {}

    if search:
        search_clauses = " OR ".join(f"[{c}] LIKE :search" for c in columns)
        base_sql += f" WHERE ({search_clauses})"
        count_sql += f" WHERE ({search_clauses})"
        params["search"] = f"%{search}%"

    with engine.connect() as conn:
        total = conn.execute(text(count_sql), params).scalar()

    if order_by and order_by in columns:
        direction = "DESC" if order_dir == "desc" else "ASC"
        base_sql += f" ORDER BY [{order_by}] {direction}"
    else:
        pk = inspector.get_pk_constraint(table_name)
        if pk.get("constrained_columns"):
            base_sql += f" ORDER BY [{pk['constrained_columns'][0]}] DESC"

    offset = (page - 1) * per_page
    base_sql += " LIMIT :limit OFFSET :offset"
    params["limit"] = per_page
    params["offset"] = offset

    with engine.connect() as conn:
        rows = [dict(r._mapping) for r in conn.execute(text(base_sql), params)]

    return {"table": table_name, "columns": columns, "rows": rows, "total": total,
            "page": page, "per_page": per_page, "total_pages": max(1, (total + per_page - 1) // per_page)}


@router.get("/tables/{table_name}/max-id")
async def max_id(table_name: str):
    _validate_table(table_name)
    columns = [c["name"] for c in _get_inspector().get_columns(table_name)]
    id_col = next((c for c in columns if c.lower() == "id"), None)
    if not id_col:
        return {"max_id": None, "next_id": None, "message": "该表没有 id 列"}

    with engine.connect() as conn:
        row = conn.execute(text(f"SELECT MAX([{id_col}]) FROM [{table_name}]")).fetchone()
        max_val = row[0] if row and row[0] is not None else 0
    return {"max_id": max_val, "next_id": max_val + 1}


def _find_soft_delete_column(table_name: str) -> tuple[str, str] | None:
    """Find a suitable column for soft delete. Returns (column_name, delete_value)."""
    inspector = _get_inspector()
    col_names = {c["name"].lower(): c["name"] for c in inspector.get_columns(table_name)}

    if "status" in col_names:
        return (col_names["status"], "inactive")
    if "is_deleted" in col_names:
        return (col_names["is_deleted"], "1")
    if "deleted_at" in col_names:
        return (col_names["deleted_at"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return None


@router.post("/tables/{table_name}/rows")
async def insert_row(table_name: str, data: dict = Body(...)):
    _validate_table(table_name)
    inspector = _get_inspector()
    all_columns = {c["name"] for c in inspector.get_columns(table_name)}
    insert_data = {k: v for k, v in data.items() if k in all_columns}
    if not insert_data:
        raise HTTPException(status_code=400, detail="No valid columns provided")

    columns = list(insert_data.keys())
    placeholders = ", ".join(f":{c}" for c in columns)
    cols_quoted = ", ".join(f"[{c}]" for c in columns)
    sql = f"INSERT INTO [{table_name}] ({cols_quoted}) VALUES ({placeholders})"

    with engine.connect() as conn:
        result = conn.execute(text(sql), insert_data)
        conn.commit()
        try:
            last_id = result.lastrowid
        except Exception:
            last_id = None

    return {"success": True, "last_id": last_id, "message": "行已插入"}


@router.put("/tables/{table_name}/rows")
async def update_row(table_name: str, data: dict = Body(...), where: dict = Body(...)):
    _validate_table(table_name)
    pk_cols = _get_pk_columns(table_name)
    inspector = _get_inspector()
    all_columns = {c["name"] for c in inspector.get_columns(table_name)}

    where_clauses = {}
    if where:
        where_clauses = {k: v for k, v in where.items() if k in all_columns}
    if not where_clauses:
        for pk in pk_cols:
            if pk in data:
                where_clauses[pk] = data.pop(pk, None)
    if not where_clauses:
        raise HTTPException(status_code=400, detail="需要主键条件来定位要更新的行")

    set_data = {k: v for k, v in data.items() if k in all_columns}
    if not set_data:
        raise HTTPException(status_code=400, detail="没有需要更新的列")

    set_parts = ", ".join(f"[{c}] = :set_{c}" for c in set_data)
    where_parts = " AND ".join(f"[{c}] = :where_{c}" for c in where_clauses)

    params = {f"set_{k}": v for k, v in set_data.items()}
    params.update({f"where_{k}": v for k, v in where_clauses.items()})

    sql = f"UPDATE [{table_name}] SET {set_parts} WHERE {where_parts}"
    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        conn.commit()

    return {"success": True, "affected": result.rowcount, "message": f"已更新 {result.rowcount} 行"}


@router.put("/tables/{table_name}/rows/soft-delete")
async def soft_delete_row(table_name: str, where: dict = Body(...)):
    _validate_table(table_name)
    inspector = _get_inspector()
    all_columns = {c["name"] for c in inspector.get_columns(table_name)}

    where_clauses = {k: v for k, v in where.items() if k in all_columns}
    if not where_clauses:
        raise HTTPException(status_code=400, detail="需要条件来定位要停用的行")

    sd = _find_soft_delete_column(table_name)
    if not sd:
        raise HTTPException(status_code=400,
            detail="该表没有 status / is_deleted / deleted_at 列，无法软删除。请直接在数据库中处理。")

    col_name, col_value = sd
    where_parts = " AND ".join(f"[{c}] = :where_{c}" for c in where_clauses)
    params = {f"where_{k}": v for k, v in where_clauses.items()}
    params["sd_val"] = col_value

    sql = f"UPDATE [{table_name}] SET [{col_name}] = :sd_val WHERE {where_parts}"
    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        conn.commit()

    return {"success": True, "affected": result.rowcount,
            "soft_delete_column": col_name, "set_to": col_value,
            "message": f"已将 {result.rowcount} 行标记为停用（{col_name} = {col_value}）"}


def _find_enable_value(col_name: str) -> str:
    """Return the 'enabled' value for a soft-delete column."""
    if col_name == "status":
        return "active"
    if col_name == "is_deleted":
        return "0"
    if col_name == "deleted_at":
        return None
    return "active"


@router.put("/tables/{table_name}/rows/soft-enable")
async def soft_enable_row(table_name: str, where: dict = Body(...)):
    _validate_table(table_name)
    inspector = _get_inspector()
    all_columns = {c["name"] for c in inspector.get_columns(table_name)}

    where_clauses = {k: v for k, v in where.items() if k in all_columns}
    if not where_clauses:
        raise HTTPException(status_code=400, detail="需要条件来定位要启用的行")

    sd = _find_soft_delete_column(table_name)
    if not sd:
        raise HTTPException(status_code=400,
            detail="该表没有 status / is_deleted / deleted_at 列，无法启用。")

    col_name, _ = sd
    enable_value = _find_enable_value(col_name)
    where_parts = " AND ".join(f"[{c}] = :where_{c}" for c in where_clauses)
    params = {f"where_{k}": v for k, v in where_clauses.items()}

    if enable_value is None:
        sql = f"UPDATE [{table_name}] SET [{col_name}] = NULL WHERE {where_parts}"
    else:
        params["sd_val"] = enable_value
        sql = f"UPDATE [{table_name}] SET [{col_name}] = :sd_val WHERE {where_parts}"

    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        conn.commit()

    return {"success": True, "affected": result.rowcount,
            "column": col_name, "set_to": str(enable_value),
            "message": f"已启用 {result.rowcount} 行（{col_name} = {enable_value}）"}
