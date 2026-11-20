import time
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import integrity.integrity_monitor as monitor


def make_message(sequence=1, session="audit_session"):
    return {
        "schema_version": "1.0",
        "source_id": "audit_camera",
        "session_id": session,
        "sequence_number": sequence,
        "capture_timestamp_ms": int(time.time() * 1000),
        "detection_count": 1,
        "detections": [
            {
                "class": "person",
                "confidence": 0.94,
                "bbox": [120, 80, 250, 400]
            }
        ]
    }


class IntegrityValidatorAudit(unittest.TestCase):

    def setUp(self):
        monitor.last_sequence = None
        monitor.last_session = None

        for key in monitor.statistics:
            monitor.statistics[key] = 0

    def test_01_valid_person_message(self):
        faults = monitor.validate_message(make_message())
        self.assertEqual(faults, [])

    def test_02_valid_car_message(self):
        message = make_message()
        message["detections"][0]["class"] = "car"

        faults = monitor.validate_message(message)
        self.assertEqual(faults, [])

    def test_03_stale_timestamp(self):
        message = make_message()
        message["capture_timestamp_ms"] -= 2000

        faults = monitor.validate_message(message)
        self.assertIn("Stale message", faults)

    def test_04_future_timestamp(self):
        message = make_message()
        message["capture_timestamp_ms"] += 2000

        faults = monitor.validate_message(message)
        self.assertIn("Future timestamp", faults)

    def test_05_duplicate_sequence(self):
        first = make_message(sequence=1)
        second = make_message(sequence=1)

        monitor.validate_message(first)
        faults = monitor.validate_message(second)

        self.assertIn("Duplicate message", faults)

    def test_06_missing_sequence(self):
        first = make_message(sequence=1)
        second = make_message(sequence=3)

        monitor.validate_message(first)
        faults = monitor.validate_message(second)

        self.assertTrue(
            any("Sequence gap" in fault for fault in faults)
        )

    def test_07_out_of_order_sequence(self):
        first = make_message(sequence=2)
        second = make_message(sequence=1)

        monitor.validate_message(first)
        faults = monitor.validate_message(second)

        self.assertIn("Out-of-order message", faults)

    def test_08_invalid_confidence(self):
        message = make_message()
        message["detections"][0]["confidence"] = 1.5

        faults = monitor.validate_message(message)
        self.assertIn("Invalid confidence", faults)

    def test_09_invalid_bounding_box(self):
        message = make_message()
        message["detections"][0]["bbox"] = [120, 80, 250]

        faults = monitor.validate_message(message)
        self.assertIn("Invalid bounding box", faults)

    def test_10_detection_count_mismatch(self):
        message = make_message()
        message["detection_count"] = 2

        faults = monitor.validate_message(message)
        self.assertIn("Detection count mismatch", faults)

    def test_11_missing_required_field(self):
        message = make_message()
        del message["source_id"]

        faults = monitor.validate_message(message)

        self.assertIn("Missing field: source_id", faults)

    def test_12_malformed_message(self):
        faults = monitor.validate_message("not a dictionary")

        self.assertIn("Malformed message", faults)

    def test_13_invalid_source_id(self):
        message = make_message()
        message["source_id"] = ""

        faults = monitor.validate_message(message)
        self.assertIn("Invalid source ID", faults)

    def test_14_unsupported_schema_version_limitation(self):
        message = make_message()
        message["schema_version"] = "99.0"

        faults = monitor.validate_message(message)

        self.assertIn("Unsupported schema version", faults)

    def test_16_unsupported_schema_updates_invalid_statistics(self):
        message = make_message()
        message["schema_version"] = "99.0"

        faults = monitor.validate_message(message)
        monitor.update_statistics(faults)

        self.assertEqual(monitor.statistics["invalid_messages"], 1)

    def test_15_invalid_message_does_not_advance_sequence(self):
        first = make_message(sequence=1)
        monitor.validate_message(first)

        invalid = make_message(sequence=2)
        invalid["detections"][0]["confidence"] = 1.5

        faults = monitor.validate_message(invalid)
        self.assertIn("Invalid confidence", faults)

        third = make_message(sequence=3)
        faults = monitor.validate_message(third)

        self.assertTrue(
            any("Sequence gap: 1" in fault for fault in faults)
        )

    def test_17_valid_sequence_gap_resynchronizes_tracking(self):
        first = make_message(sequence=1)
        monitor.validate_message(first)

        third = make_message(sequence=3)
        faults = monitor.validate_message(third)

        self.assertTrue(
            any("Sequence gap: 1" in fault for fault in faults)
        )

        fourth = make_message(sequence=4)
        faults = monitor.validate_message(fourth)

        self.assertEqual(faults, [])


if __name__ == "__main__":
    print("\nINTEGRITY VALIDATOR INDEPENDENT AUDIT")
    print("=" * 55)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        IntegrityValidatorAudit
    )

    result = unittest.TextTestRunner(verbosity=2).run(suite)

    print("\nAUDIT SUMMARY")
    print("=" * 55)
    print("Total tests :", result.testsRun)
    print("Passed      :", result.testsRun - len(result.failures) - len(result.errors))
    print("Failed      :", len(result.failures))
    print("Errors      :", len(result.errors))

    if result.wasSuccessful():
        print("\nAUDIT EXECUTION: SUCCESS")
    else:
        print("\nAUDIT EXECUTION: ISSUES FOUND")
