# import json

# from .connection import get_connection

# class ChatRepository:
#     def create_project(self, thread_id: str, title: str = "New Project"):

#         conn = get_connection()
#         cursor = conn.cursor()

#         cursor.execute(
#             """
#             INSERT OR IGNORE INTO projects(thread_id, title)
#             VALUES(?, ?)
#             """,
#             (thread_id, title),
#         )

#         conn.commit()
#         conn.close()

#     def update_project_timestamp(self, thread_id: str):

#         conn = get_connection()
#         cursor = conn.cursor()

#         cursor.execute(
#             """
#             UPDATE projects
#             SET updated_at=CURRENT_TIMESTAMP
#             WHERE thread_id=?
#             """,
#             (thread_id,),
#         )

#         conn.commit()
#         conn.close()

#     def save_message(
#         self,
#         thread_id: str,
#         role: str,
#         message_type: str,
#         content: str,
#         metadata: dict | None = None,
#     ):

#         conn = get_connection()
#         cursor = conn.cursor()

#         cursor.execute(
#             """
#             INSERT INTO messages(
#                 thread_id,
#                 role,
#                 message_type,
#                 content,
#                 metadata
#             )
#             VALUES (?, ?, ?, ?, ?)
#             """,
#             (
#                 thread_id,
#                 role,
#                 message_type,
#                 content,
#                 json.dumps(metadata) if metadata else None,
#             ),
#         )

#         conn.commit()
#         conn.close()

#         self.update_project_timestamp(thread_id)

#     def get_messages(self, thread_id: str):

#         conn = get_connection()
#         cursor = conn.cursor()

#         cursor.execute(
#             """
#             SELECT *
#             FROM messages
#             WHERE thread_id=?
#             ORDER BY created_at ASC,id ASC
#             """,
#             (thread_id,),
#         )

#         rows = cursor.fetchall()

#         conn.close()

#         return [dict(row) for row in rows]

#     def list_projects(self):

#         conn = get_connection()
#         cursor = conn.cursor()

#         cursor.execute(
#             """
#             SELECT *
#             FROM projects
#             ORDER BY updated_at DESC
#             """
#         )

#         rows = cursor.fetchall()

#         conn.close()

#         return [dict(row) for row in rows]

import json

from .connection import get_connection


class ChatRepository:

    def create_project(
        self,
        thread_id: str,
        title: str = "New Project"
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO projects(thread_id, title)
            VALUES(?, ?)
            """,
            (thread_id, title),
        )

        conn.commit()
        conn.close()

    # NEW METHOD
    def update_project_title(
        self,
        thread_id: str,
        title: str
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE projects
            SET title=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE thread_id=?
            """,
            (title, thread_id),
        )

        conn.commit()
        conn.close()

    def update_project_timestamp(
        self,
        thread_id: str
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE projects
            SET updated_at=CURRENT_TIMESTAMP
            WHERE thread_id=?
            """,
            (thread_id,),
        )

        conn.commit()
        conn.close()

    def save_message(
        self,
        thread_id: str,
        role: str,
        message_type: str,
        content: str,
        metadata: dict | None = None,
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO messages(
                thread_id,
                role,
                message_type,
                content,
                metadata
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                thread_id,
                role,
                message_type,
                content,
                json.dumps(metadata) if metadata else None,
            ),
        )

        conn.commit()
        conn.close()

        self.update_project_timestamp(thread_id)

    def get_messages(
        self,
        thread_id: str
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM messages
            WHERE thread_id=?
            ORDER BY created_at ASC,id ASC
            """,
            (thread_id,),
        )

        rows = cursor.fetchall()

        conn.close()

        return [dict(row) for row in rows]

    def list_projects(self):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM projects
            ORDER BY updated_at DESC
            """
        )

        rows = cursor.fetchall()

        conn.close()

        return [dict(row) for row in rows]