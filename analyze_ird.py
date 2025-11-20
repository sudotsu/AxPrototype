"""
AxProtocol IRD Analyzer v3.0

Analyzes the Truth-Reality Gap in AxPrototype sessions.
"""

import pandas as pd
from pathlib import Path
import sys

LOG_FILE = Path("logs/ird_log.csv")

def analyze():
    if not LOG_FILE.exists():
        print("[!] No IRD log found.")
        return

    try:
        df = pd.read_csv(LOG_FILE)
    except Exception as e:
        print(f"[!] Error reading log: {e}")
        return

    print("\n" + "="*50)
    print(" 🧠 AxPrototype Cognitive Health Report")
    print("="*50)

    # 1. Overall Health
    avg_iv = df['iv'].mean()
    avg_ird = df['ird'].mean()

    print(f"\n📊 Global Metrics ({len(df)} records)")
    print(f"   • Integrity (IV):  {avg_iv:.3f}  (Target > 0.8)")
    print(f"   • Delusion (IRD):  {avg_ird:.3f}  (Target < 0.3)")

    # 2. Role Breakdown (Builder vs Critic)
    if 'role' in df.columns:
        print("\n🎭 Role Performance")
        print(df.groupby('role')[['iv', 'ird']].mean())

    # 3. Recent Trend
    recent = df.tail(5)
    print("\n📉 Last 5 Runs")
    cols = [c for c in ['timestamp', 'role', 'iv', 'ird', 'verdict'] if c in df.columns]
    print(recent[cols])

    if avg_ird > 0.4:
        print("\n⚠️  WARNING: High IRD detected. The system is generating logical plans that fail practical checks.")

if __name__ == "__main__":
    analyze()