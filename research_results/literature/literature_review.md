# Literature Review and Comparative Analysis

## Research project
Development of a Software-Defined Platform for AI-Driven Vehicle
Perception and Decision-Making.

## 1. Selected research papers

### Paper 1
Title: Monitoring of Perception Systems: Deterministic, Probabilistic,
and Learning-based Fault Detection and Identification

Authors: Pasquale Antonante, Heath G. Nilsen, Luca Carlone
Journal: Artificial Intelligence
Year: 2023
Volume: 325
Article: 103998
DOI: 10.1016/j.artint.2023.103998
URL: https://arxiv.org/abs/2205.10906

Focus:
Runtime monitoring of perception systems using diagnostic graphs
and deterministic, probabilistic and learning-based fault detection.

Relevance:
Supports the motivation for monitoring perception-system failures.

### Paper 2
Title: Integrity Monitoring of Multimodal Perception System
for Vehicle Localization

Authors: Arjun Balakrishnan, Sergio Rodriguez Florez, Roger Reynaud
Journal: Sensors
Year: 2020
Volume: 20
Issue: 16
Article: 4654
DOI: 10.3390/s20164654
URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC7472622/

Focus:
Integrity assessment of multimodal exteroceptive sensor data using
a multisource coherence-based approach.

Relevance:
Supports the importance of assessing the reliability of
perception information in autonomous vehicles.

### Paper 3
Title: Fault Detection, Isolation, Identification and Recovery (FDIIR)
Methods for Automotive Perception Sensors Including a Detailed
Literature Survey for Lidar

Authors: Thomas Goelles, Birgit Schlager, Stefan Muckenhuber
Journal: Sensors
Year: 2020
Volume: 20
Issue: 13
Article: 3662
DOI: 10.3390/s20133662
URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC7374415/

Focus:
Automotive perception-sensor fault detection, isolation,
identification and recovery, with a detailed LiDAR literature survey.

Relevance:
Provides background on sensor-level fault diagnosis and mitigation.

### Paper 4
Title: A Non-Intrusive Data Age Tracer for Real-Time ROS 2 Applications

Authors: Yundo Choi, Taekyeong Lee, Hyeong Rae Cho, Kyong Hoon Kim
Journal: IEEE Embedded Systems Letters
Year: 2026
Status: Accepted/In press
DOI: 10.1109/LES.2026.3727658
URL: https://research.knu.ac.kr/en/publications/a-non-intrusive-data-age-tracer-for-real-time-ros-2-applications/

Focus:
Tracing direct and indirect data age in ROS 2 applications and
studying the effects of upstream data freshness on downstream outputs.

Relevance:
Supports the importance of data freshness and temporal consistency.

### Paper 5
Title: A Faster and More Reliable Middleware for Autonomous Driving Systems

Authors: Yuankai He, Hanlin Chen, Weisong Shi
Year: 2025
Publication type: arXiv preprint
arXiv: 2510.11448
URL: https://arxiv.org/abs/2510.11448

Focus:
Sensor-in-Memory middleware for autonomous-driving systems,
with freshness-oriented transport, sequence numbers, heartbeat
and optional checksums.

Relevance:
Provides a comparison for distributed vehicle-data communication,
message ordering and freshness.

---

## 2. Preliminary comparison with this project

| Feature | Paper 1 | Paper 2 | Paper 3 | Paper 4 | Paper 5 | Our project |
|---|---|---|---|---|---|---|
| Automotive perception | Yes | Yes | Yes | Yes | Yes | Yes |
| Perception/system fault monitoring | Yes | Yes | Yes | Data-age tracing | Middleware integrity | Yes |
| Multimodal sensor coherence | Not central | Yes | Sensor-specific | Not central | Not central | No |
| Data freshness/age | Temporal monitoring | Not central | Not central | Yes | Yes | Yes |
| Sequence validation | Not central | Not central | Not central | Not central | Yes | Yes |
| Detection-field validation | Diagnostic tests | Sensor coherence | Sensor faults | Not central | Not central | Yes |
| KUKSA/VSS integration | Not reported | Not reported | Not reported | ROS 2 | ROS 2-oriented | Yes |
| Integrity affects downstream decision | Monitoring framework | Integrity assessment | Fault mitigation | Data-age analysis | Middleware behavior | Yes |
| Baseline/proposed decision comparison | Different monitoring algorithms | Different integrity methods | Review | Tracing analysis | Middleware comparison | Yes |
| Live dashboard and history | Not central | Not central | Not central | Not central | Not central | Yes |
| Controlled evaluation | Yes | Yes | Review | Case study | Experiments | Yes |

