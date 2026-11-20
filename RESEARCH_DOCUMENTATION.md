# RESEARCH DOCUMENTATION

# KUKSA-Based Data-Integrity-Aware Perception-to-Decision Framework for Software-Defined Vehicles

## 1. Abstract

This project develops a KUKSA-based perception-to-decision framework for Software-Defined Vehicles (SDVs). It integrates YOLO11n object perception, structured vehicle-data exchange, perception-message integrity validation and fault-aware decision-making.

The framework detects stale, duplicate, out-of-order, missing-sequence and invalid detection messages. Controlled experiments compare a baseline decision pipeline with the proposed integrity-aware pipeline. A Streamlit dashboard supports monitoring and experimental visualization.

The controlled evaluation detected all five injected faulty messages among ten test messages. The independent integrity-validator audit passed all 17 tests.

## 2. Problem Statement

Perception information is used by downstream vehicle functions to make decisions. However, perception messages exchanged through software platforms may be stale, duplicated, delayed, out of order or invalid.

Processing unreliable perception information without checking its integrity may lead to inappropriate downstream decisions.

This project investigates how message integrity validation can improve the handling of unreliable perception inputs in an SDV software architecture.

## 3. Objectives

1. Develop a software-based SDV perception-to-decision framework using Eclipse KUKSA Databroker.
2. Integrate YOLO11n object detection.
3. Define structured perception messages using a custom VSS signal.
4. Develop a perception-message integrity monitor.
5. Implement baseline and fault-aware decision modules.
6. Conduct controlled fault-injection experiments.
7. Evaluate integrity detection using independent ground-truth labels.
8. Measure repeated decision-processing latency.
9. Develop a dashboard for monitoring and analysis.

## 4. System Architecture

The system uses a distributed laptop–Raspberry Pi architecture.

1. The laptop webcam is captured and streamed through a Flask server on port 5001.
2. A Raspberry Pi 5 receives the MJPEG video stream over Wi-Fi.
3. YOLO11n performs CPU-based object detection on the Raspberry Pi using an input size of 320 pixels.
4. Structured perception messages are published to the Eclipse KUKSA Databroker hosted on the laptop (port 55555).
5. The integrity monitor and fault-aware decision module process perception messages on the Raspberry Pi.
6. Annotated video frames are served by a Flask video server on the Raspberry Pi (port 5002).
7. The laptop hosts the Streamlit dashboard and SQLite historical storage.

A separate baseline decision module is implemented for comparison.

The Streamlit dashboard provides live video monitoring, historical event inspection and research-result visualization.

The system architecture diagram is available at research_results/figures/06_system_architecture.png.

## 5. Implementation

### 5.1 Perception Module

YOLO11n performs object detection using camera input. Each detection contains an object class, confidence value and bounding-box coordinates. The resulting structured message is published through KUKSA.

### 5.2 KUKSA Data Platform

Eclipse KUKSA Databroker provides the vehicle-data exchange interface.

The custom VSS signal is Vehicle.Perception.FrameData.

The message contains:
- Schema version
- Source identifier
- Session identifier
- Sequence number
- Capture timestamp
- Detection count
- Object detections

Additional signals carry integrity and decision status.

### 5.3 Integrity Monitor

The integrity monitor validates:
- Required message fields
- Supported schema version
- Source and session identifiers
- Message freshness and future timestamps
- Duplicate sequence numbers
- Missing sequence numbers
- Out-of-order messages
- Detection-count consistency
- Detection class validity
- Confidence range
- Bounding-box validity

The maximum message age is configured as 500 ms, with a future timestamp tolerance of 1000 ms.

Invalid messages are marked faulty. Sequence tracking avoids advancing state when other validation checks fail. Valid sequence gaps are detected and the tracker resynchronizes.

### 5.4 Baseline Decision Module

The baseline module uses perception information without integrity-aware validation.

Decision policy:
- Person detected: ALERT
- No person detected: NORMAL

### 5.5 Proposed Decision Module

The proposed module considers perception information and integrity status.

Decision policy:
- Invalid or faulty perception: CAUTION
- Valid perception with a person detected: ALERT
- Valid perception without a person detected: NORMAL

This demonstrates fault-aware handling and does not claim certified vehicle safety.

### 5.6 Fault Injection

The experiments cover:
1. Stale messages
2. Duplicate messages
3. Out-of-order messages
4. Missing sequence numbers
5. Invalid confidence values
6. Delayed publication

Stale-message and delayed-publication experiments use different injection methods to examine message freshness.

### 5.7 Dashboard and Storage

The Streamlit dashboard provides:
- Live vehicle view
- Historical event exploration
- Research experiment results
- System architecture visualization
- Latency benchmark results
- CSV and JSON data export

SQLite is used for historical event storage. The dashboard supports monitoring and visualization rather than constituting the primary research contribution.

## 6. Experimental Methodology

### 6.1 Controlled Offline Evaluation

The controlled dataset contains seven scenario templates:
- Normal without person
- Normal with person
- Stale message
- Duplicate message
- Missing sequence
- Out-of-order message
- Invalid confidence

Each scenario has an independent expected_fault label. The evaluator compares this label with the integrity monitor result.

The evaluation contains ten message instances because duplicate, missing-sequence and out-of-order scenarios involve paired messages.

