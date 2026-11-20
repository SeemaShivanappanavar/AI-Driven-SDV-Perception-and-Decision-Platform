import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "evaluation"
OUT = ROOT / "research_results" / "figures"

summary = pd.read_csv(DATA / "latency_benchmark_summary.csv")

# 1. Overall mean latency
overall = summary[summary["scenario"] == "OVERALL"]

plt.figure(figsize=(8, 5))
plt.bar(overall["pipeline"], overall["mean_ms"])
plt.ylabel("Mean latency (ms)")
plt.title("Overall Mean Decision-Processing Latency")
plt.tight_layout()
plt.savefig(OUT / "01_overall_mean_latency.png", dpi=300)
plt.close()

# 2. Overall P95 latency
plt.figure(figsize=(8, 5))
plt.bar(overall["pipeline"], overall["p95_ms"])
plt.ylabel("P95 latency (ms)")
plt.title("Overall P95 Decision-Processing Latency")
plt.tight_layout()
plt.savefig(OUT / "02_overall_p95_latency.png", dpi=300)
plt.close()

# 3. Scenario-wise mean latency
scenario_data = summary[summary["scenario"] != "OVERALL"]

pivot = scenario_data.pivot(
    index="scenario",
    columns="pipeline",
    values="mean_ms"
)

pivot.plot(kind="bar", figsize=(11, 6))
plt.ylabel("Mean latency (ms)")
plt.xlabel("Test scenario")
plt.title("Scenario-wise Baseline vs Proposed Latency")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(OUT / "03_scenario_wise_latency.png", dpi=300)
plt.close()

print("LATENCY GRAPHS GENERATED")
for file in sorted(OUT.glob("*.png")):
    print(file.name)
