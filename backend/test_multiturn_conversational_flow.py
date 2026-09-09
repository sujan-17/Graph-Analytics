import json
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.core.database import SessionLocal
from app.models.workspace import Workspace
from app.models.dataset import Dataset

client = TestClient(app)

# Use existing user and workspace
user_id = "7029567a-16d6-4e07-9b3a-86ea5c3d4cd0"
workspace_id = "729249ca-ef88-4dbc-8ec3-f8dc544ebd20"
dataset_id = "03bb003b-beb7-47b8-b573-7ace4ad56bf0"

token = create_access_token(subject=user_id)
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("=== Starting Multi-Turn Conversational Analytics Verification ===")

# Turn 1: Broad multi-column query
q1 = "Sales and profit by Region and Category"
print(f"\n--- Turn 1: '{q1}' ---")
res1 = client.post(
    f"/api/workspaces/{workspace_id}/analysis",
    headers=headers,
    json={"question": q1, "dataset_id": dataset_id}
)
print("Turn 1 Status Code:", res1.status_code)
assert res1.status_code == 200, f"Turn 1 failed: {res1.text}"
data1 = res1.json()

conv_id = data1.get("conversation_id")
print("Turn 1 Conversation ID:", conv_id)
print("Turn 1 Execution Status:", data1.get("execution_status"))
print("Turn 1 Generated Code:\n", data1.get("generated_code"))
print("Turn 1 Result Rows:", len(data1.get("result_table") or []))
if data1.get("result_table"):
    print("Turn 1 Columns:", list(data1["result_table"][0].keys()))

assert conv_id is not None, "Conversation ID must not be None"
assert data1.get("execution_status") == "SUCCESS", f"Execution failed: {data1.get('error_message')}"

# Turn 2: Follow-up drill-down in same conversation
q2 = "Now filter that only for Enterprise customers"
print(f"\n--- Turn 2 (Follow-up Drill-Down): '{q2}' ---")
res2 = client.post(
    f"/api/workspaces/{workspace_id}/analysis",
    headers=headers,
    json={
        "question": q2,
        "dataset_id": dataset_id,
        "conversation_id": conv_id
    }
)
print("Turn 2 Status Code:", res2.status_code)
assert res2.status_code == 200, f"Turn 2 failed: {res2.text}"
data2 = res2.json()

print("Turn 2 Conversation ID:", data2.get("conversation_id"))
print("Turn 2 Execution Status:", data2.get("execution_status"))
print("Turn 2 Intent Refers to Previous:", (data2.get("intent") or {}).get("refers_to_previous"))
print("Turn 2 Intent Filters:", (data2.get("intent") or {}).get("filters"))
print("Turn 2 Intent Group By:", (data2.get("intent") or {}).get("group_by"))
print("Turn 2 Generated Code:\n", data2.get("generated_code"))
print("Turn 2 Result Rows:", len(data2.get("result_table") or []))
if data2.get("result_table"):
    print("Turn 2 Sample Row:", data2["result_table"][0])
    print("Turn 2 Columns:", list(data2["result_table"][0].keys()))

assert data2.get("conversation_id") == conv_id, "Conversation ID must persist across turns"
assert data2.get("execution_status") == "SUCCESS", f"Turn 2 failed: {data2.get('error_message')}"

# Turn 3: Verify Chronological Workspace Listing
print("\n--- Listing Workspace Analyses ---")
list_res = client.get(f"/api/workspaces/{workspace_id}/analysis", headers=headers)
assert list_res.status_code == 200
items = list_res.json()
print(f"Total analyses in workspace: {len(items)}")
if len(items) >= 2:
    print("First analysis created_at:", items[0].get("created_at"))
    print("Last analysis created_at:", items[-1].get("created_at"))
    is_asc = items[0].get("created_at") <= items[-1].get("created_at")
    print("Is chronological (past first, new second):", is_asc)
    assert is_asc, "Analyses list must be chronological"

print("\n=== All Multi-Turn Verification Checks PASSED Successfully! ===")
