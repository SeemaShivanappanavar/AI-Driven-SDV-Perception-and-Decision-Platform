import json
import time
import copy
import csv
import uuid
import sys
import math
import statistics

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from integrity import integrity_monitor
from decision.baseline_decision_module import make_baseline_decision
from decision.decision_module import make_decision


DATASET_FILE = PROJECT_ROOT / "evaluation" / "test_dataset.json"

RAW_OUTPUT = (
    PROJECT_ROOT / "evaluation" / "latency_benchmark_raw.csv"
)

SUMMARY_OUTPUT = (
    PROJECT_ROOT / "evaluation" / "latency_benchmark_summary.csv"
)

WARMUP_REPETITIONS = 5
MEASURED_REPETITIONS = 30


def reset_monitor(session_id):
    """Reset integrity-monitor state for an independent repetition."""

    integrity_monitor.last_sequence = None
    integrity_monitor.last_session = session_id

    for key in integrity_monitor.statistics:
        integrity_monitor.statistics[key] = 0


def prepare_message(template, session_id, sequence, age_offset_ms=0):
    """Create a fresh message while preserving the scenario template."""

    message = copy.deepcopy(template)

    message["session_id"] = session_id
    message["sequence_number"] = sequence

    message["capture_timestamp_ms"] = (
        int(time.time() * 1000) - age_offset_ms
    )

    return message


def get_scenarios():
    return [
        ("T01", "normal_no_person", [(1, 0)]),
        ("T02", "normal_person", [(1, 0)]),
        ("T03", "stale", [(1, 2000)]),
        ("T04", "duplicate", [(1, 0), (1, 0)]),
        ("T05", "missing_sequence", [(1, 0), (3, 0)]),
        ("T06", "out_of_order", [(2, 0), (1, 0)]),
        ("T07", "invalid_confidence", [(1, 0)])
    ]


def run_repetition(
    test_id,
    scenario,
    events,
    template,
    repetition,
    collect_measurements,
    raw_results
):
    """Run one complete scenario with a fresh monitor session."""

    session_id = str(uuid.uuid4())
    reset_monitor(session_id)

    for index, (sequence, age_offset) in enumerate(events):

        message = prepare_message(
            template,
            session_id,
            sequence,
            age_offset
        )

        event_id = (
            test_id
            if len(events) == 1
            else f"{test_id}_{index + 1}"
        )

        # --------------------------------------
        # Baseline decision timing
        # --------------------------------------

        baseline_start = time.perf_counter_ns()

        baseline_decision, _ = make_baseline_decision(message)

        baseline_end = time.perf_counter_ns()

        baseline_latency_ms = (
            baseline_end - baseline_start
        ) / 1_000_000

        # --------------------------------------
        # Proposed integrity-aware timing
        # --------------------------------------

        proposed_start = time.perf_counter_ns()

        faults = integrity_monitor.validate_message(message)

        integrity_status = "FAULT" if faults else "VALID"

        integrity_data = {
            "integrity_status": integrity_status
        }

        proposed_decision, _ = make_decision(
            message,
            integrity_data
        )

        proposed_end = time.perf_counter_ns()

        proposed_latency_ms = (
            proposed_end - proposed_start
        ) / 1_000_000

        if collect_measurements:

            raw_results.append({
                "repetition": repetition,
                "test_id": test_id,
                "event_id": event_id,
                "scenario": scenario,
                "sequence_number": sequence,
                "integrity_status": integrity_status,
                "detected_faults": "; ".join(faults),
                "baseline_decision": baseline_decision,
                "proposed_decision": proposed_decision,
                "baseline_latency_ms": baseline_latency_ms,
                "proposed_latency_ms": proposed_latency_ms
            })


def percentile(values, percentage):
    """Calculate a percentile using the nearest-rank method."""

    ordered = sorted(values)

    if not ordered:
        return 0.0

    rank = math.ceil((percentage / 100) * len(ordered))
    return ordered[max(0, rank - 1)]


