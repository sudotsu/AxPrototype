"""
AxProtocol Operator Console v3.0

Visualizes the Caller -> Builder -> Critic pipeline.

"""

import streamlit as st
import json
import pandas as pd
from axp.orchestration.chain import execute_caller_only, execute_warroom
from pathlib import Path

st.set_page_config(page_title="AxProtocol Creative", layout="wide")

st.title("AxProtocol v3.0: Creative WarRoom")

# Sidebar
st.sidebar.header("Directives Active")
st.sidebar.markdown("- **D8 Strongest Take**\n- **D13 Anti-Sycophancy**\n- **D22 Immutable Ledger**")

# Main Input
objective = st.text_area("Creative Objective", height=100)

if st.button("Analyze & Optimize"):
    with st.spinner("Caller is analyzing..."):
        # Phase 1: Caller
        caller_res = execute_caller_only(objective, Path("."))
        st.session_state['caller_res'] = caller_res

# Display Caller Result & Feedback Loop
if 'caller_res' in st.session_state:

    res = st.session_state['caller_res']

    if res['status'] == "terminate":
        st.error(res['response'])

    elif res['status'] == "suggest_optimized_prompt_and_insight":
        st.info("✨ Optimized Prompt Generated")
        st.markdown(f"### {res['suggested_objective']}")

        with st.expander("🧠 View AxP Insight", expanded=True):
            insight = res['axp_insight']
            st.write(insight['verdict']['reasoning'])
            for p in insight['perspectives']:
                st.caption(f"**{p['name']}**: {p['description']}")

        user_feedback = st.text_input("Feedback (Optional 'New Oil')", placeholder="Yes, but ensure...")

        col1, col2 = st.columns(2)

        if col1.button("Confirm & Run"):
            st.session_state['run_args'] = {
                "obj": res['suggested_objective'],
                "reject": False,
                "feed": user_feedback
            }
            st.rerun()

        if col2.button("Reject & Run Best Effort"):
            st.session_state['run_args'] = {
                "obj": res['suggested_objective'],
                "reject": True,
                "feed": user_feedback
            }
            st.rerun()

# Execute WarRoom
if 'run_args' in st.session_state:
    args = st.session_state['run_args']
    with st.spinner("Builder & Critic working..."):
        final_res = execute_warroom(
            args['obj'],
            user_rejection=args['reject'],
            user_feedback=args['feed'],
            base_dir=Path(".")
        )

    # Visualize Results
    tab1, tab2, tab3 = st.tabs(["Artifact", "Critic's Review", "Chain Data"])

    with tab1:
        st.json(final_res['final_artifact'])

    with tab2:
        crit = final_res['critic_summary']
        if final_res.get('afterthought', {}).get('present'):
            st.warning(f"🧠 Afterthought: {final_res['afterthought']['message']}")
        st.write(crit)

    with tab3:
        st.write("Full Chain Registry")
        st.json(final_res)

    # Clean up state after run? Optional.



