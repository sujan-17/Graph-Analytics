import sys
import re
import json
import argparse
import pandas as pd
import numpy as np

def run_worker(csv_path: str, code_path: str, output_path: str):
    try:
        # Load dataset safely into Pandas DataFrame
        df = pd.read_csv(csv_path)

        # Parse genuine date/time columns if present
        date_pattern = re.compile(r"(^|[_\s])(date|time|timestamp|datetime)($|[_\s])", re.IGNORECASE)
        for col in df.columns:
            if date_pattern.search(str(col)):
                try:
                    converted = pd.to_datetime(df[col], errors='coerce')
                    if converted.notna().sum() > 0:
                        df[col] = converted
                except Exception:
                    pass

        # Read generated python code
        with open(code_path, "r", encoding="utf-8") as f:
            code_str = f.read()

        def safe_import(name, *args, **kwargs):
            base_name = name.split(".")[0]
            if base_name in ["pandas", "numpy", "datetime", "math", "re", "json", "dateutil"]:
                return __import__(name, *args, **kwargs)
            raise ImportError(f"Import of module '{name}' is restricted in sandbox.")

        # Whitelist of safe builtins to prevent arbitrary execution
        safe_builtins = {
            "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
            "enumerate": enumerate, "filter": filter, "float": float, "format": format,
            "int": int, "isinstance": isinstance, "issubclass": issubclass, "len": len,
            "list": list, "map": map, "max": max, "min": min, "pow": pow,
            "print": print, "range": range, "reversed": reversed, "round": round,
            "set": set, "slice": slice, "sorted": sorted, "str": str, "sum": sum,
            "tuple": tuple, "type": type, "zip": zip, "True": True, "False": False, "None": None,
            "__import__": safe_import
        }

        # Restricted execution globals
        local_scope = {"__builtins__": safe_builtins, "df": df, "pd": pd, "np": np}
        
        # Execute user/LLM generated code in restricted local namespace
        exec(code_str, local_scope, local_scope)

        # Extract result variable
        if "result" not in local_scope:
            raise ValueError("The generated code did not define a 'result' variable.")

        result = local_scope["result"]

        # Format result into JSON structure
        output_data = {}
        if isinstance(result, pd.Series):
            result = result.reset_index()

        if isinstance(result, pd.DataFrame):
            # If the index is a MultiIndex or has an explicit name (e.g. from groupby without as_index=False, or pivot),
            # reset index so grouped dimension columns are included in to_dict(orient="records").
            # Otherwise, if it's an ordinary filter/slice with an unnamed Index, reset with drop=True so no artificial 'index' column is added.
            if isinstance(result.index, pd.MultiIndex) or (result.index.name is not None and str(result.index.name).strip() != ""):
                result = result.reset_index()
            elif not isinstance(result.index, pd.RangeIndex):
                result = result.reset_index(drop=True)

            # If an 'index' column was somehow created from unnamed index reset, drop it if it's just 0..N
            if 'index' in result.columns and len(result.columns) > 1:
                col_vals = list(result['index'])
                if col_vals == list(range(len(result))):
                    result = result.drop(columns=['index'])

            # Flatten MultiIndex columns if present (e.g., from .agg(['sum', 'mean']))
            if isinstance(result.columns, pd.MultiIndex):
                result.columns = [
                    "_".join(str(lvl) for lvl in col if str(lvl) and not str(lvl).startswith("Unnamed")).strip("_")
                    for col in result.columns.values
                ]
            else:
                result.columns = [str(c) for c in result.columns]

            # Limit rows to 200 for UI performance
            output_df = result.head(200).copy()
            # Convert all datetime/timestamp columns and object values to strings
            for c in output_df.columns:
                if pd.api.types.is_datetime64_any_dtype(output_df[c]):
                    output_df[c] = output_df[c].astype(str)
                elif output_df[c].dtype == object:
                    output_df[c] = output_df[c].apply(
                        lambda x: str(x) if isinstance(x, (pd.Timestamp, np.datetime64)) else x
                    )

            output_data = {
                "type": "dataframe",
                "columns": list(output_df.columns),
                "data": output_df.replace({np.nan: None}).to_dict(orient="records"),
                "total_rows": len(result)
            }
        elif isinstance(result, (list, tuple, np.ndarray, pd.Index)):
            res_list = list(result)
            col_name = "Value"
            output_data = {
                "type": "dataframe",
                "columns": [col_name],
                "data": [{col_name: str(val) if not isinstance(val, (int, float, bool)) else val} for val in res_list[:200]],
                "total_rows": len(res_list)
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
            json.dump({"status": "success", "result": output_data}, f, default=str)

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
