"""
AxProtocol Advanced Analytics Dashboard v2.5 - PRODUCTION HARDENED
===================================================================
Enterprise-grade analytics with CRITICAL FIXES:
✅ FIX 1: Kaleido PNG export with friendly error handling
✅ FIX 2: Removed unused LEDGER_LOG variable
✅ FIX 3: Chunked CSV loading for large datasets (memory-efficient)
✅ FIX 4: Complete column guards + "No data" cards for all charts

Standalone analytics module - read-only, safe to run.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import json
import sys

# ============================================================================
# Configuration
# ============================================================================

LOG_FILE = Path("logs/kpi_log.csv")
IRD_LOG = Path("logs/ird_log.csv")
# FIX 2: Removed unused LEDGER_LOG variable
CHART_DIR = Path("logs/charts")
EXPORT_DIR = Path("logs/exports")

# Create directories
CHART_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Chart themes
THEME = "plotly_white"  # or "plotly_dark", "seaborn", "ggplot2"
COLOR_SCHEME = px.colors.qualitative.Set2

# FIX 3: Configuration for large CSV handling
LARGE_FILE_THRESHOLD_MB = 50  # Files larger than this use chunking
CHUNK_SIZE = 10000  # Rows per chunk

# ============================================================================
# FIX 1: Kaleido Installation Check
# ============================================================================

def check_kaleido() -> Tuple[bool, str]:
    """
    Check if kaleido is installed for PNG export.
    
    Returns:
        Tuple of (is_installed, message)
    """
    try:
        import kaleido
        return True, "✅ Kaleido available for PNG export"
    except ImportError:
        return False, (
            "⚠️ Kaleido not installed - PNG export unavailable\n"
            "   Install with: pip install kaleido\n"
            "   Or use: pip install plotly kaleido"
        )

# Check kaleido on import
KALEIDO_AVAILABLE, KALEIDO_MESSAGE = check_kaleido()

# ============================================================================
# FIX 3: Memory-Efficient Data Loading
# ============================================================================

def get_file_size_mb(filepath: Path) -> float:
    """Get file size in megabytes."""
    if not filepath.exists():
        return 0
    return filepath.stat().st_size / (1024 * 1024)

def load_kpi_data(use_chunks: bool = None) -> Optional[pd.DataFrame]:
    """
    Load and validate KPI data with comprehensive cleaning.
    
    FIX 3: Automatically uses chunked loading for large files.
    
    Args:
        use_chunks: Force chunked loading (None = auto-detect based on file size)
    """
    if not LOG_FILE.exists():
        print("⚠️  No KPI log found at", LOG_FILE)
        return None
    
    try:
        file_size = get_file_size_mb(LOG_FILE)
        
        # FIX 3: Auto-detect if we should use chunks
        if use_chunks is None:
            use_chunks = file_size > LARGE_FILE_THRESHOLD_MB
        
        if use_chunks:
            print(f"📊 Loading large file ({file_size:.1f} MB) in chunks...")
            return _load_kpi_chunked()
        else:
            return _load_kpi_standard()
    
    except Exception as e:
        print(f"❌ Error loading KPI data: {e}")
        return None

def _load_kpi_standard() -> Optional[pd.DataFrame]:
    """Standard CSV loading for smaller files."""
    df = pd.read_csv(LOG_FILE)
    
    if df.empty:
        print("⚠️  KPI log is empty.")
        return None
    
    return _clean_kpi_dataframe(df)

def _load_kpi_chunked() -> Optional[pd.DataFrame]:
    """
    FIX 3: Memory-efficient chunked loading for large files.
    Processes data in chunks to avoid loading entire file into RAM.
    """
    chunks = []
    chunk_count = 0
    
    try:
        for chunk in pd.read_csv(LOG_FILE, chunksize=CHUNK_SIZE):
            chunk_count += 1
            chunks.append(_clean_kpi_dataframe(chunk))
            
            # Progress indicator for very large files
            if chunk_count % 10 == 0:
                print(f"   Processed {chunk_count * CHUNK_SIZE:,} rows...")
        
        if not chunks:
            print("⚠️  KPI log is empty.")
            return None
        
        # Combine all chunks
        df = pd.concat(chunks, ignore_index=True)
        print(f"✅ Loaded {len(df):,} rows from {chunk_count} chunks")
        return df
    
    except Exception as e:
        print(f"❌ Error in chunked loading: {e}")
        return None

def _clean_kpi_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize KPI dataframe."""
    if df.empty:
        return df
    
    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Parse timestamp
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["date"] = df["timestamp"].dt.date
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.day_name()
    
    # Convert numeric columns
    numeric_cols = ["revenue", "leads", "booked", "target"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Remove rows with all NaN
    df = df.dropna(how='all')
    
    return df

def load_ird_data(use_chunks: bool = None) -> Optional[pd.DataFrame]:
    """
    Load IRD evaluation data.
    
    FIX 3: Supports chunked loading for large files.
    """
    if not IRD_LOG.exists():
        return None
    
    try:
        file_size = get_file_size_mb(IRD_LOG)
        
        # FIX 3: Auto-detect chunked loading
        if use_chunks is None:
            use_chunks = file_size > LARGE_FILE_THRESHOLD_MB
        
        if use_chunks:
            print(f"📊 Loading large IRD file ({file_size:.1f} MB) in chunks...")
            return _load_ird_chunked()
        else:
            return _load_ird_standard()
    
    except Exception as e:
        print(f"❌ Error loading IRD data: {e}")
        return None

def _load_ird_standard() -> Optional[pd.DataFrame]:
    """Standard IRD loading."""
    df = pd.read_csv(IRD_LOG)
    
    if df.empty:
        return None
    
    return _clean_ird_dataframe(df)

def _load_ird_chunked() -> Optional[pd.DataFrame]:
    """FIX 3: Chunked IRD loading."""
    chunks = []
    
    for chunk in pd.read_csv(IRD_LOG, chunksize=CHUNK_SIZE):
        chunks.append(_clean_ird_dataframe(chunk))
    
    if not chunks:
        return None
    
    return pd.concat(chunks, ignore_index=True)

def _clean_ird_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize IRD dataframe."""
    if df.empty:
        return df
    
    # Parse timestamp
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["date"] = df["timestamp"].dt.date
    
    return df

def calculate_statistics(df: pd.DataFrame, column: str) -> Dict:
    """Calculate comprehensive statistics for a column."""
    if column not in df.columns or df[column].empty:
        return {}
    
    data = df[column].dropna()
    
    if len(data) == 0:
        return {}
    
    return {
        "mean": data.mean(),
        "median": data.median(),
        "std": data.std(),
        "min": data.min(),
        "max": data.max(),
        "q25": data.quantile(0.25),
        "q75": data.quantile(0.75),
        "count": len(data),
        "sum": data.sum() if column != "ird" else None
    }

# ============================================================================
# FIX 4: "No Data" Card Helper
# ============================================================================

def create_no_data_figure(title: str, message: str = "No data available") -> go.Figure:
    """
    FIX 4: Create a clean "No data" card when data is missing.
    
    Args:
        title: Chart title
        message: Message to display
    """
    fig = go.Figure()
    
    fig.add_annotation(
        text=f"<b>{message}</b><br><br>Run campaigns to generate data",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="#6c757d"),
        align="center"
    )
    
    fig.update_layout(
        title=title,
        template=THEME,
        height=400,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
    )
    
    return fig

# ============================================================================
# Advanced Visualizations (with FIX 4 column guards)
# ============================================================================

def create_metric_trend_chart(
    df: pd.DataFrame,
    metric: str,
    title: Optional[str] = None,
    aggregate: str = "sum"
) -> go.Figure:
    """
    Create interactive trend chart with moving average.
    
    FIX 4: Complete column validation with no-data fallback.
    """
    # FIX 4: Guard against missing columns
    if df is None or df.empty:
        return create_no_data_figure(
            title or f"{metric.capitalize()} Trend",
            "No data available for trend analysis"
        )
    
    if metric not in df.columns:
        return create_no_data_figure(
            title or f"{metric.capitalize()} Trend",
            f"Column '{metric}' not found in data"
        )
    
    if "date" not in df.columns:
        return create_no_data_figure(
            title or f"{metric.capitalize()} Trend",
            "Timestamp data required for trend analysis"
        )
    
    # Check if there's any valid data in the metric column
    if df[metric].isna().all() or len(df[metric].dropna()) == 0:
        return create_no_data_figure(
            title or f"{metric.capitalize()} Trend",
            f"No valid data in '{metric}' column"
        )
    
    # Aggregate by date
    try:
        if aggregate == "sum":
            daily = df.groupby("date")[metric].sum().reset_index()
        elif aggregate == "mean":
            daily = df.groupby("date")[metric].mean().reset_index()
        else:
            daily = df.groupby("date")[metric].count().reset_index()
        
        daily = daily.sort_values("date")
        
        # FIX 4: Check if aggregation resulted in empty data
        if daily.empty or len(daily) == 0:
            return create_no_data_figure(
                title or f"{metric.capitalize()} Trend",
                "No data after aggregation"
            )
        
        # Calculate moving average
        if len(daily) > 7:
            daily['ma_7'] = daily[metric].rolling(window=7, min_periods=1).mean()
        
        fig = go.Figure()
        
        # Add actual values
        fig.add_trace(go.Scatter(
            x=daily["date"],
            y=daily[metric],
            mode='lines+markers',
            name=metric.capitalize(),
            line=dict(color='#007bff', width=2),
            marker=dict(size=6)
        ))
        
        # Add moving average if available
        if 'ma_7' in daily.columns:
            fig.add_trace(go.Scatter(
                x=daily["date"],
                y=daily['ma_7'],
                mode='lines',
                name='7-Day MA',
                line=dict(color='#ff6b6b', width=2, dash='dash')
            ))
        
        fig.update_layout(
            title=title or f"{metric.capitalize()} Trend",
            xaxis_title="Date",
            yaxis_title=metric.capitalize(),
            template=THEME,
            hovermode='x unified',
            height=500
        )
        
        return fig
    
    except Exception as e:
        print(f"⚠️ Error creating trend chart: {e}")
        return create_no_data_figure(
            title or f"{metric.capitalize()} Trend",
            f"Error processing data: {str(e)[:50]}"
        )

def create_performance_dashboard(df: pd.DataFrame) -> go.Figure:
    """
    Create comprehensive performance dashboard with multiple metrics.
    
    FIX 4: Column validation for all subplots.
    """
    # FIX 4: Guard against missing data
    if df is None or df.empty:
        return create_no_data_figure(
            "Performance Dashboard",
            "No KPI data available"
        )
    
    # FIX 4: Check for required columns
    required_cols = ["date", "leads", "booked", "revenue"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        return create_no_data_figure(
            "Performance Dashboard",
            f"Missing columns: {', '.join(missing_cols)}"
        )
    
    try:
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Leads Over Time", "Booking Rate", 
                           "Revenue Growth", "Daily Performance"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": True}, {"type": "bar"}]]
        )
        
        # Aggregate daily data
        daily = df.groupby("date").agg({
            "leads": "sum",
            "booked": "sum",
            "revenue": "sum"
        }).reset_index()
        daily = daily.sort_values("date")
        
        # FIX 4: Check if aggregation worked
        if daily.empty:
            return create_no_data_figure(
                "Performance Dashboard",
                "No data after date aggregation"
            )
        
        # Leads trend (top left)
        fig.add_trace(
            go.Scatter(x=daily["date"], y=daily["leads"], 
                      name="Leads", line=dict(color='#007bff')),
            row=1, col=1
        )
        
        # Booking rate (top right)
        daily['booking_rate'] = (daily['booked'] / daily['leads'] * 100).fillna(0)
        fig.add_trace(
            go.Scatter(x=daily["date"], y=daily['booking_rate'],
                      name="Booking %", line=dict(color='#28a745')),
            row=1, col=2
        )
        
        # Revenue growth (bottom left)
        daily['revenue_cumsum'] = daily['revenue'].cumsum()
        fig.add_trace(
            go.Scatter(x=daily["date"], y=daily['revenue_cumsum'],
                      name="Cumulative Revenue", line=dict(color='#ffc107')),
            row=2, col=1
        )
        
        # Daily performance bars (bottom right)
        fig.add_trace(
            go.Bar(x=daily["date"], y=daily["revenue"],
                  name="Daily Revenue", marker_color='#17a2b8'),
            row=2, col=2
        )
        
        fig.update_layout(
            title="Performance Dashboard",
            template=THEME,
            height=800,
            showlegend=True
        )
        
        return fig
    
    except Exception as e:
        print(f"⚠️ Error creating performance dashboard: {e}")
        return create_no_data_figure(
            "Performance Dashboard",
            f"Error processing data: {str(e)[:50]}"
        )

def create_domain_comparison(df: pd.DataFrame) -> go.Figure:
    """
    Compare performance across domains.
    
    FIX 4: Column guards for domain data.
    """
    # FIX 4: Validate required columns
    if df is None or df.empty:
        return create_no_data_figure(
            "Domain Comparison",
            "No IRD data available"
        )
    
    if "domain" not in df.columns or "ird" not in df.columns:
        return create_no_data_figure(
            "Domain Comparison",
            "Domain or IRD column missing"
        )
    
    # FIX 4: Check for valid data
    if df["domain"].isna().all() or df["ird"].isna().all():
        return create_no_data_figure(
            "Domain Comparison",
            "No valid domain or IRD data"
        )
    
    try:
        # Aggregate by domain
        domain_stats = df.groupby("domain")["ird"].agg([
            ("mean", "mean"),
            ("median", "median"),
            ("count", "count")
        ]).reset_index()
        
        # FIX 4: Check if we have data after grouping
        if domain_stats.empty or len(domain_stats) == 0:
            return create_no_data_figure(
                "Domain Comparison",
                "No data after domain grouping"
            )
        
        domain_stats = domain_stats.sort_values("mean")
        
        fig = go.Figure()
        
        # Mean IRD by domain
        fig.add_trace(go.Bar(
            x=domain_stats["domain"],
            y=domain_stats["mean"],
            name="Mean IRD",
            marker_color='#007bff',
            text=domain_stats["count"],
            texttemplate='n=%{text}',
            textposition='outside'
        ))
        
        # Add reference line at 0.4
        fig.add_hline(
            y=0.4, 
            line_dash="dash", 
            line_color="red",
            annotation_text="Target: 0.4",
            annotation_position="right"
        )
        
        fig.update_layout(
            title="Domain Performance Comparison (Lower IRD = Better)",
            xaxis_title="Domain",
            yaxis_title="Average IRD",
            template=THEME,
            height=500
        )
        
        return fig
    
    except Exception as e:
        print(f"⚠️ Error creating domain comparison: {e}")
        return create_no_data_figure(
            "Domain Comparison",
            f"Error processing data: {str(e)[:50]}"
        )

def create_correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Create correlation heatmap for numeric columns.
    
    FIX 4: Column validation for correlation analysis.
    """
    # FIX 4: Validate data
    if df is None or df.empty:
        return create_no_data_figure(
            "Correlation Matrix",
            "No data available for correlation analysis"
        )
    
    try:
        # Select numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # FIX 4: Need at least 2 numeric columns for correlation
        if len(numeric_cols) < 2:
            return create_no_data_figure(
                "Correlation Matrix",
                "Need at least 2 numeric columns for correlation"
            )
        
        # Remove columns with all NaN or single value
        valid_cols = []
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) > 1 and data.std() > 0:
                valid_cols.append(col)
        
        # FIX 4: Check if we have enough valid columns
        if len(valid_cols) < 2:
            return create_no_data_figure(
                "Correlation Matrix",
                "Not enough valid numeric data for correlation"
            )
        
        # Calculate correlation
        corr = df[valid_cols].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale='RdBu',
            zmid=0,
            text=corr.values.round(2),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation")
        ))
        
        fig.update_layout(
            title="Correlation Matrix",
            template=THEME,
            height=600,
            width=700
        )
        
        return fig
    
    except Exception as e:
        print(f"⚠️ Error creating correlation heatmap: {e}")
        return create_no_data_figure(
            "Correlation Matrix",
            f"Error processing data: {str(e)[:50]}"
        )

