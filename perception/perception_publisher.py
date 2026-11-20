import json
import time
import uuid
import cv2
import os

from ultralytics import YOLO
from kuksa_client.grpc import VSSClient, Datapoint


# ==========================================================
# CONFIGURATION
# ==========================================================

MODEL_PATH = "yolo11n.pt"
VIDEO_SOURCE = 0

KUKSA_HOST = "127.0.0.1"
KUKSA_PORT = 55555

SIGNAL_PATH = "Vehicle.Perception.FrameData"

CONFIDENCE_THRESHOLD = 0.25

SOURCE_ID = "camera_01"
SESSION_ID = str(uuid.uuid4())

# Website camera image
DASHBOARD_IMAGE_PATH = "dashboard/static/latest_frame.jpg"
TEMP_IMAGE_PATH = "dashboard/static/latest_frame.tmp.jpg"


# ==========================================================
# SAVE LATEST ANNOTATED FRAME
# ==========================================================

def save_dashboard_frame(frame):

    os.makedirs(
        os.path.dirname(DASHBOARD_IMAGE_PATH),
        exist_ok=True
    )

    success = cv2.imwrite(
        TEMP_IMAGE_PATH,
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 85]
    )

    if success:
        os.replace(
            TEMP_IMAGE_PATH,
            DASHBOARD_IMAGE_PATH
        )


# ==========================================================
# MAIN FUNCTION
# ==========================================================

def main():

    print("\nLoading YOLO model...")

    model = YOLO(MODEL_PATH)

    sequence_number = 0

    previous_time = time.perf_counter()
    fps = 0.0

    print("Connecting to KUKSA Databroker...")

    with VSSClient(KUKSA_HOST, KUKSA_PORT) as client:

        print("Connected successfully!")

        video = cv2.VideoCapture(VIDEO_SOURCE)

        if not video.isOpened():
            raise RuntimeError(
                f"Unable to open video source: {VIDEO_SOURCE}"
            )

        try:

            # ==========================================
            # YOLO WARM-UP
            # ==========================================

            print("\nWarming up YOLO model...")

            ret, warmup_frame = video.read()

            if not ret:
                raise RuntimeError(
                    "Unable to capture warm-up frame."
                )

            warmup_start = time.perf_counter()

            model.predict(
                source=warmup_frame,
                device="cpu",
                conf=CONFIDENCE_THRESHOLD,
                verbose=False
            )

            warmup_time = (
                time.perf_counter() - warmup_start
            ) * 1000

            print(
                f"YOLO warm-up completed: {warmup_time:.2f} ms"
            )

            # ==========================================
            # LIVE PERCEPTION
            # ==========================================

            print("\nStarting live perception...")
            print("Press Q in the video window to stop.\n")

            while True:

                # Capture camera frame
                ret, frame = video.read()

                if not ret:
                    print("Video frame unavailable.")
                    break

                # Mirror original camera frame before YOLO inference
                frame = cv2.flip(frame, 1)

                # Capture timestamp immediately
                capture_timestamp_ms = int(
                    time.time() * 1000
                )

                # YOLO inference
                start_time = time.perf_counter()

                results = model.predict(
                    source=frame,
                    device="cpu",
                    conf=CONFIDENCE_THRESHOLD,
                    verbose=False
                )

                perception_latency_ms = (
                    time.perf_counter() - start_time
                ) * 1000

                # Extract detections
                detections = []

                for result in results:

                    for box in result.boxes:

                        class_id = int(box.cls[0])

                        confidence = float(box.conf[0])

                        bbox = [
                            round(float(value), 2)
                            for value in box.xyxy[0].tolist()
                        ]

                        detections.append({

                            "class": model.names[class_id],

                            "confidence": round(
                                confidence, 4
                            ),

                            "bbox": bbox

                        })

                sequence_number += 1

                # Prepare perception message
                perception_data = {

                    "schema_version": "1.0",

                    "source_id": SOURCE_ID,

                    "session_id": SESSION_ID,

                    "sequence_number": sequence_number,

                    "capture_timestamp_ms": capture_timestamp_ms,

                    "detection_count": len(detections),

                    "perception_latency_ms": round(
                        perception_latency_ms, 2
                    ),

                    "detections": detections

                }

                # Publish to KUKSA
                client.set_current_values({

                    SIGNAL_PATH: Datapoint(
                        json.dumps(perception_data)
                    )

                })

                # Calculate FPS
                current_time = time.perf_counter()

                elapsed_time = (
                    current_time - previous_time
                )

                if elapsed_time > 0:
                    fps = 1.0 / elapsed_time

                previous_time = current_time

                # Annotate camera frame
                annotated_frame = results[0].plot()

                cv2.putText(
                    annotated_frame,
                    f"Objects: {len(detections)}",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    annotated_frame,
                    f"Latency: {perception_latency_ms:.2f} ms",
                    (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )

                cv2.putText(
                    annotated_frame,
                    f"FPS: {fps:.1f}",
                    (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 0),
                    2
                )

                cv2.putText(
                    annotated_frame,
                    "KUKSA: CONNECTED",
                    (20, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                # Save latest annotated image for website
                save_dashboard_frame(annotated_frame)

                # Display local camera window
                cv2.imshow(
                    "SDV - Live Object Detection",
                    annotated_frame
                )

                print(
                    f"Frame: {sequence_number} | "
                    f"Objects: {len(detections)} | "
                    f"Latency: {perception_latency_ms:.2f} ms | "
                    f"FPS: {fps:.1f} | "
                    f"Published to KUKSA"
                )

                # Exit on Q
                if cv2.waitKey(1) & 0xFF == ord('q'):

                    print("\nStopping perception...")
                    break

        finally:

            video.release()

            cv2.destroyAllWindows()

            print("\nPerception publisher stopped.")


# ==========================================================
# PROGRAM ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    main()
