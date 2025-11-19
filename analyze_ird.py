import pandas as pd
from pathlib import Path

# Define the path to your log file
LOG_FILE = Path(__file__).parent / "logs" / "ird_log.csv"

def analyze_ird_log(file_path: Path):
    """
    Loads and analyzes the IRD log file.
    """
    if not file_path.exists():
        print(f"Error: Log file not found at {file_path}")
        return

    try:
        # Load the CSV file into a pandas DataFrame
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        print(f"Log file is empty: {file_path}")
        return
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    print("--- AxProtocol TAES/IRD Analysis ---")
    print("\n")

    # 1. Overall Performance
    print(f"Total runs logged: {len(df)}")
    avg_ird = df['ird'].mean()
    avg_iv = df['iv'].mean()
    print(f"Average IRD (Truth-Gap): {avg_ird:.4f}")
    print(f"Average IV (Integrity):  {avg_iv:.4f}")

    # 2. High-Risk Runs (D25 Threshold Breach)
    high_ird_runs = df[df['ird'] > 0.5]
    print(f"Runs failing IRD check (IRD > 0.5): {len(high_ird_runs)} ({len(high_ird_runs) / len(df) * 100:.2f}%)")
    print("\n")

    # 3. Worst Performing Domains
    print("--- Worst Domains (by Avg. IRD) ---")
    domain_performance = df.groupby('domain')['ird'].mean().sort_values(ascending=False)
    print(domain_performance)
    print(f"-> Recommendation: Focus on improving prompts for '{domain_performance.idxmax()}'")
    print("\n")

    # 4. Worst Performing Roles
    print("--- Worst Roles (by Avg. IRD) ---")
    role_performance = df.groupby('role_name')['ird'].mean().sort_values(ascending=False)
    print(role_performance)
    print(f"-> Recommendation: Focus on improving prompts for '{role_performance.idxmax()}'")
    print("\n")

if __name__ == "__main__":
    analyze_ird_log(LOG_FILE)