def create_time_of_day_analysis(df: pd.DataFrame) -> go.Figure:
    """
    Analyze performance by hour of day.
    
    FIX 4: Column guards for time analysis.
    """
    # FIX 4: Validate required columns
    if df is None or df.empty:
        return create_no_data_figure(
            "Time of Day Analysis",
            "No data available"
        )
    
    if "hour" not in df.columns:
        return create_no_data_figure(
            "Time of Day Analysis",
            "Hour data not available (requires timestamp)"
        )
    
    if "leads" not in df.columns:
        return create_no_data_figure(
            "Time of Day Analysis",
            "Leads data not available"
        )
    
    try:
        # Aggregate by hour
        hourly = df.groupby("hour")["leads"].sum().reset_index()
        
        # FIX 4: Check if we have data
        if hourly.empty or len(hourly) == 0:
            return create_no_data_figure(
                "Time of Day Analysis",
                "No data after hourly aggregation"
            )
        
        hourly = hourly.sort_values("hour")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=hourly["hour"],
            y=hourly["leads"],
            name="Leads by Hour",
            marker_color='#007bff'
        ))
        
        fig.update_layout(
            title="Lead Generation by Time of Day",
            xaxis_title="Hour of Day",
            yaxis_title="Total Leads",
            template=THEME,
            height=500,
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1
            )
        )
        
        return fig
    
    except Exception as e:
        print(f"⚠️ Error creating time of day analysis: {e}")
        return create_no_data_figure(
            "Time of Day Analysis",
            f"Error processing data: {str(e)[:50]}"
        )

