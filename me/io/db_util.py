import sqlite3
from contextlib import closing
from sqlite3 import Connection, Cursor
from typing import Mapping, Collection


class SQLiteDB:

    def __init__(self, db_path='data/me.db'):
        self.db_path = db_path

    def execute(self, sql: str, params: Collection[str] or Mapping[str, str] = (),
                cursor_or_connection: Connection | Cursor | None = None) -> object:
        if cursor_or_connection is None:
            with self.connect() as conn:
                return self.execute(sql, cursor_or_connection=conn)
        if isinstance(cursor_or_connection, Connection):
            with closing(cursor_or_connection.cursor()) as curs:
                return self.execute(sql, cursor_or_connection=curs)
        if not isinstance(cursor_or_connection, Cursor):
            raise ValueError(
                f"cursor_or_connection must be of type Connection or Cursor, not {type(cursor_or_connection)}")
        cursor: Cursor = cursor_or_connection
        return cursor.execute(sql, params)

    # def query(self, sql):
    #     self.cursor.execute(sql)
    #     return self.cursor.fetchall()

    def setup(self):
        create_servers_table_sql = "CREATE TABLE IF NOT EXISTS servers(server_id INTEGER NOT NULL PRIMARY KEY)"
        create_user_table_sql = "CREATE TABLE IF NOT EXISTS users(user_id INTEGER NOT NULL PRIMARY KEY , active_server INTEGER)"
        create_permissions_table_sql = "CREATE TABLE IF NOT EXISTS permissions(server_id INTEGER NOT NULL, permission TEXT NOT NULL, owner_id INTEGER NOT NULL, owner_type TEXT NOT NULL, FOREIGN KEY(server_id) REFERENCES servers(server_id), PRIMARY KEY(server_id, server_id, permission, owner_id)) "
        create_server_settings_table_sql = "CREATE TABLE IF NOT EXISTS server_settings(server_id INTEGER NOT NULL, setting TEXT NOT NULL, setting_value TEXT, FOREIGN KEY(server_id) REFERENCES servers(server_id), PRIMARY KEY(server_id, setting))"
        create_user_settings_table_sql = "CREATE TABLE IF NOT EXISTS user_settings(server_id INTEGER NOT NULL, user_id INTEGER NOT NULL, setting TEXT NOT NULL, setting_value TEXT, FOREIGN KEY(server_id) REFERENCES servers(server_id), FOREIGN KEY(user_id) REFERENCES users(user_id), PRIMARY KEY(server_id, user_id, setting))"

        queries = [create_servers_table_sql, create_user_table_sql, create_permissions_table_sql,
                   create_server_settings_table_sql, create_user_settings_table_sql]
        for create_table_sql in queries:
            self.execute(create_table_sql)

    def connect(self) -> Connection:
        return sqlite3.connect(self.db_path)
