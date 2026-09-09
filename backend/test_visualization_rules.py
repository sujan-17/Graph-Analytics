from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.graph.nodes.visualization import should_generate_visualization

print("=== Testing should_generate_visualization rules ===")

# Test 1: Detail query without chart keyword -> should be False
state_detail = {
    "user_query": "give me the details of the person who buys the technology in the west region",
    "query_intent": {"intent": "filtering", "filters": {"Category": "Technology", "Region": "West"}}
}
cols = ["Order ID", "Customer Type", "Product", "Sales", "Profit"]
data = [
    {"Order ID": "ORD-1001", "Customer Type": "Enterprise", "Product": "Laptop", "Sales": 2500, "Profit": 500},
    {"Order ID": "ORD-1009", "Customer Type": "Consumer", "Product": "Phone", "Sales": 700, "Profit": 150}
]
res_detail = should_generate_visualization(state_detail, cols, data)
print("1. Detail query visualization allowed:", res_detail)
assert res_detail is False, "Detail query must NOT generate visualization"

# Test 2: Analytical aggregation query -> should be True
state_agg = {
    "user_query": "Sales and profit by Region and Category",
    "query_intent": {"intent": "grouping", "group_by": ["Region", "Category"], "metrics": ["Sales", "Profit"]}
}
cols_agg = ["Region", "Category", "Sales", "Profit"]
data_agg = [
    {"Region": "East", "Category": "Technology", "Sales": 5000, "Profit": 1200},
    {"Region": "West", "Category": "Technology", "Sales": 4000, "Profit": 900}
]
res_agg = should_generate_visualization(state_agg, cols_agg, data_agg)
print("2. Analytical groupby visualization allowed:", res_agg)
assert res_agg is True, "Analytical groupby query MUST generate visualization"

# Test 3: Explicit chart request on a detail query -> should be True
state_explicit = {
    "user_query": "give me a chart showing details of buyers in west region",
    "query_intent": {"intent": "filtering"}
}
res_explicit = should_generate_visualization(state_explicit, cols, data)
print("3. Explicit chart request visualization allowed:", res_explicit)
assert res_explicit is True, "Explicit chart request MUST generate visualization"

# Test 4: End-to-end API test with TestClient for "give me the details of the person who buys the technology in the west region"
print("\n=== Testing API execution for detail query ===")
client = TestClient(app)
user_id = "7029567a-16d6-4e07-9b3a-86ea5c3d4cd0"
workspace_id = "729249ca-ef88-4dbc-8ec3-f8dc544ebd20"
dataset_id = "03bb003b-beb7-47b8-b573-7ace4ad56bf0"
token = create_access_token(subject=user_id)
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

query = "give me the details of the person who buys the technology in the west region"
res = client.post(
    f"/api/workspaces/{workspace_id}/analysis",
    headers=headers,
    json={"question": query, "dataset_id": dataset_id}
)
print("API Status Code:", res.status_code)
assert res.status_code == 200, f"API failed: {res.text}"
payload = res.json()
print("Execution Status:", payload.get("execution_status"))
print("Chart Spec Present:", payload.get("chart_spec") is not None)
assert payload.get("chart_spec") is None, "Chart spec must be None for detail queries!"

table = payload.get("result_table") or []
print(f"Result rows: {len(table)}")
if table:
    print("Columns:", list(table[0].keys()))
    assert "index" not in table[0], "Unwanted 'index' column must NOT be present!"

print("\n=== ALL VISUALIZATION REQUIREMENT TESTS PASSED! ===")
