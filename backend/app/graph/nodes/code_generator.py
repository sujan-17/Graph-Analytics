import re
from typing import Dict, Any, List, Optional
from langchain_core.prompts import PromptTemplate
from app.core.llm import call_gemini_llm
from app.graph.state import AnalysisState
from app.graph.agents.base import BaseAgent
from app.graph.prompts.code import CODE_GENERATOR_PROMPT

def is_col_id(col_name: str) -> bool:
    cl = col_name.lower()
    return cl.endswith("_id") or cl.endswith("id") or cl == "id" or "uuid" in cl or cl.endswith("_no") or "code" in cl

def find_entity_columns(query_text: str, all_cols: List[str]) -> List[str]:
    """
    Finds entity identifier and dimension columns matching the query.
    For example, if query mentions 'customer', matches ['customer_id', 'customer'] or ['Customer_ID', 'Customer_Name'].
    """
    q = query_text.lower()
    entity_terms = ["customer", "product", "order", "invoice", "transaction", "rep", "employee", "store", "segment", "region"]
    matched = []

    for term in entity_terms:
        if term in q:
            id_cols = [c for c in all_cols if (term in c.lower() or c.lower() in term) and is_col_id(c)]
            name_cols = [c for c in all_cols if (term in c.lower() or c.lower() in term) and not is_col_id(c)]
            for c in (id_cols + name_cols):
                if c not in matched:
                    matched.append(c)

    return matched

def build_filter_expr(col: str, val: Any) -> str:
    """
    Builds a robust Pandas filter condition supporting numeric comparisons (>10, >=2, <5, etc.),
    comparison dictionaries ({"operator": ">", "value": 10}), and case-insensitive string equality.
    """
    op = "=="
    comp_val = None

    if isinstance(val, dict):
        op = val.get("operator", "==")
        comp_val = val.get("value")
    else:
        v_str = str(val).strip()
        m = re.match(r"^([><]=?|!=|==)\s*(.+)$", v_str)
        if m:
            op = m.group(1)
            comp_val = m.group(2).strip()
        else:
            comp_val = v_str

    try:
        num = float(comp_val)
        if op in [">", ">=", "<", "<=", "!=", "=="]:
            return f"(pd.to_numeric(df[{repr(col)}], errors='coerce') {op} {num})"
    except (ValueError, TypeError):
        pass

    return f"(df[{repr(col)}].astype(str).str.lower() == {repr(str(comp_val).lower())})"


