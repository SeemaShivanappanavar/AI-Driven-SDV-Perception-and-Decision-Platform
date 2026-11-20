import json
import time
import uuid
from pathlib import Path

OUTPUT_FILE = Path("evaluation/test_dataset.json")

session_id = str(uuid.uuid4())
current_time = int(time.time() * 1000)

person_detection = [{
    "class": "person",
    "confidence": 0.94,
    "bbox": [120, 80, 250, 400]
}]

car_detection = [{
    "class": "car",
    "confidence": 0.91,
    "bbox": [300, 150, 600, 420]
}]

test_cases = [
    {
        "test_id": "T01",
        "scenario": "normal_no_person",
        "sequence_number": 1,
        "timestamp_offset_ms": 0,
        "detections": car_detection,
        "expected_fault": False
    },
    {
        "test_id": "T02",
        "scenario": "normal_person",
        "sequence_number": 2,
        "timestamp_offset_ms": 0,
        "detections": person_detection,
        "expected_fault": False
    },
    {
        "test_id": "T03",
        "scenario": "stale",
        "sequence_number": 3,
        "timestamp_offset_ms": -2000,
        "detections": person_detection,
        "expected_fault": True
    },
    {
        "test_id": "T04",
        "scenario": "duplicate",
        "sequence_number": 3,
        "timestamp_offset_ms": 0,
        "detections": person_detection,
        "expected_fault": True
    },
    {
        "test_id": "T05",
        "scenario": "missing_sequence",
        "sequence_number": 5,
        "timestamp_offset_ms": 0,
        "detections": car_detection,
        "expected_fault": True
    },
    {
        "test_id": "T06",
        "scenario": "out_of_order",
        "sequence_number": 4,
        "timestamp_offset_ms": 0,
        "detections": person_detection,
        "expected_fault": True
    },
    {
        "test_id": "T07",
        "scenario": "invalid_confidence",
        "sequence_number": 6,
        "timestamp_offset_ms": 0,
        "detections": [{
            "class": "person",
            "confidence": 1.5,
            "bbox": [120, 80, 250, 400]
        }],
        "expected_fault": True
    }
]

messages = []

for case in test_cases:
    message = {
        "test_id": case["test_id"],
        "scenario": case["scenario"],
        "schema_version": 1,
        "source_id": "evaluation_dataset",
        "session_id": session_id,
        "sequence_number": case["sequence_number"],
        "capture_timestamp_ms": (
            current_time + case["timestamp_offset_ms"]
        ),
        "detection_count": len(case["detections"]),
        "detections": case["detections"],
        "expected_fault": case["expected_fault"]
    }

    messages.append(message)

OUTPUT_FILE.write_text(
    json.dumps(messages, indent=4)
)

print("Evaluation dataset generated successfully.")
print("Session ID:", session_id)
print("Total messages:", len(messages))
print("Output:", OUTPUT_FILE)
