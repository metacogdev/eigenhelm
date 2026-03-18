def build_query(table, filters=None, fields=None, sort=None, limit=None,
                 join=None, group=None, having=None):
    """Build SQL query string. SQL injection vulnerable, string concatenation."""
    sql = "SELECT "

    if fields:
        sql += ", ".join(fields)
    else:
        sql += "*"

    sql += " FROM " + table

    if join:
        for j in join:
            jtype = j.get("type", "INNER")
            jtable = j.get("table", "")
            jon = j.get("on", "")
            sql += f" {jtype} JOIN {jtable} ON {jon}"

    if filters:
        conditions = []
        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(f"{key} = '{value}'")
            elif isinstance(value, (list, tuple)):
                vals = ", ".join(f"'{v}'" if isinstance(v, str) else str(v)
                               for v in value)
                conditions.append(f"{key} IN ({vals})")
            elif value is None:
                conditions.append(f"{key} IS NULL")
            else:
                conditions.append(f"{key} = {value}")
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

    if group:
        sql += " GROUP BY " + ", ".join(group)

    if having:
        sql += " HAVING " + having

    if sort:
        parts = []
        for s in sort:
            if isinstance(s, str):
                parts.append(s)
            elif isinstance(s, tuple):
                parts.append(f"{s[0]} {s[1]}")
        sql += " ORDER BY " + ", ".join(parts)

    if limit:
        sql += f" LIMIT {limit}"

    return sql
