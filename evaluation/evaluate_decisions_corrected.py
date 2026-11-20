import json
import time
import copy
import csv
import uuid
import sys

from pathlib import Path

# Add project root to Python import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from integrity import integrity_monitor
from decision.baseline_decision_module import make_baseline_decision
from decision.decision_module import make_decision


DATASET_FILE = Path("evaluation/test_dataset.json")

OUTPUT_FILE = Path(
    "evaluation/evaluation_results_corrected.csv"
)


def reset_monitor(session_id):
    """Reset integrity state before an independent scenario."""

    integrity_monitor.last_sequence = None
    integrity_monitor.last_session = session_id

    for key in integrity_monitor.statistics:
        integrity_monitor.statistics[key] = 0


def prepare_message(template, session_id, sequence, age_offset_ms=0):

    message = copy.deepcopy(template)

    message["session_id"] = session_id
    message["sequence_number"] = sequence

    # Generate a fresh timestamp for the experiment.
    message["capture_timestamp_ms"] = (
        int(time.time() * 1000) - age_offset_ms
    )

    return message


def evaluate_message(
    message,
    test_id,
    scenario,
    injected_fault
):

    # ==========================================
    # BASELINE DECISION
    # ==========================================

    baseline_start = time.perf_counter()

    baseline_decision, baseline_reason = (
        make_baseline_decision(message)
    )

    baseline_latency = (
        time.perf_counter() - baseline_start
    ) * 1000

    # ==========================================
    # PROPOSED INTEGRITY-AWARE DECISION
    # ==========================================

    proposed_start = time.perf_counter()

    faults = integrity_monitor.validate_message(message)

    integrity_status = (
        "FAULT" if faults else "VALID"
    )

    integrity_data = {
        "integrity_status": integrity_status
    }

    proposed_decision, proposed_reason = make_decision(
        message,
        integrity_data
    )

    proposed_latency = (
        time.perf_counter() - proposed_start
    ) * 1000

    # ==========================================
    # DISPLAY RESULTS
    # ==========================================

    print("\n" + "=" * 65)
    print("TEST ID:", test_id)
    print("SCENARIO:", scenario)
    print("SEQUENCE:", message["sequence_number"])
    print("INJECTED FAULT:", injected_fault)
    print("DETECTED STATUS:", integrity_status)
    print("DETECTED FAULTS:", faults)
    print("BASELINE DECISION:", baseline_decision)
    print("PROPOSED DECISION:", proposed_decision)
    print(
        "BASELINE LATENCY:",
        round(baseline_latency, 4),
        "ms"
    )
    print(
        "PROPOSED LATENCY:",
        round(proposed_latency, 4),
        "ms"
    )
    print("=" * 65)

    return {
        "test_id": test_id,
        "scenario": scenario,
        "session_id": message["session_id"],
        "sequence_number": message["sequence_number"],

        # Independent ground truth
        "injected_fault": injected_fault,

        # Actual integrity monitor output
        "integrity_status": integrity_status,
        "faults": "; ".join(faults),

        "baseline_decision": baseline_decision,
        "proposed_decision": proposed_decision,

        "baseline_latency_ms": round(
            baseline_latency, 4
        ),

        "proposed_latency_ms": round(
            proposed_latency, 4
        )
    }


def calculate_metrics(results):

    tp = fp = fn = tn = 0

    for result in results:

        actual_fault = result["injected_fault"]
        detected_fault = (
            result["integrity_status"] == "FAULT"
        )

        if actual_fault and detected_fault:
            tp += 1

        elif not actual_fault and detected_fault:
            fp += 1

        elif actual_fault and not detected_fault:
            fn += 1

        else:
            tn += 1

    total = len(results)

    precision = (
        tp / (tp + fp) * 100
        if tp + fp else 0
    )

    recall = (
        tp / (tp + fn) * 100
        if tp + fn else 0
    )

    false_positive_rate = (
        fp / (fp + tn) * 100
        if fp + tn else 0
    )

    accuracy = (
        (tp + tn) / total * 100
        if total else 0
    )

    print("\n\nINDEPENDENT FAULT-DETECTION EVALUATION")
    print("=" * 60)

    print("Total messages:", total)
    print("True Positives:", tp)
    print("False Positives:", fp)
    print("False Negatives:", fn)
    print("True Negatives:", tn)

    print("\nPrecision:", round(precision, 2), "%")
    print("Recall / Detection Rate:", round(recall, 2), "%")
    print("False Positive Rate:", round(false_positive_rate, 2), "%")
    print("Accuracy:", round(accuracy, 2), "%")

    print("\nNOTE:")
    print(
        "Ground truth comes from the dataset's expected_fault "
        "field and the defined fault-injection sequence."
    )

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "precision": precision,
        "recall": recall,
        "false_positive_rate": false_positive_rate,
        "accuracy": accuracy
    }


def main():

    print("\nCORRECTED CONTROLLED EVALUATION")
    print("=" * 65)

    dataset = json.loads(
        DATASET_FILE.read_text(encoding="utf-8")
    )

    cases = {
        item["test_id"]: item
        for item in dataset
    }

    results = []

    scenarios = [

        ("T01", "normal_no_person", [(1, 0)]),

        ("T02", "normal_person", [(1, 0)]),

        ("T03", "stale", [(1, 2000)]),

        ("T04", "duplicate", [(1, 0), (1, 0)]),

        ("T05", "missing_sequence", [(1, 0), (3, 0)]),

        ("T06", "out_of_order", [(2, 0), (1, 0)]),

        ("T07", "invalid_confidence", [(1, 0)])
    ]

    for test_id, scenario, events in scenarios:

        session_id = str(uuid.uuid4())

        reset_monitor(session_id)

        template = cases[test_id]

        for index, (sequence, age_offset) in enumerate(events):

            message = prepare_message(
                template,
                session_id,
                sequence,
                age_offset
            )

            if len(events) == 1:

                injected_fault = bool(
                    template.get("expected_fault", False)
                )

            else:

                # First message establishes the sequence state.
                # Second message introduces the injected fault.
                injected_fault = (
                    bool(template.get("expected_fault", False))
                    and index > 0
                )

            event_id = (
                test_id
                if len(events) == 1
                else f"{test_id}_{index + 1}"
            )

            result = evaluate_message(
                message,
                event_id,
                scenario,
                injected_fault
            )

            results.append(result)

    # ==========================================
    # SAVE CORRECTED RESULTS
    # ==========================================

    if results:

        with open(
            OUTPUT_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=results[0].keys()
            )

            writer.writeheader()
            writer.writerows(results)

    # ==========================================
    # INDEPENDENT METRICS
    # ==========================================

    calculate_metrics(results)

    print("\nCorrected results saved to:")
    print(OUTPUT_FILE)

    print("\nOriginal evaluation files were not modified.")


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        print("\nEvaluation stopped.")