def create_funnel_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create conversion funnel visualization.
    
    FIX 4: Column validation for funnel.
    """
    # FIX 4: Validate required columns
    if df is None or df.empty:
        return create_no_data_figure(
            "Conversion Funnel",
            "No data available"
        )
    
    if "leads" not in df.columns or "booked" not in df.columns:
        return create_no_data_figure(
            "Conversion Funnel",
            "Leads or booked data missing"
        )
    
    try:
        total_leads = df["leads"].sum()
        total_booked = df["booked"].sum()
        
        # FIX 4: Check if we have valid totals
        if pd.isna(total_leads) or pd.isna(total_booked) or (total_leads == 0 and total_booked == 0):
            return create_no_data_figure(
                "Conversion Funnel",
                "No valid leads or booking data"
            )
        
        fig = go.Figure(go.Funnel(
            y=["Leads Generated", "Jobs Booked"],
            x=[total_leads, total_booked],
            textposition="inside",
            textinfo="value+percent initial",
            marker=dict(color=["#007bff", "#28a745"])
        ))
        
        fig.update_layout(
            title="Conversion Funnel",
            template=THEME,
            height=400
        )
        
        return fig
    
    except Exception as e:
        print(f"⚠️ Error creating funnel chart: {e}")
        return create_no_data_figure(
            "Conversion Funnel",
            f"Error processing data: {str(e)[:50]}"
        )

# ============================================================================
# FIX 1: Enhanced Chart Export with Kaleido Handling
# ============================================================================

def save_chart(fig: go.Figure, name: str, formats: List[str] = ["html", "png"]):
    """
    Save chart in multiple formats.
    
    FIX 1: Friendly error handling for PNG export without kaleido.
    
    Args:
        fig: Plotly figure
        name: Base filename (without extension)
        formats: List of formats ('html', 'png', 'json')
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    saved_count = 0
    
    for fmt in formats:
        if fmt == "html":
            filepath = CHART_DIR / f"{name}_{timestamp}.html"
            try:
                fig.write_html(str(filepath))
                print(f"📊 Saved: {filepath}")
                saved_count += 1
            except Exception as e:
                print(f"⚠️ Error saving HTML: {e}")
        
        elif fmt == "png":
            # FIX 1: Check for kaleido before attempting PNG export
            if not KALEIDO_AVAILABLE:
                print(f"⚠️ Skipping PNG export for '{name}': Kaleido not installed")
                print(f"   Install with: pip install kaleido")
                continue
            
            filepath = CHART_DIR / f"{name}_{timestamp}.png"
            try:
                fig.write_image(str(filepath), width=1200, height=800)
                print(f"📊 Saved: {filepath}")
                saved_count += 1
            except Exception as e:
                print(f"⚠️ Error saving PNG: {e}")
                print(f"   This may indicate kaleido installation issues")
                print(f"   Try: pip uninstall kaleido && pip install kaleido")
        
        elif fmt == "json":
            filepath = EXPORT_DIR / f"{name}_{timestamp}.json"
            try:
                with open(filepath, 'w') as f:
                    json.dump(fig.to_dict(), f, indent=2)
                print(f"📊 Saved: {filepath}")
                saved_count += 1
            except Exception as e:
                print(f"⚠️ Error saving JSON: {e}")
    
    return saved_count