Important:
"Not reported" means the feature was not identified in the paper's
available description or reviewed material. It does not prove that
the authors did not implement it.

This table is preliminary and must be refined after full-text review.

---

## 3. Preliminary research gap

Existing research addresses perception-system fault monitoring,
multimodal sensor integrity, automotive sensor fault diagnosis,
data-age tracing and autonomous-driving middleware reliability.

This project investigates an integrated software framework combining:

1. KUKSA-based vehicle-data exchange using custom VSS perception messages.
2. Structured perception-message validation.
3. Freshness and sequence-consistency checks.
4. Detection-field validation.
5. Integrity-aware downstream decision states.
6. Baseline and proposed decision comparison.
7. Controlled fault-injection experiments.
8. A distributed laptop-Raspberry Pi implementation.
9. Live monitoring and historical visualization.

The potential contribution is the integration and experimental
evaluation of these elements in one KUKSA-based perception-to-decision
platform.

This is a preliminary research gap, not a claim of global novelty.
A broader literature search and full-text comparison are required
before making a definitive novelty claim.

---

## 4. Important project-specific evidence to compare

Our implementation:
- YOLO11n perception on Raspberry Pi 5 CPU.
- Custom VSS signal: Vehicle.Perception.FrameData.
- Integrity status: Vehicle.Perception.IntegrityStatus.
- Decision status: Vehicle.Decision.Status.
- Maximum message age: 500 ms.
- Future timestamp tolerance: 1000 ms.
- Checks schema, source/session, timestamp, sequence, detection count,
  class, confidence and bounding-box validity.
- Invalid perception leads to CAUTION.
- Valid person detection leads to ALERT.
- Valid no-person detection leads to NORMAL.

Controlled offline evaluation:
- 10 message instances.
- 5 true positives.
- 5 true negatives.
- 0 false positives.
- 0 false negatives.

Independent validator audit:
- 17 tests passed.

Offline decision-processing benchmark:
- 300 measured messages.
- Baseline mean: 0.001111 ms.
- Proposed mean: 0.007659 ms.

Live perception session:
- 3514 frames.
- Mean perception latency: 87.44 ms.
- Approximate processing rate: 9.53 FPS.

These are different experiments and must be reported separately.
The controlled dataset is small and does not establish
real-world vehicle-safety performance.

## 5. Further literature work

Before final paper writing:
1. Obtain and read the full text of all five papers.
2. Verify each paper's methodology and experimental setup.
3. Refine the comparison table using full-text evidence.
4. Search for research specifically involving Eclipse KUKSA,
   Vehicle Signal Specification and data-integrity-aware SDV platforms.
5. Verify whether closely related integrated systems already exist.
6. Finalize the research gap only after this comparison.

---

## 6. Additional KUKSA-Specific Research

### Paper 6
Title: On deployment of Eclipse Kuksa as a framework for an
intelligent moving test platform for research of autonomous vehicles

Authors: Harri Hirvonsalo and Pertti Seppänen
Year: 2021
Publication: Proceedings of the 2nd Eclipse Research International
Conference on Security, Artificial Intelligence, Architecture
and Modelling for Next Generation Mobility
CEUR Workshop Proceedings, Volume 3028, pages 38-50.

URL:
https://ceur-ws.org/Vol-3028/D2-03-ESAAMM_2021_paper_8.pdf

Focus:
Deployment of the Eclipse KUKSA framework in an automotive
research platform, covering in-vehicle subsystems, cloud
subsystems and data communication.

Relevance:
Provides direct background for the use of KUKSA as an automotive
data platform.

Difference from our implementation:
Our project additionally implements perception-message integrity
validation and evaluates how detected faults influence downstream
decision states.

