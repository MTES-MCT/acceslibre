from django.db import connection


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    # https://docs.djangoproject.com/en/3.1/topics/db/sql/#executing-custom-sql-directly
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def run_sql(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return dictfetchall(cursor)
