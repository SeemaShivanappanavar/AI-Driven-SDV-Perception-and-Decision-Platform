# Development of a Software-Defined Platform for AI-Driven Vehicle Perception and Decision-Making

## Project Information

- **Student:** Seema Shivanappanavar
- **Institution:** KLE Technological University, Hubballi
- **Department:** Electronics and Communication Engineering
- **Project Type:** Individual REU Research Project

## Problem Statement

Vehicle perception systems depend on reliable data to make downstream decisions. Delayed, stale, duplicated, out-of-order, or invalid perception messages can affect these decisions. This project develops a software-defined platform that monitors perception-data integrity and uses the integrity status to support fault-aware decision-making.

## Objectives

1. Develop camera-based object perception using a pretrained YOLO model.
2. Exchange perception data using Eclipse KUKSA Databroker and Vehicle Signal Specification (VSS).
3. Implement perception-message integrity monitoring.
4. Develop baseline and integrity-aware decision-making modules.
5. Evaluate system behaviour using controlled fault-injection experiments.
6. Develop a dashboard for live monitoring and historical data visualization.

## Team Members

This is an individual project.

- **Student:** Seema Shivanappanavar

## Technologies and Tools

- Python and Ubuntu Linux
- YOLO11n and OpenCV
- Eclipse KUKSA Databroker and VSS
- Docker
- Flask
- Streamlit
- SQLite
- Pandas
- Raspberry Pi 5

## Current Progress

- [x] AI-based perception pipeline implemented.
- [x] KUKSA-based data communication implemented.
- [x] Perception-integrity monitoring implemented.
- [x] Baseline and fault-aware decision modules implemented.
- [x] Fault-injection experiments completed.
- [x] Evaluation and latency benchmarking completed.
- [x] Integrity-validator audit completed.
- [x] Dashboard and historical storage implemented.
- [x] Distributed laptop and Raspberry Pi demonstration completed.
- [ ] Final research paper writing.

---

## Overview
A software-based SDV perception-to-decision framework using Eclipse KUKSA Databroker. It investigates the effects of unreliable perception messages on downstream decisions.

## Components
- YOLO11n perception
- Eclipse KUKSA Databroker
- Integrity monitor
- Baseline and proposed decision modules
- Fault injection
- Offline evaluation
- Latency benchmarking
- Streamlit dashboard
- SQLite historical storage

## Architecture
Camera -> YOLO11n -> KUKSA -> Integrity Monitor -> Fault-Aware Decision Module

## Integrity Checks
Required fields, schema version, source/session identifiers, timestamps, duplicate sequences, sequence gaps, out-of-order messages, detection count, class labels, confidence and bounding boxes.

Maximum message age: 500 ms.
Future timestamp tolerance: 1000 ms.
Schema version: 1.0.

## Decision Policies
Baseline:
- Person: ALERT
- No person: NORMAL

Proposed:
- Invalid perception: CAUTION
- Valid person detection: ALERT
- Valid no-person detection: NORMAL

## Environment
Ubuntu, Python 3.14.4, KUKSA Databroker 0.7.1, kuksa_client 0.6.0, Docker, YOLO11n, OpenCV, Streamlit and SQLite.

## Evaluation Commands
python evaluation/evaluate_decisions_corrected.py
python evaluation/benchmark_latency.py
python evaluation/integrity_validator_audit.py

## Controlled Evaluation Results
Total messages: 10
True positives: 5
False positives: 0
False negatives: 0
True negatives: 5
Precision: 100%
Recall: 100%
False positive rate: 0%
Accuracy: 100%

These results apply only to the controlled test dataset.

## Latest Repeated Latency Benchmark
Measured samples: 300

| Metric | Baseline | Proposed |
|---|---:|---:|
| Mean | 0.001111 ms | 0.007659 ms |
| Median | 0.001092 ms | 0.007865 ms |
| Minimum | 0.000902 ms | 0.005530 ms |
| Maximum | 0.001453 ms | 0.019096 ms |
| P95 | 0.001343 ms | 0.008416 ms |

These are local Python decision-processing measurements, excluding KUKSA communication, message pairing, publication, database operations and dashboard rendering.

## Validator Audit
17 tests executed.
17 passed.
0 failed.
0 errors.

## Live Fault Injection
Six experiment logs cover stale messages, duplicate messages, out-of-order messages, missing sequence numbers, invalid confidence and delayed publication. Stale and delayed publication are two methods of examining message freshness.

## Limitations
- Controlled evaluation dataset.
- No complete end-to-end latency measurement.
- A sequence gap does not independently prove packet loss.
- Perception runs on Raspberry Pi 5 CPU.
- No hardware ECU deployment or certified vehicle-safety validation.

## Research Contribution
A KUKSA-based framework that monitors perception-message integrity and uses integrity status to influence downstream decision-making. It compares baseline and integrity-aware processing under controlled perception-message faults.

## Verified Live Deployment

The live demonstration uses a distributed laptop–Raspberry Pi architecture.

- Laptop webcam captured and streamed through Flask on port 5001.
- Raspberry Pi 5 receives the MJPEG stream over Wi-Fi.
- YOLO11n performs CPU inference on the Raspberry Pi at 320-pixel input size.
- Annotated frames are saved and streamed by a Flask video server on port 5002.
- Perception messages are published to the laptop-hosted Eclipse KUKSA Databroker on port 55555.
- Integrity monitoring and decision processing run on the Raspberry Pi.
- Streamlit dashboard and SQLite historical storage run on the laptop.

## Live Perception Performance

Single-session live measurements:

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

These measurements represent one live session and should not be interpreted as guaranteed performance under all operating conditions.

## System Architecture Figure

See `research_results/figures/06_system_architecture.png`.
