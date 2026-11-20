import json

from kuksa_client.grpc import VSSClient

HOST = "127.0.0.1"
PORT = 55555

PERCEPTION_SIGNAL = "Vehicle.Perception.FrameData"


def make_baseline_decision(perception):

    detections = perception.get("detections", [])

    person_detected = any(
        detection.get("class", "").lower() == "person"
        for detection in detections
    )

    if person_detected:
        return "ALERT", "Person detected in the perception frame"

    return "NORMAL", "No person detected"


def main():

    print("\nStarting Baseline Decision Module")
    print("Integrity checking: DISABLED")
    print("-" * 45)

    with VSSClient(HOST, PORT) as client:

        for updates in client.subscribe_current_values(
            [PERCEPTION_SIGNAL]
        ):

            try:
                raw_message = updates[PERCEPTION_SIGNAL].value
                perception = json.loads(raw_message)

                decision, reason = make_baseline_decision(perception)

                print(
                    f"Frame: {perception.get('sequence_number')} | "
                    f"Decision: {decision} | "
                    f"Reason: {reason}"
                )

            except (json.JSONDecodeError, TypeError, AttributeError) as error:
                print("Baseline processing error:", error)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBaseline Decision Module stopped.")