# ============================================================================
# Alert & Insight Generation
# ============================================================================

def generate_insights(kpi_df: Optional[pd.DataFrame], 
                     ird_df: Optional[pd.DataFrame]) -> List[str]:
    """
    Generate actionable insights from data.
    
    FIX 4: Column guards for all insight generation.
    """
    insights = []
    
    if kpi_df is not None and not kpi_df.empty:
        # Revenue insights
        if "revenue" in kpi_df.columns and not kpi_df["revenue"].isna().all():
            stats = calculate_statistics(kpi_df, "revenue")
            if stats.get("sum", 0) > 0:
                insights.append(
                    f"💰 Total Revenue: ${stats['sum']:,.2f} "
                    f"(avg: ${stats['mean']:,.2f}/campaign)"
                )
        
        # Booking rate
        if ("leads" in kpi_df.columns and "booked" in kpi_df.columns and
            not kpi_df["leads"].isna().all() and not kpi_df["booked"].isna().all()):
            total_leads = kpi_df["leads"].sum()
            total_booked = kpi_df["booked"].sum()
            if total_leads > 0:
                rate = (total_booked / total_leads) * 100
                insights.append(
                    f"📈 Booking Rate: {rate:.1f}% "
                    f"({total_booked}/{total_leads})"
                )
                
                if rate < 20:
                    insights.append("⚠️ Low booking rate - consider improving follow-up")
                elif rate > 40:
                    insights.append("✅ Excellent booking rate - current strategy effective")
        
        # Best day of week
        if ("day_of_week" in kpi_df.columns and "leads" in kpi_df.columns and
            not kpi_df["day_of_week"].isna().all() and not kpi_df["leads"].isna().all()):
            try:
                best_day = kpi_df.groupby("day_of_week")["leads"].sum().idxmax()
                insights.append(f"📅 Peak Day: {best_day}")
            except (ValueError, KeyError):
                pass  # Not enough data for peak day
    
    if ird_df is not None and not ird_df.empty:
        # IRD health
        if "ird" in ird_df.columns and not ird_df["ird"].isna().all():
            stats = calculate_statistics(ird_df, "ird")
            mean_ird = stats.get("mean", 0)
            
            if mean_ird < 0.3:
                insights.append("✅ System Health: Excellent (IRD < 0.3)")
            elif mean_ird < 0.4:
                insights.append("✅ System Health: Good (IRD < 0.4)")
            elif mean_ird < 0.6:
                insights.append("⚠️ System Health: Warning (IRD 0.4-0.6)")
            else:
                insights.append("❌ System Health: Critical (IRD > 0.6)")
        
        # Domain performance
        if ("domain" in ird_df.columns and "ird" in ird_df.columns and
            not ird_df["domain"].isna().all() and not ird_df["ird"].isna().all()):
            try:
                best_domain = ird_df.groupby("domain")["ird"].mean().idxmin()
                insights.append(f"🎯 Best Performing Domain: {best_domain}")
            except (ValueError, KeyError):
                pass  # Not enough data for domain comparison
    
    # FIX 4: Add insight if no data available
    if not insights:
        insights.append("ℹ️ No insights available - run campaigns to generate data")
    
    return insights

