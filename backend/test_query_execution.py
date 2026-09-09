import requests
from app.core.security import create_access_token

token = create_access_token(subject="7029567a-16d6-4e07-9b3a-86ea5c3d4cd0")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

workspace_id = "729249ca-ef88-4dbc-8ec3-f8dc544ebd20"
dataset_id = "03bb003b-beb7-47b8-b573-7ace4ad56bf0"

# 1. Test chronological listing
list_res = requests.get(f"http://127.0.0.1:8000/api/workspaces/{workspace_id}/analysis", headers=headers)
print("List analyses status:", list_res.status_code)
if list_res.status_code == 200:
    items = list_res.json()
    print(f"Total analyses in workspace: {len(items)}")
    if len(items) >= 2:
        print("First analysis created_at:", items[0].get("created_at"))
        print("Last analysis created_at:", items[-1].get("created_at"))
        is_asc = items[0].get("created_at") <= items[-1].get("created_at")
        print("Is chronological (past first, new second):", is_asc)

# 2. Run multi-column combination query
query = "give me the details of the person who buys the technology in the west region"
print(f"\nSubmitting query: '{query}'...")
res = requests.post(
    f"http://127.0.0.1:8000/api/workspaces/{workspace_id}/analysis",
    headers=headers,
    json={"question": query, "dataset_id": dataset_id}
)
print("Analysis run status code:", res.status_code)
if res.status_code == 200:
    data = res.json()
    print("Execution Status:", data.get("execution_status"))
    print("Error:", data.get("error_message"))
    print("Generated code:\n", data.get("generated_code"))
    results = data.get("results")
    if results:
        print("\nResult summary:")
        print("Result JSON keys/preview:", str(results.get("result_json"))[:300])
        print("Chart JSON present:", bool(results.get("chart_json")))
        print("Insights:", results.get("insights"))
else:
    print("Error response:", res.text)
