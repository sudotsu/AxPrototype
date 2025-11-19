"""
AxProtocol Operator Console v2.5 - PRODUCTION HARDENED
======================================================
Enterprise-grade Streamlit dashboard with CRITICAL FIXES:
 FIX 1: Domains loaded from DomainConfig.json (source of truth)
 FIX 2: Formalized detector API (score_all_domains public method)
 FIX 3: AxP signature watermark in exports + sanitized filenames
 FIX 4: Token handling ready for secure session storage

Changes from v2.4:
- Fixed domain source of truth (reads from DomainConfig.json)
- Formalized domain detector API (public score_all_domains)
- Added AxP signature to all exports
- Sanitized export filenames
- Ready for auth integration with session storage
- Maintains all v2.4 features (domain detection, TAES, history, etc.)
"""

import streamlit as st
from pathlib import Path
import logging, sys, traceback
from datetime import datetime, timedelta
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Dict, List, Tuple
import re
import os

# Import AxProtocol components
try:
    from axp.orchestration.chain import run_chain
    from axp.utils.session_logging import log_session
    from run_axp import MODEL, TIER  # Module-level constants
    from ledger import get_last_n_entries, verify_hash_chain
    from taes_evaluation import check_cognitive_disalignment
    from pathlib import Path as PathLib
except ImportError as e:
    st.error(f"Failed to import AxProtocol modules: {e}")
    st.stop()

# ============================================================================
# Configuration & Constants
# ============================================================================