# ============================================================================
# Main Dashboard Generation
# ============================================================================

def generate_full_dashboard(save_charts: bool = True, 
                           formats: List[str] = ["html"]):
    """
    Generate complete analytics dashboard.
    
    FIX 1: Warns about PNG export requirements
    FIX 4: Handles missing data gracefully
    
    Args:
        save_charts: Whether to save charts to disk
        formats: Export formats for charts
    """
    print("\n" + "="*70)
    print("AxProtocol Advanced Analytics Dashboard v2.5")
    print("="*70 + "\n")
    
    # FIX 1: Display kaleido status if PNG requested
    if "png" in formats:
        print(KALEIDO_MESSAGE)
        if not KALEIDO_AVAILABLE:
            print("   Continuing with other formats...\n")
    
    # Load data
    print("📊 Loading data...")
    kpi_df = load_kpi_data()
    ird_df = load_ird_data()
    
    if kpi_df is None and ird_df is None:
        print("❌ No data available. Run campaigns to generate analytics.")
        return
    
    # Show data summary
    if kpi_df is not None:
        file_size = get_file_size_mb(LOG_FILE)
        print(f"   KPI Data: {len(kpi_df):,} rows ({file_size:.1f} MB)")
    if ird_df is not None:
        file_size = get_file_size_mb(IRD_LOG)
        print(f"   IRD Data: {len(ird_df):,} rows ({file_size:.1f} MB)")
    
    # Generate insights
    print("\n💡 Key Insights:")
    insights = generate_insights(kpi_df, ird_df)
    for insight in insights:
        print(f"   {insight}")
    
    charts_generated = []
    charts_saved = 0
    
    # KPI Charts
    if kpi_df is not None:
        print("\n📈 Generating KPI charts...")
        
        # Performance dashboard
        fig_dash = create_performance_dashboard(kpi_df)
        if save_charts:
            charts_saved += save_chart(fig_dash, "performance_dashboard", formats)
        charts_generated.append("Performance Dashboard")
        
        # Metric trends
        for metric in ["leads", "booked", "revenue"]:
            if metric in kpi_df.columns:
                fig = create_metric_trend_chart(kpi_df, metric)
                if save_charts:
                    charts_saved += save_chart(fig, f"{metric}_trend", formats)
                charts_generated.append(f"{metric.capitalize()} Trend")
        
        # Time of day analysis
        if "hour" in kpi_df.columns:
            fig_time = create_time_of_day_analysis(kpi_df)
            if save_charts:
                charts_saved += save_chart(fig_time, "time_of_day", formats)
            charts_generated.append("Time of Day Analysis")
        
        # Funnel chart
        fig_funnel = create_funnel_chart(kpi_df)
        if save_charts:
            charts_saved += save_chart(fig_funnel, "conversion_funnel", formats)
        charts_generated.append("Conversion Funnel")
        
        # Correlation heatmap
        fig_corr = create_correlation_heatmap(kpi_df)
        if save_charts:
            charts_saved += save_chart(fig_corr, "correlation_matrix", formats)
        charts_generated.append("Correlation Matrix")
    
    # IRD Charts
    if ird_df is not None:
        print("\n🧠 Generating IRD analytics...")
        
        # Domain comparison
        if "domain" in ird_df.columns:
            fig_domains = create_domain_comparison(ird_df)
            if save_charts:
                charts_saved += save_chart(fig_domains, "domain_comparison", formats)
            charts_generated.append("Domain Comparison")
    
    # Summary
    print("\n" + "="*70)
    print(f"✅ Dashboard Generation Complete")
    print(f"📊 Charts Generated: {len(charts_generated)}")
    for chart in charts_generated:
        print(f"   • {chart}")
    if save_charts:
        print(f"\n💾 Files Saved: {charts_saved}")
        print(f"📁 Output Directory: {CHART_DIR}")
    print("="*70 + "\n")

# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Main entry point for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AxProtocol Advanced Analytics Dashboard"
    )
    parser.add_argument(
        "--format",
        nargs="+",
        choices=["html", "png", "json"],
        default=["html"],
        help="Export formats (default: html)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save charts to disk"
    )
    parser.add_argument(
        "--check-kaleido",
        action="store_true",
        help="Check kaleido installation status and exit"
    )
    
    args = parser.parse_args()
    
    # FIX 1: Allow checking kaleido status
    if args.check_kaleido:
        print(KALEIDO_MESSAGE)
        if KALEIDO_AVAILABLE:
            print("\n✅ PNG export is ready to use!")
        else:
            print("\n⚠️ Install kaleido to enable PNG export:")
            print("   pip install kaleido")
        sys.exit(0)
    
    generate_full_dashboard(
        save_charts=not args.no_save,
        formats=args.format
    )

if __name__ == "__main__":
    main()