### Paper 7
Title: Towards Data-Centric and Context-Aware Decision Making
in Software-Defined Vehicles

Authors: Ella Peltonen, Vishaka Basnayake, Nada Elgendy,
Benjamin Kämä, Pertti Seppänen and Tero Päivärinta.
Year: 2025.
Repository: University of Oulu research repository.

URL:
https://oulurepo.oulu.fi/bitstream/handle/10024/56698/nbnfioulu-202506064203.pdf

Focus:
A data-centric, microservices-oriented SDV architecture using
open-source building blocks, including Eclipse KUKSA, for
vehicle-edge-cloud data processing and context-aware decision-making.

Relevance:
Directly relates to KUKSA, VSS, SDV architecture and decision-making.

Difference from our implementation:
This work presents an architectural vision and future implementation
directions. Our project implements a specific perception-to-decision
pipeline and experimentally evaluates perception-message integrity
fault handling.

## 7. Refined Preliminary Research Gap

KUKSA-related research has explored open automotive data platforms,
in-vehicle and cloud integration, VSS-based data management and
data-centric decision-making architectures.

Perception-monitoring research has separately investigated
perception faults, sensor integrity, data freshness and fault
detection.

The present project focuses on bringing these areas together in
an implemented KUKSA-based software platform. It validates
structured perception messages for freshness, sequence consistency,
schema correctness and detection-field validity, then propagates
integrity status into downstream decision-making.

The contribution is evaluated using controlled fault scenarios,
baseline-versus-proposed decision comparison, an independent
validator audit, local processing-latency measurements and a
distributed laptop-Raspberry Pi demonstration.

This is a preliminary gap statement. It must be checked against
additional full-text literature before claiming that the combination
is novel.

---

## 8. ROS 2-Based Architecture for Autonomous Driving Systems:
## Design and Implementation (2026)

Authors: Andrea Bonci, Federico Brunella, Matteo Colletta,
Alessandro Di Biase, Aldo Franco Dragoni and Angjelo Libofsha.

Journal: Sensors
Year: 2026
Volume: 26
Issue: 2
Article: 463
DOI: 10.3390/s26020463

URL:
https://www.mdpi.com/1424-8220/26/2/463

Focus:
A modular ROS 2 autonomous-driving architecture with perception,
planning and control layers, QoS communication, freshness-oriented
event-driven decision-making and validation on a 1:10-scale vehicle.

Relevance:
A close architectural comparison for distributed perception,
freshness requirements and downstream decision processing.

Difference from our implementation:
This work focuses on a ROS 2 architecture and real-time vehicle
demonstration. Our work focuses on KUKSA/VSS perception-message
integrity validation and controlled fault-aware decision evaluation.

## 9. A Survey on Sensor Failures in Autonomous Vehicles:
## Challenges and Solutions (2024)

Authors: Francisco Matos, Jorge Bernardino, João Durães
and João Cunha.

Journal: Sensors
Year: 2024
Volume: 24
Issue: 16
Article: 5108
DOI: 10.3390/s24165108

URL:
https://pmc.ncbi.nlm.nih.gov/articles/PMC11360603/

Focus:
A survey of sensor failures in autonomous vehicles, their causes,
challenges and possible mitigation strategies.

Relevance:
Provides broader background for the importance of reliable
perception inputs and fault-aware vehicle systems.

Difference from our implementation:
This is a literature survey. Our work implements and evaluates
a specific software-level perception-message integrity pipeline.

## 10. Refined Literature Position

The selected works cover four complementary areas:

1. KUKSA and SDV data-platform architecture.
2. Perception and sensor integrity monitoring.
3. Message freshness, sequence consistency and middleware.
4. Distributed autonomous-driving architectures and decision-making.

The project contribution should be framed as an implemented
and experimentally evaluated integration of these concerns:
KUKSA/VSS perception messaging, structured integrity validation,
fault-aware downstream decisions, controlled evaluation and
live distributed monitoring.

The selected literature does not establish that no prior system
has implemented a similar combination. A full-text comparison
and targeted search for closely related implementations are
still required before making a novelty claim.