class CodeGeneratorAgent(BaseAgent):
    """
    Code Generator Agent: Synthesizes high-performance, deterministic Pandas
    data manipulation code executed against the user's dataset to satisfy
    the query plan.
    """
    name = "CodeGeneratorAgent"
    role = "Pandas & Numerical Computation Synthesis Agent"
    description = "Generates safe, efficient Pandas code targeting DataFrame df and assigning to result."

    def __init__(self):
        super().__init__(
            name="CodeGeneratorAgent",
            role="Pandas & Numerical Computation Synthesis Agent",
            description="Transforms logical plans into executable Pandas code using LangChain PromptTemplate."
        )
        self.prompt_template = PromptTemplate(
            template=CODE_GENERATOR_PROMPT,
            input_variables=["dataset_profile_summary", "analysis_plan", "user_query"]
        )

    def invoke(self, state: AnalysisState) -> Dict[str, Any]:
        user_query = state.get("user_query", "")
        profile_summary = state.get("dataset_profile_summary", "")
        plan = state.get("analysis_plan", [])
        
        generated_code = ""
        prompt_text = self.prompt_template.format(
            dataset_profile_summary=profile_summary,
            analysis_plan="\n".join(plan) if plan else "Execute Pandas analysis.",
            user_query=user_query
        )
        
        llm_output = call_gemini_llm(prompt_text, temperature=0.1, custom_api_key=state.get("gemini_api_key"))
        if llm_output:
            code_match = re.search(r"```python\s*(.*?)\s*```", llm_output, re.DOTALL)
            if code_match:
                generated_code = code_match.group(1).strip()
            elif "result =" in llm_output or "result=" in llm_output:
                generated_code = llm_output.strip()

        # Heuristic code generation fallback if LLM unavailable, rate-limited, or failed
        if not generated_code:
            profile = state.get("dataset_profile", {})
            columns = profile.get("columns", [])
            all_cols = [c["name"] for c in columns]
            
            # Categorize columns accurately
            id_cols = [c["name"] for c in columns if is_col_id(c["name"])]
            num_cols = [
                c["name"] for c in columns
                if not is_col_id(c["name"]) and any(t in c.get("data_type", "").lower() for t in ["int", "float", "double", "decimal", "numeric"])
            ]
            cat_cols = [
                c["name"] for c in columns
                if any(t in c.get("data_type", "").lower() for t in ["str", "object", "string", "category", "text"])
            ]
            
            # Check query intent or user query for matched columns
            intent = state.get("query_intent") or {}
            intent_gb = intent.get("group_by") or []
            intent_metrics = intent.get("metrics") or ([intent.get("metric")] if intent.get("metric") else [])
            intent_filters = intent.get("filters") or {}

            q_low = user_query.lower()
            is_avg = any(w in q_low for w in ["average", "avg", "mean"])
            is_count = any(w in q_low for w in ["count", "number of", "how many"])
            is_min = any(w in q_low for w in ["min", "minimum", "lowest"])
            is_max = any(w in q_low for w in ["max", "maximum", "highest"])

            if is_avg:
                agg_func = "mean"
                agg_prefix = "avg_"
            elif is_count:
                agg_func = "count"
                agg_prefix = "count_"
            elif is_min:
                agg_func = "min"
                agg_prefix = "min_"
            elif is_max:
                agg_func = "max"
                agg_prefix = "max_"
            else:
                agg_func = "sum"
                agg_prefix = "total_"

            # If filters were detected (or parse numeric comparison from query text)
            if not intent_filters:
                comp_m = re.search(r"(?:more than|greater than|>|>=)\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z_]+)", q_low)
                if not comp_m:
                    comp_m = re.search(r"([a-zA-Z_]+)\s*(?:more than|greater than|>|>=)\s*([0-9]+(?:\.[0-9]+)?)", q_low)
                if comp_m:
                    g1, g2 = comp_m.group(1), comp_m.group(2)
                    col_c = g2 if any(ch.isdigit() for ch in g1) else g1
                    num_c = g1 if any(ch.isdigit() for ch in g1) else g2
                    matched = [c for c in all_cols if col_c in c.lower() or c.lower() in col_c]
                    if matched:
                        intent_filters[matched[0]] = f">{num_c}"

            if intent_filters:
                conds = [build_filter_expr(col, val) for col, val in intent_filters.items() if col in all_cols]
                filter_expr = " & ".join(conds) if conds else "True"

                is_detail_query = any(w in q_low for w in ["detail of", "details of", "show records", "show rows", "raw data", "list of all records"])
                entity_cols = find_entity_columns(user_query, all_cols)
                id_col = next((c for c in entity_cols if is_col_id(c)), (id_cols[0] if id_cols else None))
                dim_col = next((c for c in entity_cols if not is_col_id(c)), (cat_cols[0] if cat_cols else None))
                
                # Numeric columns strictly excluding ID columns
                target_nums = [c for c in num_cols if c in intent_metrics or c.lower() in q_low]
                metric_col = target_nums[0] if target_nums else (num_cols[0] if num_cols else None)

                if not is_detail_query and (is_count or entity_cols or "customer" in q_low):
                    if id_col and dim_col and metric_col:
                        generated_code = (
                            f"sub = df[{filter_expr}]\n"
                            f"result = sub.groupby([{repr(id_col)}, {repr(dim_col)}], as_index=False)[{repr(metric_col)}].sum()"
                            f".rename(columns={{{repr(metric_col)}: 'total_quantity'}}).sort_values('total_quantity', ascending=False)"
                        )
                    elif id_col and metric_col:
                        generated_code = (
                            f"sub = df[{filter_expr}]\n"
                            f"result = sub.groupby({repr(id_col)}, as_index=False)[{repr(metric_col)}].sum()"
                            f".rename(columns={{{repr(metric_col)}: 'total_quantity'}}).sort_values('total_quantity', ascending=False)"
                        )
                    elif id_col:
                        generated_code = (
                            f"sub = df[{filter_expr}]\n"
                            f"result = pd.DataFrame([{{'Filter Condition': 'Filtered', 'Customer Count': int(sub[{repr(id_col)}].nunique()), 'Total Records': len(sub)}}])"
                        )
                    else:
                        generated_code = f"result = df[{filter_expr}].head(50)"
                elif not is_detail_query and target_nums:
                    metric_cols = target_nums
                    fixed_filter_cols = set(intent_filters.keys())
                    candidate_dims = [c for c in cat_cols if c not in fixed_filter_cols and not is_col_id(c)]

                    if candidate_dims and metric_cols:
                        primary_dim = candidate_dims[0]
                        m = metric_cols[0]
                        agg_name = f"{agg_prefix}{m}"
                        generated_code = f"result = df[{filter_expr}].groupby({repr(primary_dim)}, as_index=False)[{repr(m)}].{agg_func}().rename(columns={{{repr(m)}: {repr(agg_name)}}}).sort_values({repr(agg_name)}, ascending=False)"
                    elif metric_cols:
                        metric_dict_items = [f"{repr('Total ' + m)}: round(float(sub[{repr(m)}].{agg_func}()), 2)" for m in metric_cols]
                        filter_summary_items = [f"{repr(k)}: {repr(str(v))}" for k, v in intent_filters.items()]
                        all_dict_items = filter_summary_items + metric_dict_items
                        generated_code = f"sub = df[{filter_expr}]\nresult = pd.DataFrame([{{{', '.join(all_dict_items)}}}])"
                    else:
                        generated_code = f"result = df[{filter_expr}].head(50)"
                else:
                    generated_code = f"result = df[{filter_expr}].head(50)"
            else:
                entity_cols = find_entity_columns(user_query, all_cols)
                
                matched_cat = [c for c in all_cols if c in intent_gb]
                for c in entity_cols:
                    if c not in matched_cat:
                        matched_cat.append(c)

                matched_num = [c for c in num_cols if c in intent_metrics or c.lower() in q_low]
                target_nums = matched_num if matched_num else (num_cols[:1] if num_cols else [])

                target_cats = matched_cat if matched_cat else ([c for c in cat_cols if c.lower() in q_low] or (cat_cols[:1] if cat_cols else []))

                if target_cats and target_nums:
                    cat_repr = "[" + ", ".join(repr(c) for c in target_cats) + "]" if len(target_cats) > 1 else repr(target_cats[0])
                    m = target_nums[0]
                    agg_col_name = f"{agg_prefix}{m}"
                    
                    if len(target_nums) > 1 and not is_avg:
                        num_list = "[" + ", ".join(repr(c) for c in target_nums) + "]"
                        sort_col = target_nums[0]
                        generated_code = f"result = df.groupby({cat_repr}, as_index=False)[{num_list}].{agg_func}().sort_values({repr(sort_col)}, ascending=False)"
                    else:
                        generated_code = f"result = df.groupby({cat_repr}, as_index=False)[{repr(m)}].{agg_func}().rename(columns={{{repr(m)}: {repr(agg_col_name)}}}).sort_values({repr(agg_col_name)}, ascending=False)"
                elif target_nums:
                    m = target_nums[0]
                    label = f"Average {m}" if is_avg else f"Total {m}"
                    generated_code = f"result = pd.DataFrame([{{{repr(label)}: round(df[{repr(m)}].{agg_func}(), 2)}}])"
                elif all_cols:
                    first_col = all_cols[0]
                    generated_code = f"result = df[{repr(first_col)}].value_counts().reset_index().head(20)"
                else:
                    generated_code = "result = df.head(50)"

        return {
            "generated_code": generated_code
        }

# Agent instance for LangGraph StateGraph & backward-compatible node export
code_generator_agent = CodeGeneratorAgent()
code_generator_node = code_generator_agent
