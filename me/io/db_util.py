import sqlite3
from contextlib import closing
from sqlite3 import Connection, Cursor
from typing import Mapping, Collection, List

import pandas as pd

from me.permission_types import PermType
from me.message_types import MessageType

SELECT_MESSAGES_AND_GROUPS = "SELECT m.message_id, g.channel_id, g.first_message_id, g.server_id, g.type_id, g.user_id FROM messages m JOIN message_groups g ON m.first_message_id = g.first_message_id AND m.channel_id = g.channel_id"
PRAGMA = "PRAGMA foreign_keys = 1"


class SQLiteDB:

    def __init__(self, db_path='data/me.db'):
        self.db_path = db_path

    def read_sql(self, sql: str, params: Collection[str] or Mapping[str, str] = (), debug=False) -> pd.DataFrame:
        if debug:
            print(f"Executing SQL: {sql}".replace("?", "{}").format(*params))
        with self.connect() as conn:
            df = pd.read_sql(sql, conn, params=params)
            if debug:
                print(df)
            return df

    def execute(self, sql: str, params: Collection[str] or Mapping[str, str] = (),
                cursor_or_connection: Connection | Cursor | None = None) -> object:
        if cursor_or_connection is None:
            with self.connect() as conn:
                conn.execute(PRAGMA)
                return self.execute(sql, params, cursor_or_connection=conn)
        if isinstance(cursor_or_connection, Connection):
            with closing(cursor_or_connection.cursor()) as curs:
                return self.execute(sql, params, cursor_or_connection=curs)
        if not isinstance(cursor_or_connection, Cursor):
            raise ValueError(
                f"cursor_or_connection must be of type Connection or Cursor, not {type(cursor_or_connection)}")
        cursor: Cursor = cursor_or_connection
        return cursor.execute(sql, params)

    def add_server(self, server_id: int):
        self.execute("INSERT INTO servers (server_id) VALUES (?) ON CONFLICT DO NOTHING", (server_id,))

    def add_user(self, user_id: int):
        self.execute("INSERT INTO users (user_id, active_server) VALUES (?, ?) ON CONFLICT DO NOTHING", (user_id, None))

    def update_perm_types(self):
        with self.connect() as conn:
            conn.execute(PRAGMA)
            with closing(conn.cursor()) as cursor:
                cursor.executemany(
                    "INSERT INTO permission_types (permission_id, permission_name) VALUES (?, ?) ON CONFLICT DO UPDATE SET permission_name = ?",
                    [(perm_type.value, perm_type.name, perm_type.name) for perm_type in PermType])

    def update_message_types(self):
        with self.connect() as conn:
            conn.execute(PRAGMA)
            with closing(conn.cursor()) as cursor:
                cursor.executemany(
                    "INSERT INTO message_types (type_id, type_name) VALUES (?, ?) ON CONFLICT DO UPDATE SET type_name = ?",
                    [(message_type.value, message_type.name, message_type.name) for message_type in MessageType])

    def add_messages(self, message_ids: List[int], message_type: MessageType, channel_id: int, user_id: int,
                     server_id: int):
        first_message_id = min(message_ids)
        with self.connect() as conn:
            conn.execute(PRAGMA)
            with closing(conn.cursor()) as cursor:
                message_group_sql = "INSERT INTO message_groups (first_message_id, server_id, type_id, channel_id, user_id, server_id) VALUES (?, ?, ?, ?, ?, ?)"
                message_group_params = (first_message_id, server_id, message_type.value, channel_id, user_id,
                                        server_id)
                messages_sql = "INSERT INTO messages (message_id, first_message_id, channel_id) VALUES (?, ?, ?)"
                cursor.execute(message_group_sql, message_group_params)
                cursor.executemany(messages_sql,
                                   [(message_id, first_message_id, channel_id) for message_id in message_ids])

    def delete_messages(self, first_message_id: int):
        with self.connect() as conn:
            conn.execute(PRAGMA)
            first_message_id = int(first_message_id)
            with closing(conn.cursor()) as cursor:
                cursor.execute("DELETE FROM messages WHERE first_message_id = ?", (first_message_id,))
                cursor.execute("DELETE FROM message_groups WHERE first_message_id = ?", (first_message_id,))

    def get_messages_of_type_df(self, message_type: MessageType):
        sql = f"{SELECT_MESSAGES_AND_GROUPS} WHERE g.type_id = ?"
        return self.read_sql(sql, params=(message_type,))

    def get_messages_of_type_and_user_df(self, message_type: MessageType, user_id: int, server_id: int):
        sql = f"{SELECT_MESSAGES_AND_GROUPS} WHERE g.type_id = ? AND g.user_id = ? AND g.server_id = ?"
        return self.read_sql(sql, params=(message_type, user_id, server_id))

    def setup(self):
        create_servers_table_sql = "CREATE TABLE IF NOT EXISTS servers(server_id INTEGER NOT NULL PRIMARY KEY)"
        create_permission_types_table_sql = "CREATE TABLE IF NOT EXISTS permission_types(permission_id INTEGER NOT NULL PRIMARY KEY, permission_name TEXT)"
        create_user_table_sql = "CREATE TABLE IF NOT EXISTS users(user_id INTEGER NOT NULL PRIMARY KEY , active_server INTEGER)"
        # create_permissions_table_sql = """
        # CREATE TABLE IF NOT EXISTS permissions (
        #     server_id        INTEGER not null,
        #     user_id          INTEGER not null,
        #     permission_id    INTEGER not null,
        #     permission_value integer not null,
        #     permission_cust_name       TEXT,
        #     primary key (server_id, permission_id, user_id),
        #     FOREIGN KEY(server_id)  references servers,
        #     FOREIGN KEY(user_id)    references users,
        #     FOREIGN KEY(permission_id)    references permission_types
        # )
        # """
        create_server_settings_table_sql = "CREATE TABLE IF NOT EXISTS server_settings(server_id INTEGER NOT NULL, setting TEXT NOT NULL, setting_value TEXT, FOREIGN KEY(server_id) REFERENCES servers(server_id), PRIMARY KEY(server_id, setting))"
        create_user_settings_table_sql = "CREATE TABLE IF NOT EXISTS user_settings(server_id INTEGER NOT NULL, user_id INTEGER NOT NULL, setting TEXT NOT NULL, setting_value TEXT, FOREIGN KEY(server_id) REFERENCES servers(server_id), FOREIGN KEY(user_id) REFERENCES users(user_id), PRIMARY KEY(server_id, user_id, setting))"
        create_message_types_table_sql = "CREATE TABLE IF NOT EXISTS message_types(type_id INTEGER NOT NULL PRIMARY KEY, type_name TEXT)"
        create_message_groups_table_sql = "CREATE TABLE IF NOT EXISTS message_groups(first_message_id INTEGER NOT NULL, channel_id INTEGER NOT NULL, server_id INTEGER NOT NULL,type_id INTEGER NOT NULL, user_id INTEGER NOT NULL, PRIMARY KEY(first_message_id, channel_id), FOREIGN KEY(server_id) REFERENCES servers, FOREIGN KEY(type_id) REFERENCES message_types)"
        create_messags_table_sql = "CREATE TABLE IF NOT EXISTS messages(message_id INTEGER NOT NULL, first_message_id INTEGER, channel_id INTEGER, FOREIGN KEY(first_message_id, channel_id) REFERENCES message_groups(first_message_id, channel_id), PRIMARY KEY(first_message_id, channel_id))"

        queries = [create_permission_types_table_sql, create_servers_table_sql, create_user_table_sql,
                   # create_permissions_table_sql,
                   create_server_settings_table_sql, create_user_settings_table_sql, create_message_types_table_sql,
                   create_message_groups_table_sql, create_messags_table_sql]
        for create_table_sql in queries:
            self.execute(create_table_sql)
        self.update_perm_types()
        self.update_message_types()

    def connect(self) -> Connection:
        return sqlite3.connect(self.db_path)

    def get_permission(self, server_id: str, user_id: str, permission: str):
        sql = "SELECT * FROM permissions WHERE server_id = ? AND user_id = ? AND permission_id = ?"
        df = pd.read_sql(sql, self.connect(), params=(server_id, user_id, permission))
        df["permission_value"] = df["permission_value"].astype(bool)
        return df