### 6.2 Repeated Latency Benchmark

The benchmark measures baseline and proposed decision-processing functions.

Configuration:
- Scenario templates: 7
- Warm-up repetitions: 5
- Measured repetitions: 30
- Measured messages: 300

Timing uses Python high-resolution performance-counter measurements.

The benchmark excludes YOLO execution, KUKSA communication, message pairing, publication, database operations and dashboard rendering. Running the benchmark again overwrites its raw and summary CSV output files; preserve the existing results before rerunning.

Therefore, the reported values represent local decision-processing function latency, not end-to-end system latency.

### 6.3 Independent Validator Audit

A separate unit-test audit checks message validation, timestamp faults, sequence faults, invalid confidence, invalid bounding boxes, malformed messages, missing fields and sequence-state handling.

## 7. Experimental Results

### 7.1 Integrity Detection

| Metric | Result |
|---|---:|
| Total messages | 10 |
| True Positives | 5 |
| False Positives | 0 |
| False Negatives | 0 |
| True Negatives | 5 |
| Precision | 100% |
| Recall | 100% |
| False Positive Rate | 0% |
| Accuracy | 100% |

All injected faults in this controlled dataset were detected, and all valid messages were classified as valid.

These results apply only to the controlled test dataset and should not be generalized to real-world conditions. The confusion matrix evaluates integrity fault detection, not final vehicle-decision correctness.

### 7.2 Decision-Processing Latency

Latest repeated benchmark results:

| Metric | Baseline | Proposed |
|---|---:|---:|
| Samples | 300 | 300 |
| Mean latency | 0.001111 ms | 0.007659 ms |
| Median latency | 0.001092 ms | 0.007865 ms |
| Minimum latency | 0.000902 ms | 0.005530 ms |
| Maximum latency | 0.001453 ms | 0.019096 ms |
| Standard deviation | 0.000112 ms | 0.001230 ms |
| P95 latency | 0.001343 ms | 0.008416 ms |

Additional mean processing time: approximately 0.006548 ms.

The proposed pipeline requires additional processing because it validates message integrity before producing a decision.

These are local Python function-level measurements, not ECU execution times or complete vehicle-system latency.

### 7.3 Independent Validator Audit

| Metric | Result |
|---|---:|
| Total tests | 17 |
| Passed | 17 |
| Failed | 0 |
| Errors | 0 |

All 17 validator audit tests passed.

### 7.4 Fault-Injection Experiment Logs

Six controlled fault-injection experiment logs are available. These logs are separate from the ten-message offline evaluation:
- Stale message
- Duplicate message
- Out-of-order message
- Missing sequence number
- Invalid confidence
- Delayed publication

The recorded experiments reported FAULT integrity status and CAUTION decision handling.

A missing sequence number represents a subscriber-observed sequence gap. It does not independently prove network packet loss.

### 7.5 Live Perception Performance

A single live operating session on the Raspberry Pi 5 produced the following measurements:

| Metric | Result |
|---|---:|
| Frames processed | 3514 |
| Mean perception latency | 87.44 ms |
| Median perception latency | 87.22 ms |
| P95 perception latency | 89.31 ms |
| Minimum latency | 85.48 ms |
| Maximum latency | 96.08 ms |
| Approximate processing rate | 9.53 FPS |
| Average detections per frame | 1.81 |

These measurements describe live perception performance for one session. They are separate from the offline decision-processing benchmark and do not represent complete end-to-end system latency.

## 8. Research Contribution

The central contribution is the integration of perception-message integrity validation with downstream decision-making in a KUKSA-based SDV software framework.

The framework:
- Validates perception-message structure and freshness.
- Detects sequence-related inconsistencies.
- Identifies invalid detection information.
- Uses integrity status to influence downstream decisions.
- Provides controlled fault injection and comparative evaluation.
- Supports historical monitoring and visualization.

The research focuses on data integrity and fault-aware decision handling rather than developing a new object-detection model.

## 9. Limitations

1. The controlled evaluation dataset is small.
2. Detection metrics do not establish general real-world performance.
3. Latency measurements cover local Python functions, not end-to-end communication.
4. The perception model runs on the Raspberry Pi 5 CPU.
5. No hardware ECU deployment has been performed.
6. No certified vehicle-safety validation has been performed.
7. Sequence gaps cannot independently establish the cause of missing messages.

## 10. Conclusion

This project developed a KUKSA-based perception-to-decision framework with integrity-aware decision handling for Software-Defined Vehicles.

The implementation combines object perception, vehicle-data exchange, integrity validation, decision-making, fault injection, experimental evaluation and dashboard visualization.

The controlled evaluation detected all injected faulty messages in the test dataset. The independent validator audit passed all 17 tests. The repeated benchmark quantified the additional local processing cost introduced by integrity validation.

The results demonstrate a software-based approach for incorporating perception-message integrity into SDV decision pipelines.

## 11. Reproducibility

The project contains source code, evaluation scripts, test data, benchmark CSV files, audit tests and live experiment logs.

The following offline experiments can be reproduced after activating the Python virtual environment:

1. python evaluation/evaluate_decisions_corrected.py
2. python evaluation/benchmark_latency.py
3. python evaluation/integrity_validator_audit.py

These offline experiments do not require YOLO or a running KUKSA broker.
