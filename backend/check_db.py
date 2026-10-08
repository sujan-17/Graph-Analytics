import sqlite3
import json

conn = sqlite3.connect('graph_analytics.db')
cursor = conn.cursor()

for name, sql in cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'"):
    print(f"--- {name} ---\n{sql}\n")


print("\nWORKSPACES:")
for row in cursor.execute("SELECT id, name, user_id FROM workspaces"):
    print(row)

print("\nDATASETS:")
for row in cursor.execute("SELECT id, filename, workspace_id, row_count, column_count FROM datasets"):
    print(row)

print("\nRECENT ANALYSES:")
for row in cursor.execute("SELECT id, query, created_at, status FROM analyses ORDER BY created_at DESC LIMIT 5"):
    print(row)
