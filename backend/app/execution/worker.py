import sys
import json
import argparse
import pandas as pd
import numpy as np

def run_worker(csv_path: str, code_path: str, output_path: str):
    try:
        # Load dataset safely into Pandas DataFrame
        df = pd.read_csv(csv_path)

        # Parse date columns if present
        for col in df.columns:
            if "date" in col.lower() or "time" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception:
                    pass

        # Read generated python code
        with open(code_path, "r", encoding="utf-8") as f:
            code_str = f.read()

        # Restricted execution globals
        local_scope = {"df": df, "pd": pd, "np": np}
        
        # Execute user/LLM generated code in restricted local namespace
        exec(code_str, local_scope, local_scope)

        # Extract result variable
        if "result" not in local_scope:
            raise ValueError("The generated code did not define a 'result' variable.")

        result = local_scope["result"]

        # Format result into JSON structure
        output_data = {}
        if isinstance(result, pd.DataFrame):
            # Limit rows to 200 for UI performance
            output_df = result.head(200).copy()
            # Convert datetime columns to string
            for c in output_df.select_dtypes(include=['datetime', 'datetime64']).columns:
                output_df[c] = output_df[c].astype(str)
            output_data = {
                "type": "dataframe",
                "columns": list(output_df.columns),
                "data": output_df.replace({np.nan: None}).to_dict(orient="records"),
                "total_rows": len(result)
            }
        elif isinstance(result, pd.Series):
            res_df = result.reset_index()
            res_df.columns = [str(c) for c in res_df.columns]
            output_data = {
                "type": "dataframe",
                "columns": list(res_df.columns),
                "data": res_df.head(200).replace({np.nan: None}).to_dict(orient="records"),
                "total_rows": len(result)
            }
        elif isinstance(result, (int, float, str, bool, np.integer, np.floating)):
            output_data = {
                "type": "scalar",
                "value": float(result) if isinstance(result, (float, np.floating)) else int(result) if isinstance(result, (int, np.integer)) else str(result)
            }
        elif isinstance(result, dict):
            output_data = {
                "type": "dict",
                "data": result
            }
        else:
            output_data = {
                "type": "string",
                "value": str(result)
            }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"status": "success", "result": output_data}, f)

    except Exception as e:
        import traceback
        err_msg = f"{type(e).__name__}: {str(e)}"
        tb = traceback.format_exc()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"status": "error", "error": err_msg, "traceback": tb}, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--code", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_worker(args.csv, args.code, args.output)
