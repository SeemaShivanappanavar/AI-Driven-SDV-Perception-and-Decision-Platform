import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "evaluation" / "evaluation_results_corrected.csv"
OUT = ROOT / "research_results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA)

# Ground truth and integrity-monitor prediction
actual = df["injected_fault"].astype(bool)
predicted = df["integrity_status"] == "FAULT"

TP = int((actual & predicted).sum())
TN = int((~actual & ~predicted).sum())
FP = int((~actual & predicted).sum())
FN = int((actual & ~predicted).sum())

matrix = [[TN, FP], [FN, TP]]

# 1. Fault-detection confusion matrix
fig, ax = plt.subplots(figsize=(7, 5))
ax.imshow(matrix)

ax.set_xticks([0, 1], labels=["Predicted VALID", "Predicted FAULT"])
ax.set_yticks([0, 1], labels=["Actual normal", "Actual fault"])
ax.set_xlabel("Integrity monitor prediction")
ax.set_ylabel("Ground truth")
ax.set_title("Integrity Fault Detection Confusion Matrix")

for i in range(2):
    for j in range(2):
        ax.text(j, i, str(matrix[i][j]),
                ha="center", va="center", fontsize=16)

plt.tight_layout()
plt.savefig(OUT / "04_fault_detection_confusion_matrix.png", dpi=300)
plt.close()

# 2. Baseline versus proposed decision counts
decision_counts = pd.DataFrame({
    "Baseline": df["baseline_decision"].value_counts(),
    "Proposed": df["proposed_decision"].value_counts()
}).fillna(0).reindex(["NORMAL", "ALERT", "CAUTION"], fill_value=0)

decision_counts.plot(kind="bar", figsize=(8, 5))
plt.ylabel("Number of messages")
plt.xlabel("Decision")
plt.title("Baseline vs Proposed Decision Distribution")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(OUT / "05_decision_distribution.png", dpi=300)
plt.close()

# 3. Scenario-wise decision comparison table
comparison = df[[
    "test_id",
    "scenario",
    "injected_fault",
    "integrity_status",
    "faults",
    "baseline_decision",
    "proposed_decision"
]]

comparison.to_csv(
    ROOT / "research_results" / "decision_comparison_table.csv",
    index=False
)

print("\nFAULT DETECTION RESULTS")
print("=======================")
print("True positives :", TP)
print("True negatives :", TN)
print("False positives:", FP)
print("False negatives:", FN)
print("Accuracy       :", round((TP + TN) / len(df) * 100, 2), "%")
print("Precision      :", round(TP / (TP + FP) * 100, 2), "%")
print("Recall         :", round(TP / (TP + FN) * 100, 2), "%")

print("\nDECISION COMPARISON")
print(decision_counts)

print("\nGenerated figures:")
for file in sorted(OUT.glob("0[45]_*.png")):
    print(file.name)

print("\nGenerated table:")
print(ROOT / "research_results" / "decision_comparison_table.csv")