def calculate_summary(raw_results):

    summary_rows = []

    groups = {}

    for row in raw_results:

        scenario = row["scenario"]

        groups.setdefault(
            scenario,
            {"baseline": [], "proposed": []}
        )

        groups[scenario]["baseline"].append(
            row["baseline_latency_ms"]
        )

        groups[scenario]["proposed"].append(
            row["proposed_latency_ms"]
        )

    # Add scenario-wise and overall statistics.
    groups["OVERALL"] = {
        "baseline": [
            row["baseline_latency_ms"] for row in raw_results
        ],
        "proposed": [
            row["proposed_latency_ms"] for row in raw_results
        ]
    }

    for scenario, pipelines in groups.items():

        for pipeline, values in pipelines.items():

            summary_rows.append({
                "scenario": scenario,
                "pipeline": pipeline,
                "sample_count": len(values),
                "mean_ms": statistics.mean(values),
                "median_ms": statistics.median(values),
                "minimum_ms": min(values),
                "maximum_ms": max(values),
                "standard_deviation_ms": (
                    statistics.stdev(values) if len(values) > 1 else 0
                ),
                "p95_ms": percentile(values, 95)
            })

    return summary_rows


def main():

    print("\nREPEATED LATENCY BENCHMARK")
    print("=" * 65)

    dataset = json.loads(
        DATASET_FILE.read_text(encoding="utf-8")
    )

    cases = {
        item["test_id"]: item
        for item in dataset
    }

    scenarios = get_scenarios()

    raw_results = []

    total_messages = sum(
        len(events) for _, _, events in scenarios
    )

    print("Scenarios:", len(scenarios))
    print("Messages per complete run:", total_messages)
    print("Warm-up repetitions:", WARMUP_REPETITIONS)
    print("Measured repetitions:", MEASURED_REPETITIONS)
    print("YOLO execution: Not required")
    print("KUKSA connection: Not required")
    print("=" * 65)

    # ------------------------------------------
    # Warm-up: measurements are discarded
    # ------------------------------------------

    print("\nRunning warm-up repetitions...")

    for repetition in range(1, WARMUP_REPETITIONS + 1):

        for test_id, scenario, events in scenarios:

            run_repetition(
                test_id,
                scenario,
                events,
                cases[test_id],
                repetition,
                False,
                raw_results
            )

    print("Warm-up completed.")

    # ------------------------------------------
    # Measured repetitions
    # ------------------------------------------

    print("\nRunning measured repetitions...")

    for repetition in range(1, MEASURED_REPETITIONS + 1):

        for test_id, scenario, events in scenarios:

            run_repetition(
                test_id,
                scenario,
                events,
                cases[test_id],
                repetition,
                True,
                raw_results
            )

        print(
            f"Completed repetition "
            f"{repetition}/{MEASURED_REPETITIONS}"
        )

    # ------------------------------------------
    # Save raw measurements
    # ------------------------------------------

    if raw_results:

        with open(
            RAW_OUTPUT,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=raw_results[0].keys()
            )

            writer.writeheader()
            writer.writerows(raw_results)

    # ------------------------------------------
    # Calculate and save summary
    # ------------------------------------------

    summary_rows = calculate_summary(raw_results)

    with open(
        SUMMARY_OUTPUT,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=summary_rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(summary_rows)

    # ------------------------------------------
    # Display overall results
    # ------------------------------------------

    print("\n" + "=" * 65)
    print("OVERALL LATENCY RESULTS")
    print("=" * 65)

    for row in summary_rows:

        if row["scenario"] == "OVERALL":

            print("\nPipeline:", row["pipeline"])
            print("Samples:", row["sample_count"])
            print("Mean:", round(row["mean_ms"], 6), "ms")
            print("Median:", round(row["median_ms"], 6), "ms")
            print("Minimum:", round(row["minimum_ms"], 6), "ms")
            print("Maximum:", round(row["maximum_ms"], 6), "ms")
            print(
                "Standard deviation:",
                round(row["standard_deviation_ms"], 6),
                "ms"
            )
            print("P95:", round(row["p95_ms"], 6), "ms")

    print("\nBenchmark completed successfully.")
    print("\nRaw measurements:")
    print(RAW_OUTPUT)

    print("\nSummary:")
    print(SUMMARY_OUTPUT)

    print(
        "\nNote: These measurements cover local decision-processing "
        "functions only. They exclude KUKSA communication, message "
        "pairing, publication, database operations and dashboard rendering."
    )


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        print("\nBenchmark interrupted.")
