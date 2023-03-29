from datetime import datetime
from typing import List, Tuple

from sage.database.backends.utils import get_kind


def get_start_query(subj: str, pred: str, obj: str, table_name: str) -> Tuple[str, List[str]]:
    """Get a prepared SQL query which starts scanning for a triple pattern.

    Args:
      * subj: Subject of the triple pattern.
      * pred: Predicate of the triple pattern.
      * obj: Object of the triple pattern.
      * table_name: Name of the SQL table to scan for RDF triples.

    Returns:
      A tuple with the prepared SQL query and its parameters.
    """
    kind = get_kind(subj, pred, obj)
    query = f"SELECT * FROM {table_name} "
    if kind == 'spo':
        query += """WHERE subject = %s
                    AND predicate = %s
                    AND md5(object) = md5(%s)
                    ORDER BY subject, predicate, md5(object), insert_t, delete_t"""
        return query, (subj, pred, obj)
    elif kind == '???':
        query += "ORDER BY subject, predicate, md5(object), insert_t, delete_t"
        return query, None
    elif kind == 's??':
        query += """WHERE subject = %s
                    ORDER BY subject, predicate, md5(object), insert_t, delete_t"""
        return query, [subj]
    elif kind == 'sp?':
        query += """WHERE subject = %s
                    AND predicate = %s
                    ORDER BY subject, predicate, md5(object), insert_t, delete_t"""
        return query, (subj, pred)
    elif kind == '?p?':
        query += """WHERE predicate = %s
                    ORDER BY predicate, md5(object), subject, insert_t, delete_t"""
        return query, [pred]
    elif kind == '?po':
        query += """WHERE predicate = %s
                    AND md5(object) = md5(%s)
                    ORDER BY predicate, md5(object), subject, insert_t, delete_t"""
        return query, (pred, obj)
    elif kind == 's?o':
        query += """WHERE subject = %s
                    AND md5(object) = md5(%s)
                    ORDER BY md5(object), subject, predicate, insert_t, delete_t"""
        return query, (subj, obj)
    elif kind == '??o':
        query += """WHERE md5(object) = md5(%s)
                    ORDER BY md5(object), subject, predicate, insert_t, delete_t"""
        return query, [obj]
    else:
        raise Exception(f"Unkown pattern type: {kind}")


def get_resume_query(subj: str, pred: str, obj: str, last_read: Tuple[str, str, str, datetime, datetime], table_name: str, symbol: str = ">") -> Tuple[str, str]:
    """Get a prepared SQL query which resumes scanning for a triple pattern.

    The SQL query rely on keyset pagination to resume query processing using an optimized Index Scan.

    Args:
      * subj: Subject of the triple pattern.
      * pred: Predicate of the triple pattern.
      * obj: Object of the triple pattern.
      * last_read: The SQL row from which to resume scanning.
      * table_name: Name of the SQL table to scan for RDF triples.
      * symbol: Symbol used to perform the keyset pagination. Defaults to ">=".

    Returns:
      A tuple with the prepared SQL query and its parameters.
    """
    last_s, last_p, last_o, last_insert_t, last_delete_t = last_read
    kind = get_kind(subj, pred, obj)
    query = f"SELECT * FROM {table_name} "
    if kind == 'spo':
        return None, None
    elif kind == '???':
        query += f"""WHERE (subject, predicate, md5(object), insert_t, delete_t) {symbol} (%s, %s, md5(%s), %s, %s)
                     ORDER BY subject, predicate, md5(object), insert_t, delete_t"""
        return query, (last_s, last_p, last_o, last_insert_t, last_delete_t)
    elif kind == 's??':
        query += f"""WHERE subject = %s
                     AND (predicate, md5(object), insert_t, delete_t) {symbol} (%s, md5(%s), %s, %s)
                     ORDER BY subject, predicate, md5(object), insert_t, delete_t"""
        return query, (last_s, last_p, last_o, last_insert_t, last_delete_t)
    elif kind == 'sp?':
        query += f"""WHERE subject = %s
                     AND predicate = %s
                     AND (md5(object), insert_t, delete_t) {symbol} (md5(%s), %s, %s)
                     ORDER BY subject, predicate, md5(object), insert_t, delete_t"""
        return query, (last_s, last_p, last_o, last_insert_t, last_delete_t)
    elif kind == '?p?':
        query += f"""WHERE predicate = %s
                     AND (md5(object), subject, insert_t, delete_t) {symbol} (md5(%s), %s, %s, %s)
                     ORDER BY predicate, md5(object), subject, insert_t, delete_t"""
        return query, (last_p, last_o, last_s, last_insert_t, last_delete_t)
    elif kind == '?po':
        query += f"""WHERE predicate = %s
                     AND md5(object) = md5(%s)
                     AND (subject, insert_t, delete_t) {symbol} (%s, %s, %s)
                     ORDER BY predicate, md5(object), subject, insert_t, delete_t"""
        return query, (last_p, last_o, last_s, last_insert_t, last_delete_t)
    elif kind == 's?o':
        query += f"""WHERE subject = %s
                     AND md5(object) = md5(%s)
                     AND (predicate, insert_t, delete_t) {symbol} (%s, %s, %s)
                     ORDER BY md5(object), subject, predicate, insert_t, delete_t"""
        return query, (last_s, last_o, last_p, last_insert_t, last_delete_t)
    elif kind == '??o':
        query += f"""WHERE md5(object) = md5(%s)
                     AND (subject, predicate, insert_t, delete_t) {symbol} (%s, %s, %s, %s)
                     ORDER BY md5(object), subject, predicate, insert_t, delete_t"""
        return query, (last_o, last_s, last_p, last_insert_t, last_delete_t)
    else:
        raise Exception(f"Unkown pattern type: {kind}")


def get_insert_query(table_name: str) -> str:
    """Build a SQL query to insert a RDF triple into a MVCC-PostgreSQL table.

    Argument: Name of the SQL table in which the triple will be inserted.

    Returns: A prepared SQL query that can be executed with a tuple (subject, predicate, object).
    """
    return f"INSERT INTO {table_name} (subject, predicate, object, insert_t, delete_t) VALUES (%s, %s, %s, transaction_timestamp(), 'infinity'::timestamp) ON CONFLICT DO NOTHING"


def get_insert_many_query(table_name: str) -> str:
    """Build a SQL query to insert several RDF triples into a MVCC-PostgreSQL table.

    Argument: Name of the SQL table in which the triples will be inserted.

    Returns: A prepared SQL query that can be executed with a list of tuples (subject, predicate, object).
    """
    return f"INSERT INTO {table_name} (subject, predicate, object, insert_t, delete_t) VALUES %s ON CONFLICT DO NOTHING"


def get_delete_query(table_name: str) -> str:
    """Build a SQL query to delete a RDF triple from a MVCC-PostgreSQL table.

    Argument: Name of the SQL table from which the triple will be deleted.

    Returns: A prepared SQL query that can be executed with a tuple (subject, predicate, object).
    """
    return f"""UPDATE {table_name} SET delete_t = transaction_timestamp()
               WHERE subject = %s
               AND predicate = %s
               AND md5(object) = md5(%s)
               AND delete_t = 'infinity'::timestamp"""