# Page config
st.set_page_config(
    page_title="AxProtocol Operator Console",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Paths
UIP_CFG = Path('config/ui_presentation.json')
LOG_DIR = Path("logs/sessions")
IRD_LOG = Path("logs/ird_log.csv")
LEDGER_DB = Path("logs/ledger/audit_ledger.db")
EXPORTS_DIR = Path("logs/exports")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
DOMAIN_CONFIG = Path("DomainConfig.json")
ALLOWLIST_LIMIT = 50
ALLOWLIST_FILE = Path("config/allowlist.txt")
ALLOWLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
ENABLE_SIGNUP = os.getenv("ENABLE_SIGNUP", "false").lower() == "true"

# FIX 1: Load domains from DomainConfig.json (source of truth)
def load_domains_from_config() -> List[str]:
    """
    FIX 1: Read domains from DomainConfig.json to avoid config drift.
    Falls back to hardcoded list if config file unavailable.
    """
    try:
        if DOMAIN_CONFIG.exists():
            with open(DOMAIN_CONFIG, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Extract domain names from config
            domains = list(config.get('domains', {}).keys())

            if domains:
                return sorted(domains)  # Alphabetical order
            else:
                st.sidebar.warning(" DomainConfig.json found but no domains defined, using defaults")
        else:
            st.sidebar.info(" DomainConfig.json not found, using default domains")
    except Exception as e:
        st.sidebar.warning(f" Error loading DomainConfig.json: {e}, using defaults")

    # Fallback to hardcoded list
    return [
        "marketing", "technical", "ops", "creative",
        "education", "product", "strategy", "research"
    ]

# Load domains from config (source of truth)
DOMAINS = load_domains_from_config()

# UI presentation config loader
@st.cache_resource
def load_ui_presentation() -> dict:
    try:
        p = UIP_CFG
        if p.exists():
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {"smart_view": True, "show_tables_by_default": False, "table_thresholds": {"C": 5, "A.kpi_table": 1}}
# Alert thresholds
IRD_WARNING_THRESHOLD = 0.4
IRD_CRITICAL_THRESHOLD = 0.6
SCORE_THRESHOLD = 85

# FIX 3: AxP signature for exports

# UI logging: ensure we always capture exceptions to a file
def _configure_ui_logging():
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    fh_path = logs_dir / "app_ui.log"
    logger = logging.getLogger("axp.ui")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(fh_path, encoding="utf8")
        fh.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    def _hook(exc_type, exc_value, exc_tb):
        try:
            msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            logger.error("Unhandled exception:\n%s", msg)
        finally:
            # Also print to Streamlit console
            sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook

_configure_ui_logging()
AXP_SIGNATURE = """
---
*Generated by AxProtocol v2.5*
*Multi-Domain Reasoning Engine*
*https://github.com/axprotocol*
"""

# ============================================================================
# Utility Functions
# ============================================================================

def load_allowlist() -> set:
    """Return unique identifiers from allowlist file."""
    try:
        if not ALLOWLIST_FILE.exists():
            return set()
        entries = {line.strip() for line in ALLOWLIST_FILE.read_text(encoding="utf8").splitlines() if line.strip()}
        return entries
    except Exception:
        return set()

@st.cache_resource
# PHASE 1: Domain detector removed - Creative domain only
# def get_domain_detector():
#     """Initialize and cache domain detector."""
#     try:
#         return DomainDetector()
#     except Exception as e:
#         st.sidebar.warning(f"Domain detector unavailable: {e}")
#         return None


def load_ird_data(limit: Optional[int] = None) -> Optional[pd.DataFrame]:
    """Load IRD log data with error handling."""
    if not IRD_LOG.exists():
        return None

    try:
        df = pd.read_csv(IRD_LOG)
        if df.empty:
            return None

        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        if limit:
            df = df.tail(limit)

        return df
    except Exception as e:
        st.error(f"Error loading IRD data: {e}")
        return None


def load_session_logs() -> List[Dict]:
    """Load all session log files with metadata."""
    if not LOG_DIR.exists():
        return []

    sessions = []
    for log_file in LOG_DIR.glob("*.log"):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metadata from log
            metadata = {
                'filename': log_file.name,
                'path': str(log_file),
                'timestamp': log_file.stat().st_mtime,
                'size': log_file.stat().st_size,
                'content': content,
            }

            # Parse key fields from content
            for line in content.split('\n')[:10]:  # Check first 10 lines
                if line.startswith('[Model]'):
                    metadata['model'] = line.split(']', 1)[1].strip()
                elif line.startswith('[Tier]'):
                    metadata['tier'] = line.split(']', 1)[1].strip()
                elif line.startswith('[Domain]'):
                    metadata['domain'] = line.split(']', 1)[1].strip()
                elif line.startswith('[Objective]'):
                    # Get objective from next line
                    obj_start = content.find('[Objective]')
                    if obj_start != -1:
                        obj_text = content[obj_start:obj_start+200]
                        lines = obj_text.split('\n')
                        if len(lines) > 1:
                            metadata['objective'] = lines[1][:100] + '...'

            sessions.append(metadata)
        except Exception as e:
            continue

    # Sort by timestamp (newest first)
    sessions.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    return sessions


# FIX 3: Filename sanitization helper
def sanitize_filename(filename: str) -> str:
    """
    FIX 3: Sanitize filename to prevent path traversal and special chars.
    """
    # Remove path separators and special chars
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def export_session_results(
    objective: str,
    results: Dict,
    outputs: Dict,
    format: str = "json"
) -> Path:
    """
    Export session results in specified format.

    FIX 3: Sanitizes filenames and adds AxP signature watermark.

    Args:
        objective: The campaign objective
        results: Results dictionary from run_chain
        outputs: Dictionary with role outputs (s, a, p_rev, c_rev, crit)
        format: Export format ('json', 'csv', 'markdown')

    Returns:
        Path to exported file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = results.get('domain', 'unknown')

    # FIX 3: Sanitize domain for filename
    domain_safe = sanitize_filename(domain)

    if format == "json":
        filepath = EXPORTS_DIR / f"session_{timestamp}_{domain_safe}.json"
        export_data = {
            'timestamp': timestamp,
            'domain': domain,
            'tier': TIER,
            'model': MODEL,
            'objective': objective,
            'outputs': outputs,
            'taes_metrics': {
                role: results[role]['taes']
                for role in results
                if isinstance(results[role], dict) and 'taes' in results[role]
            },
            'scores': {
                role: results[role].get('scores', {})
                for role in results
                if isinstance(results[role], dict) and 'scores' in results[role]
            },
            # FIX 3: Add AxP signature
            '_metadata': {
                'generator': 'AxProtocol v2.5',
                'generated_at': timestamp,
                'format': 'json',
                'url': 'https://github.com/axprotocol'
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)

    elif format == "markdown":
        filepath = EXPORTS_DIR / f"session_{timestamp}_{domain_safe}.md"

        md_content = f"""# AxProtocol Session Report
**Timestamp:** {timestamp}
**Domain:** {domain}
**Tier:** {TIER}
**Model:** {MODEL}

## Objective
{objective}

## Producer Output
{outputs['producer']}

## Courier Output
{outputs['courier']}

## Critic Review
{outputs['critic']}

## TAES Metrics
"""
        # Add TAES table
        for role in ['strategist', 'analyst', 'producer_revised', 'courier_revised']:
            if role in results and 'taes' in results[role]:
                taes = results[role]['taes']
                # Handle missing role_name (fallback TAES doesn't include it)
                role_name = taes.get('role_name', role.replace('_', ' ').title())
                md_content += f"\n**{role_name}:**  \n"
                md_content += f"- Integrity Vector: {taes['integrity_vector']}  \n"
                md_content += f"- IRD: {taes['ird']:.3f}  \n"
                md_content += f"- RRP Required: {'Yes' if taes['requires_rrp'] else 'No'}  \n"

        # FIX 3: Add AxP signature watermark
        md_content += AXP_SIGNATURE

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

    elif format == "csv":
        filepath = EXPORTS_DIR / f"session_{timestamp}_{domain_safe}.csv"

        # Create CSV with TAES metrics
        rows = []
        for role in ['strategist', 'analyst', 'producer_revised', 'courier_revised']:
            if role in results and 'taes' in results[role]:
                taes = results[role]['taes']
                # Handle missing role_name (fallback TAES doesn't include it)
                role_name = taes.get('role_name', role.replace('_', ' ').title())
                rows.append({
                    'role': role_name,
                    'iv': taes['integrity_vector'],
                    'ird': taes['ird'],
                    'rrp_required': taes['requires_rrp'],
                    'domain': domain,
                    'timestamp': timestamp,
                    # FIX 3: Add generator metadata
                    'generator': 'AxProtocol v2.5'
                })

        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False)

    return filepath


def create_domain_confidence_chart(scores: Dict[str, float]) -> go.Figure:
    """Create interactive bar chart showing domain confidence scores."""
    sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    domains = [d[0].capitalize() for d in sorted_domains]
    confidences = [d[1] for d in sorted_domains]

    # Color code: winner in green, others in blue
    colors = ['#28a745' if i == 0 else '#007bff' for i in range(len(domains))]

    fig = go.Figure(data=[
        go.Bar(
            x=domains,
            y=confidences,
            marker_color=colors,
            text=[f"{c:.2%}" for c in confidences],
            textposition='auto',
        )
    ])

    fig.update_layout(
        title="Domain Detection Confidence",
        xaxis_title="Domain",
        yaxis_title="Confidence Score",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )

    return fig


def create_ird_trend_chart(df: pd.DataFrame, limit: int = 30) -> go.Figure:
    """Create IRD trend chart with alert zones."""
    df_recent = df.tail(limit).copy()

    fig = go.Figure()

    # Add IRD line
    fig.add_trace(go.Scatter(
        x=df_recent.index,
        y=df_recent['ird'],
        mode='lines+markers',
        name='IRD',
        line=dict(color='#007bff', width=2),
        marker=dict(size=6)
    ))

    # Add threshold lines
    fig.add_hline(
        y=IRD_WARNING_THRESHOLD,
        line_dash="dash",
        line_color="orange",
        annotation_text="Warning (0.4)"
    )
    fig.add_hline(
        y=IRD_CRITICAL_THRESHOLD,
        line_dash="dash",
        line_color="red",
        annotation_text="Critical (0.6)"
    )

    fig.update_layout(
        title=f"IRD Trend (Last {limit} Executions)",
        xaxis_title="Execution",
        yaxis_title="IRD Score",
        height=400,
        hovermode='x unified'
    )

    return fig


# ============================================================================
# UI Components
# ============================================================================

def render_sidebar():
    """Render sidebar with system info and controls."""
    st.sidebar.title("System Control")

    st.sidebar.markdown(
        f"""
**System Configuration:**
- **Tier:** {TIER}
- **Model:** {MODEL}
- **Version:** v2.5
- **Domains:** {len(DOMAINS)} loaded
        """
    )

    st.sidebar.markdown("### Browse Artifacts")

    with st.sidebar.expander("Sessions (logs/sessions)", expanded=False):
        try:
            sess_dir = Path("logs/sessions")
            sess_dir.mkdir(parents=True, exist_ok=True)
            files = sorted(sess_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
            if files:
                sel = st.selectbox("Session file", options=[str(p.name) for p in files], key="sess_sel")
                if sel:
                    txt = (sess_dir / sel).read_text(encoding="utf8", errors="ignore")
                    st.text_area("Preview", txt, height=180)
                    st.download_button("Download", data=txt, file_name=sel, mime="text/plain")
            else:
                st.caption("No session logs yet.")
        except Exception:
            logging.getLogger("axp.ui").exception("Sidebar: loading sessions failed")
            st.caption("Error loading sessions; see app_ui.log")

    with st.sidebar.expander("Ledger (logs/ledger)", expanded=False):
        try:
            from ledger import get_last_n_entries
            rows = get_last_n_entries(20)
            if rows:
                import pandas as pd
                st.dataframe(pd.DataFrame(rows))
            else:
                st.caption("No ledger entries yet.")
        except Exception:
            logging.getLogger("axp.ui").exception("Sidebar: ledger preview failed")
            st.caption("Ledger unavailable; see app_ui.log")

    with st.sidebar.expander("IRD Log (logs/ird_log.csv)", expanded=False):
        try:
            import pandas as pd
            ird_path = Path("logs/ird_log.csv")
            if ird_path.exists():
                df = pd.read_csv(ird_path)
                st.dataframe(df.tail(50))
                st.download_button("Download CSV", data=ird_path.read_bytes(), file_name="ird_log.csv", mime="text/csv")
            else:
                st.caption("No IRD log found.")
        except Exception:
            logging.getLogger("axp.ui").exception("Sidebar: IRD log preview failed")
            st.caption("IRD log error; see app_ui.log")

    with st.sidebar.expander("Exports (logs/exports)", expanded=False):
        try:
            exp_dir = EXPORTS_DIR
            exp_dir.mkdir(parents=True, exist_ok=True)
            files = sorted(exp_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
            if files:
                for file_path in files:
                    st.download_button(
                        f"Download {file_path.name}",
                        data=file_path.read_bytes(),
                        file_name=file_path.name,
                        key=f"export_dl_{file_path.name}"
                    )
            else:
                st.caption("No exports yet.")
        except Exception:
            logging.getLogger("axp.ui").exception("Sidebar: exports listing failed")
            st.caption("Exports error; see app_ui.log")

    with st.sidebar.expander("App Log (logs/app_ui.log)", expanded=False):
        try:
            log_path = Path("logs/app_ui.log")
            if log_path.exists():
                txt = log_path.read_text(encoding="utf8", errors="ignore")
                st.text_area("app_ui.log", txt.splitlines()[-400:] if txt else "", height=180)
                if st.button("Refresh app log"):
                    st.experimental_rerun()
                st.download_button("Download app_ui.log", data=log_path.read_bytes(), file_name="app_ui.log")
            else:
                st.caption("No app_ui.log yet.")
        except Exception:
            logging.getLogger("axp.ui").exception("Sidebar: app log preview failed")
            st.caption("App log error; see app_ui.log")

    with st.sidebar.expander("Session Errors (logs/sessions/*_errors.log)", expanded=False):
        try:
            err_files = sorted(Path("logs/sessions").glob("*_errors.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]
            if err_files:
                sel = st.selectbox("Error file", options=[f.name for f in err_files], key="err_sel")
                if sel:
                    etxt = err_files[[f.name for f in err_files].index(sel)].read_text(encoding="utf8", errors="ignore")
                    st.text_area("Preview", etxt.splitlines()[-400:] if etxt else "", height=220)
                    st.download_button("Download", data=etxt, file_name=sel, mime="text/plain")
            else:
                st.caption("No session error logs yet.")
        except Exception:
            logging.getLogger("axp.ui").exception("Sidebar: session error logs preview failed")
            st.caption("Error loading session error logs; see app_ui.log")

    # FIX 1: Show domain source
    st.sidebar.markdown(f"""
**Domain Configuration:**
- Source: {'DomainConfig.json' if DOMAIN_CONFIG.exists() else 'Default hardcoded'}
- Count: {len(DOMAINS)}
- List: {', '.join(DOMAINS[:4])}{'...' if len(DOMAINS) > 4 else ''}
    """)

    # FIX 4: Auth integration note (for future)
    if st.sidebar.checkbox("Auth Integration (Future)", value=False):
        st.sidebar.info("""
**Future Enhancement:**
Auth tokens will be stored securely in session state, not environment variables.
        """)


def render_main_interface():
    """Render main execution interface."""
    st.title(" AxProtocol Operator Console")
    st.caption("**v2.5**  Production Hardened with Config-Driven Domains")

    allowlist = load_allowlist()
    remaining = max(0, ALLOWLIST_LIMIT - len(allowlist))
    if len(allowlist) >= ALLOWLIST_LIMIT:
        st.warning("Preview tier capped. Existing early users remain free for life.")
    elif not ENABLE_SIGNUP:
        st.info("Signups are currently closed. Existing allowlisted users retain access.")
    else:
        st.success(f"{remaining} free-preview seats remaining for early adopters.")

    # Create tabs for different views
    tab_execute, tab_history, tab_analytics, tab_about = st.tabs([
        " Execute",
        " Session History",
        " Analytics",
        " About"
    ])

    with tab_execute:
        render_execute_tab()

    with tab_history:
        render_history_tab()

    with tab_analytics:
        render_analytics_tab()

    with tab_about:
        render_about_tab()


def render_execute_tab():
    """Render execution tab with domain detection."""
    st.subheader("Campaign Execution")

    # Objective input
    objective = st.text_area(
        "Objective / Transcript",
        height=150,
        placeholder="Enter your campaign objective, project brief, or query...\n\nExample: 'Build a REST API with OAuth authentication'\n\nThe system will automatically detect the domain (technical, marketing, ops, etc.)"
    )

    # PHASE 1: Creative Domain Only - Domain selection disabled
    st.info("**Phase 1: Creative Domain Only** - All executions use the creative domain.")

    # Advanced options in expander
    with st.expander("Advanced Options"):
        col_a1, col_a2 = st.columns(2)

        with col_a1:
            # PHASE 1: Domain override disabled
            st.caption("Domain override disabled in Phase 1")
            enable_domain_override = False
            domain_override = None
            # COMMENTED OUT: Domain override UI (Phase 1 isolation)
            # enable_domain_override = st.checkbox(
            #     "Override Domain Detection",
            #     value=False,
            #     help="Manually specify domain instead of auto-detection"
            # )
            # if enable_domain_override:
            #     domain_override = st.selectbox(
            #         "Select Domain",
            #         options=DOMAINS,
            #         help="Force execution in specific domain"
            #     )
            # else:
            #     domain_override = None

        with col_a2:
            # PHASE 1: Domain preview disabled
            st.caption("Domain preview disabled in Phase 1")
            show_preview = False
            # COMMENTED OUT: Domain preview UI (Phase 1 isolation)
            # show_preview = st.checkbox(
            #     "Preview Domain Detection",
            #     value=True,
            #     help="Show detection confidence before running"
            # )

            export_format = st.selectbox(
                "Export Format",
                options=["None", "JSON", "Markdown", "CSV"],
                help="Automatically export results after execution"
            )

    # PHASE 1: Domain preview disabled
    # COMMENTED OUT: Domain preview logic (Phase 1 isolation)
    # if show_preview and objective.strip() and not enable_domain_override:
    #     detector = get_domain_detector()
    #     if detector:
    #         with st.spinner("Analyzing objective..."):
    #             # FIX 2: Use formalized public API instead of private method
    #             try:
    #                 # Try public method first
    #                 scores = detector.score_all_domains(objective)
    #             except AttributeError:
    #                 # Fallback to private method if public API not yet available
    #                 st.sidebar.warning(" Using private API - update domain_detector.py")
    #                 scores = detector._score_all_domains(objective)
    #
    #             detected = detector.detect(objective, verbose=False)
    #             confidence = scores.get(detected, 0.0)
    #
    #         st.info(f"**Predicted Domain:** {detected.upper()} (confidence: {confidence:.1%})")
    #
    #         # Show confidence chart
    #         fig = create_domain_confidence_chart(scores)
    #         st.plotly_chart(fig, use_container_width=True)

    # Execute button
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        execute_button = st.button(
            " Execute AxProtocol Chain",
            type="primary",
            use_container_width=True
        )

    with col2:
        if st.button(" Clear", use_container_width=True):
            st.rerun()

    # Phase 2: Handle Caller interaction state
    if 'caller_pending_confirmation' in st.session_state and st.session_state['caller_pending_confirmation']:
        render_caller_confirmation()
        return

    # Execution logic
    if execute_button:
        if not objective.strip():
            st.warning(" Please enter an objective first.")
            return

        # Execute chain
        with st.spinner(" Executing AxProtocol reasoning chain..."):
            try:
                # Phase 2: Call chain - Caller will triage the objective
                base_dir = PathLib(__file__).parent
                s, a, p_rev, c_rev, crit, results = run_chain(
                    objective,
                    base_dir=base_dir
                )

                # Phase 2: Handle Caller's "suggest_optimized_prompt_and_insight" state
                if results.get("status") == "suggest_optimized_prompt_and_insight":
                    # Store caller result in session state for confirmation UI
                    st.session_state['caller_pending_confirmation'] = True
                    st.session_state['caller_result'] = results.get("caller", {})
                    st.session_state['original_objective'] = objective
                    st.rerun()
                    return

                # Check if Caller terminated
                if results.get("terminated"):
                    st.warning(" Request terminated by Caller.")
                    st.info(results.get("caller", {}).get("response", "No reason provided"))
                    return

                # Log session
                log_file = log_session(objective, s, a, p_rev, c_rev, crit, results, base_dir, TIER, MODEL)

                # Store in session state for display
                st.session_state['last_execution'] = {
                    'objective': objective,
                    'results': results,
                    'outputs': {
                        'strategist': s,
                        'analyst': a,
                        'producer': p_rev,
                        'courier': c_rev,
                        'critic': crit
                    },
                    'log_file': log_file,
                    'timestamp': datetime.now()
                }

                st.success(" Execution complete!")

                # Export if requested
                if export_format != "None":
                    export_path = export_session_results(
                        objective,
                        results,
                        st.session_state['last_execution']['outputs'],
                        format=export_format.lower()
                    )
                    st.success(f" Exported to: `{export_path}`")

            except Exception as e:
                st.error(f" Execution failed: {e}")
                st.exception(e)
                return

    # Display results if available
    if 'last_execution' in st.session_state:
        render_execution_results(st.session_state['last_execution'])


def render_caller_confirmation():
    """Phase 2: Render Caller's optimized prompt suggestion and get user confirmation."""
    st.markdown("---")
    st.subheader("🔍 Caller: Optimized Prompt Suggestion")

    caller_result = st.session_state.get('caller_result', {})
    suggested_objective = caller_result.get("suggested_objective", "")
    axp_insight = caller_result.get("axp_insight", {})
    confirmation_question = caller_result.get("user_confirmation_question",
        "Is this optimized prompt aligned with your core intent? (Yes/No)")

    # Display suggested objective
    st.markdown("### 📝 Suggested Objective")
    st.info(suggested_objective)

    # Display AxP Insight
    if axp_insight:
        st.markdown("### 💡 AxP Insight")
        st.markdown(f"**{axp_insight.get('title', 'Analysis')}**")

        perspectives = axp_insight.get("perspectives", [])
        for i, p in enumerate(perspectives, 1):
            name = p.get("name", f"Interpretation {i}")
            desc = p.get("description", "")
            with st.expander(f"🔸 {name}"):
                st.write(desc)

        verdict = axp_insight.get("verdict", {})
        if verdict:
            st.markdown("### ✅ Verdict")
            verdict_name = verdict.get("verdict_name", "")
            reasoning = verdict.get("reasoning", "")
            st.success(f"**{verdict_name}**")
            st.write(reasoning)

    st.markdown("---")
    st.markdown(f"**{confirmation_question}**")

    # User confirmation input
    col1, col2 = st.columns([3, 1])

    with col1:
        user_response = st.text_input(
            "Your response:",
            placeholder="Type 'Yes' or 'No', optionally followed by feedback",
            key="caller_user_response"
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

    with col_btn1:
        if st.button("✅ Confirm (Yes)", use_container_width=True, type="primary"):
            process_caller_response(True, user_response)

    with col_btn2:
        if st.button("❌ Reject (No)", use_container_width=True):
            process_caller_response(False, user_response)

    with col_btn3:
        if st.button("🔄 Use Original Objective", use_container_width=True):
            # Use original objective without optimization
            original_objective = st.session_state.get('original_objective', '')
            st.session_state['caller_pending_confirmation'] = False
            st.session_state['caller_result'] = None
            # Re-run with original objective
            with st.spinner("Executing with original objective..."):
                base_dir = PathLib(__file__).parent
                s, a, p_rev, c_rev, crit, results = run_chain(
                    original_objective,
                    base_dir=base_dir
                )
                log_file = log_session(original_objective, s, a, p_rev, c_rev, crit, results, base_dir, TIER, MODEL)
                st.session_state['last_execution'] = {
                    'objective': original_objective,
                    'results': results,
                    'outputs': {
                        'strategist': s,
                        'analyst': a,
                        'producer': p_rev,
                        'courier': c_rev,
                        'critic': crit
                    },
                    'log_file': log_file,
                    'timestamp': datetime.now()
                }
            st.rerun()


def process_caller_response(user_affirmed: bool, user_feedback: str = ""):
    """Phase 2: Process user's response to Caller's suggestion and run chain."""
    caller_result = st.session_state.get('caller_result', {})
    suggested_objective = caller_result.get("suggested_objective", "")
    original_objective = st.session_state.get('original_objective', '')

    # Parse user feedback from input if provided
    if user_feedback:
        feedback_text = user_feedback.strip()
        # Remove Yes/No prefix if present
        if feedback_text.lower().startswith("yes"):
            feedback_text = feedback_text[3:].strip()
        elif feedback_text.lower().startswith("no"):
            feedback_text = feedback_text[2:].strip()
    else:
        feedback_text = ""

    # Always use suggested objective (best effort approach)
    final_objective = suggested_objective
    user_rejection = not user_affirmed

    # Clear caller state
    st.session_state['caller_pending_confirmation'] = False
    st.session_state['caller_result'] = None

    # Run chain with final objective and user rejection flag
    with st.spinner("Executing AxProtocol chain with optimized objective..."):
        base_dir = PathLib(__file__).parent
        s, a, p_rev, c_rev, crit, results = run_chain(
            final_objective,
            base_dir=base_dir,
            user_rejection=user_rejection,
            user_feedback_on_prompt=feedback_text if feedback_text else None,
        )

        # Log session
        log_file = log_session(original_objective, s, a, p_rev, c_rev, crit, results, base_dir, TIER, MODEL)

        # Store in session state for display
        st.session_state['last_execution'] = {
            'objective': original_objective,
            'final_objective': final_objective,
            'user_affirmed': user_affirmed,
            'user_feedback': feedback_text,
            'results': results,
            'outputs': {
                'strategist': s,
                'analyst': a,
                'producer': p_rev,
                'courier': c_rev,
                'critic': crit
            },
            'log_file': log_file,
            'timestamp': datetime.now()
        }

    st.rerun()


def render_execution_results(execution_data: Dict):
    """Render execution results with comprehensive metrics."""
    st.markdown("---")
    st.subheader(" Execution Results")

    results = execution_data['results']
    outputs = execution_data['outputs']

    # Domain and metadata
    domain = results.get('domain', 'unknown')

    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    col_meta1.metric("Domain", domain.upper())
    col_meta2.metric("Tier", TIER)
    col_meta3.metric("Model", MODEL)
    col_meta4.metric("Timestamp", execution_data['timestamp'].strftime("%H:%M:%S"))

    # TAES Metrics Dashboard
    st.markdown("###  TAES Evaluation Summary")

    taes_data = []
    for role_key in ['strategist', 'analyst', 'producer_revised', 'courier_revised']:
        if role_key in results and 'taes' in results[role_key]:
            taes = results[role_key]['taes']
            # Handle missing role_name (fallback TAES doesn't include it)
            role_name = taes.get('role_name', role_key.replace('_', ' ').title())
            taes_data.append({
                'Role': role_name,
                'Integrity Vector': taes['integrity_vector'],
                'IRD': f"{taes['ird']:.3f}",
                'Status': ' RRP Required' if taes['requires_rrp'] else ' Healthy',
                'Alert': taes['ird'] > IRD_WARNING_THRESHOLD
            })

    if taes_data:
        df_taes = pd.DataFrame(taes_data)

        # Highlight rows with alerts
        def highlight_alerts(row):
            if row['Alert']:
                return ['background-color: #fff3cd'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_taes.style.apply(highlight_alerts, axis=1),
            use_container_width=True,
            hide_index=True
        )

        # Alert summary
        alerts = sum(1 for item in taes_data if item['Alert'])
        if alerts > 0:
            st.warning(f" {alerts} role(s) exceeded IRD warning threshold!")

    registry = results.get('registry') if isinstance(results, dict) else {}
    if registry:
        st.markdown("###  Registry Summary")

        def _format_cell(value):
            if isinstance(value, list):
                if all(isinstance(v, (str, int, float)) for v in value):
                    return ", ".join(str(v) for v in value)
                return json.dumps(value, indent=2)
            if isinstance(value, dict):
                return json.dumps(value, indent=2)
            return value

        def render_registry_slice(key: str, title: str, columns: list[str] | None = None) -> None:
            data = registry.get(key) or []
            st.markdown(f"####  {title}")
            if not data:
                st.caption(" No data recorded for this slice.")
                return
            rows = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                cols = columns or list(item.keys())
                rows.append({col: _format_cell(item.get(col)) for col in cols})
            if rows:
                df_slice = pd.DataFrame(rows)
                st.dataframe(df_slice, use_container_width=True, hide_index=True)
            with st.expander(f"Advanced: raw {key} JSON", expanded=False):
                st.json(data)







        qa_log = results.get('qa') or {}
        if qa_log:
            with st.expander("Advanced: Clarification Log (Q)", expanded=False):
                for key, payload in qa_log.items():
                    st.markdown(f"**{key}**")
                    st.caption(f"Q: {payload.get('question', '')}")
                    st.caption(f"A: {payload.get('answer', '')}")

    composer = results.get('composer')
    if composer:
        st.markdown("###  Executive Composer Report")
        st.markdown(composer)
        st.caption("Chain-level synthesis generated after S/A/P/C/X coordination.")

    # Advanced: Governance and Raw JSON (optional, shown if present)
    gov = results.get('governance') if isinstance(results, dict) else None
    if gov:
        with st.expander("Advanced: Governance Signals", expanded=False):
            # Show hard and soft signals if available
            hard = gov.get('signals') if isinstance(gov, dict) else None
            soft = gov.get('soft_signals') if isinstance(gov, dict) else None
            no_go = gov.get('no_go') if isinstance(gov, dict) else None
            st.write({
                'no_go': no_go,
                'signals': list(hard) if isinstance(hard, (list, set)) else hard,
                'soft_signals': list(soft) if isinstance(soft, (list, set)) else soft,
            })
            st.caption("Mode=hard signals enforce TAES caps/floors; mode=soft are logged only.")
            sentinel = results.get('sentinel') if isinstance(results, dict) else None
            if sentinel:
                st.write({
                    'sentinel_score': sentinel.get('score'),
                    'sentinel_flags': sentinel.get('flags'),
                })
                drift = (results.get('governance') or {}).get('drift')
                if drift:
                    st.caption(f"Drift findings: {len(drift)} recorded")

    with st.expander("Advanced: Raw Results JSON", expanded=False):
        try:
            st.json(results)
        except Exception:
            st.write(results)

    # Role Outputs
    st.markdown("###  Role Outputs")

    with st.expander(" Strategist", expanded=False):
        st.markdown(outputs['strategist'])

    with st.expander(" Analyst", expanded=False):
        st.markdown(outputs['analyst'])

    with st.expander(" Producer", expanded=True):
        st.markdown(outputs['producer'])

    # Smart View policy
    cfg = load_ui_presentation()
    always_tables = st.checkbox("Advanced: Always show tables", value=bool(cfg.get('show_tables_by_default', False)))
    smart = bool(cfg.get('smart_view', True)) and not always_tables
    tcfg = cfg.get('table_thresholds', {}) if isinstance(cfg, dict) else {}

    def _bullet_list(key: str, title: str, fmt_fn):
        data = registry.get(key) or []
        st.markdown(f"####  {title}")
        if not data:
            st.caption(" No data recorded for this slice.")
            return
        for item in data[:6]:
            st.markdown(f"- {fmt_fn(item)}")
        if len(data) > 6:
            st.caption(f"… {len(data)-6} more")        # S
        if not smart:
            render_registry_slice("S", "Strategy Objects (S)", ["s_id", "title", "audience", "hooks", "three_step_plan", "acceptance_tests"])
        else:
            _bullet_list("S", "Strategy Objects (S)", lambda it: f"{it.get('s_id')}: {it.get('title')}")
        # A
        a_has_kpis = any((isinstance(it, dict) and it.get('kpi_table')) for it in (registry.get('A') or []))
        if (not smart) or a_has_kpis:
            render_registry_slice("A", "Analysis Objects (A)", ["a_id", "s_refs", "kpi_table", "falsifications", "risks"])
        else:
            _bullet_list("A", "Analysis Objects (A)", lambda it: f"{it.get('a_id')} -> refs {it.get('s_refs')}")
        # P
        if not smart:
            render_registry_slice("P", "Production Assets (P)", ["p_id", "a_refs", "spec_type", "body"])
        else:
            _bullet_list("P", "Production Assets (P)", lambda it: f"{it.get('p_id')} [{it.get('spec_type')}] refs {it.get('a_refs')}")
        # C (table when long schedule)
        c_thresh = int(tcfg.get('C', 5)) if str(tcfg.get('C', '5')).isdigit() else 5
        if (not smart) or len(registry.get('C') or []) >= c_thresh:
            render_registry_slice("C", "Courier Schedule (C)", ["day", "time", "channel", "p_id", "kpi_target", "owner_action"])
        else:
            _bullet_list("C", "Courier Schedule (C)", lambda it: f"{it.get('day')} {it.get('time')} via {it.get('channel')} -> {it.get('p_id')}")
        # X
        if not smart:
            render_registry_slice("X", "Critic Findings (X)", ["x_id", "refs", "issue", "fix", "severity", "proof_scores"])
        else:
            _bullet_list("X", "Critic Findings (X)", lambda it: f"{it.get('x_id')} sev={it.get('severity')} refs={it.get('refs')}")
    with st.expander(" Courier", expanded=True):
        st.markdown(outputs['courier'])

    with st.expander(" Critic", expanded=False):
        st.markdown(outputs['critic'])

    # Advanced: Downloads (composer/registry-ready placeholders)
    with st.expander("Advanced: Downloads", expanded=False):
        # Export raw results JSON
        try:
            results_json = json.dumps(results, indent=2).encode('utf-8')
            st.download_button(
                label="Download results.json",
                data=results_json,
                file_name="results.json",
                mime="application/json",
            )
        except Exception:
            pass

        # Export role outputs as markdown
        try:
            md_blob = [
                "# AxProtocol Role Outputs",
                "",
                "## Strategist\n" + (outputs.get('strategist') or ''),
                "\n## Analyst\n" + (outputs.get('analyst') or ''),
                "\n## Producer (revised)\n" + (outputs.get('producer') or ''),
                "\n## Courier (revised)\n" + (outputs.get('courier') or ''),
                "\n## Critic\n" + (outputs.get('critic') or ''),
                "",
                AXP_SIGNATURE.strip(),
            ]
            md_bytes = "\n".join(md_blob).encode('utf-8')
            st.download_button(
                label="Download role_outputs.md",
                data=md_bytes,
                file_name="role_outputs.md",
                mime="text/markdown",
            )
        except Exception:
            pass

        composer_text = results.get('composer')
        if composer_text:
            try:
                composer_bytes = composer_text.encode('utf-8')
                st.download_button(
                    label="Download composer_report.md",
                    data=composer_bytes,
                    file_name="composer_report.md",
                    mime="text/markdown",
                )
            except Exception:
                pass

        if registry:
            try:
                registry_bytes = json.dumps(registry, indent=2).encode('utf-8')
                st.download_button(
                    label="Download registry.json",
                    data=registry_bytes,
                    file_name="registry.json",
                    mime="application/json",
                )
            except Exception:
                pass


def render_history_tab():
    """Render session history browser."""
    st.subheader(" Session History")

    sessions = load_session_logs()

    if not sessions:
        st.info(" No sessions found. Execute a campaign to create session history.")
        return

    st.markdown(f"**Total Sessions:** {len(sessions)}")

    # Filters
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        filter_model = st.selectbox(
            "Filter by Model",
            options=["All", MODEL],
            index=0
        )

    with col_f2:
        sort_order = st.selectbox(
            "Sort by",
            options=["Newest First", "Oldest First"],
            index=0
        )

    # Apply filters
    filtered_sessions = sessions
    # PHASE 1: Domain filter removed - Creative domain only
    if filter_model != "All":
        filtered_sessions = [
            s for s in filtered_sessions
            if s.get('model', '') == filter_model
        ]

    if sort_order == "Oldest First":
        filtered_sessions.reverse()

    # Display sessions
    st.markdown(f"**Showing {len(filtered_sessions)} session(s)**")

    for idx, session in enumerate(filtered_sessions[:20]):  # Limit to 20 most recent
        with st.expander(
            f"Session {idx+1}: {session.get('domain', 'Unknown').upper()} | "
            f"{datetime.fromtimestamp(session['timestamp']).strftime('%Y-%m-%d %H:%M')}"
        ):
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("Domain", session.get('domain', 'N/A').upper())
            col_s2.metric("Model", session.get('model', 'N/A'))
            col_s3.metric("Size", f"{session['size'] / 1024:.1f} KB")

            if 'objective' in session:
                st.markdown(f"**Objective:** {session['objective']}")

            if st.button(f" View Full Log", key=f"view_{idx}"):
                st.code(session['content'], language='text')


def render_analytics_tab():
    """Render analytics and monitoring dashboard."""
    st.subheader(" System Analytics")

    # IRD Trend Analysis
    st.markdown("###  IRD Trend Analysis")

    ird_df = load_ird_data(limit=50)

    if ird_df is not None and not ird_df.empty:
        # IRD trend chart
        fig_ird = create_ird_trend_chart(ird_df, limit=30)
        st.plotly_chart(fig_ird, use_container_width=True)

        # IRD statistics
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        col_stat1.metric("Mean IRD", f"{ird_df['ird'].mean():.3f}")
        col_stat2.metric("Median IRD", f"{ird_df['ird'].median():.3f}")
        col_stat3.metric("Min IRD", f"{ird_df['ird'].min():.3f}")
        col_stat4.metric("Max IRD", f"{ird_df['ird'].max():.3f}")

        # Domain breakdown
        if 'domain' in ird_df.columns:
            st.markdown("###  IRD by Domain")
            domain_stats = ird_df.groupby('domain')['ird'].agg(['mean', 'count']).reset_index()
            domain_stats.columns = ['Domain', 'Mean IRD', 'Count']
            domain_stats = domain_stats.sort_values('Mean IRD')

            fig_domains = go.Figure(data=[
                go.Bar(
                    x=domain_stats['Domain'],
                    y=domain_stats['Mean IRD'],
                    text=domain_stats['Count'],
                    texttemplate='n=%{text}',
                    textposition='outside'
                )
            ])
            fig_domains.update_layout(
                title="Mean IRD by Domain",
                xaxis_title="Domain",
                yaxis_title="Mean IRD",
                height=400
            )
            st.plotly_chart(fig_domains, use_container_width=True)
    else:
        st.info(" No IRD data available. Execute campaigns to generate analytics.")

    # Ledger Integrity Check
    st.markdown("###  Ledger Integrity")

    if LEDGER_DB.exists():
        try:
            entries = get_last_n_entries(n=10)
            integrity = verify_hash_chain()

            if integrity["valid"]:
                st.success(f" Ledger integrity verified ({integrity['entries']} entries)")
            else:
                st.error(f" Ledger integrity compromised! ({len(integrity['broken'])} broken links)")

            # Show recent entries
            with st.expander(" Recent Ledger Entries"):
                for entry in entries[-5:]:
                    st.text(
                        f"{entry['timestamp']} | "
                        f"{entry['agent_id']}  {entry['action']} | "
                        f"{entry['current_hash'][:16]}..."
                    )
        except Exception as e:
            st.error(f" Ledger check failed: {e}")
    else:
        st.info(" Ledger not initialized.")


def render_about_tab() -> None:
    """Public about view outlining governance promises."""
    st.subheader("About AxProtocol & Sentinel")
    st.markdown(
        """
        ### Governance Promise
        - **Truth > Obedience** – factual integrity beats compliance for every chain.
        - **Signed, Append-Only Ledger** – each evaluation writes an Ed25519-signed record to an immutable log.
        - **Independent Sentinel** – a detached auditor verifies ledger signatures and publishes reports at [https://sentinel.axprotocol.io](https://sentinel.axprotocol.io).

        Our first 50 early users stay free for life. If the preview tier is closed, you can still
        browse public Sentinel reports to verify governance activity in real time.
        """
    )


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point."""
    render_sidebar()
    render_main_interface()


if __name__ == "__main__":
    main()



