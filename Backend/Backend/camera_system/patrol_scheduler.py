import time
from datetime import datetime

from camera_patrol_simulator import run_simulated_patrol


# ============================================================
# CAMERA PATROL SCHEDULER
# ============================================================

# TEST MODE:
# 10 seconds = one patrol round
#
# PRODUCTION:
# Change this to 600 seconds
# 600 seconds = 10 minutes

PATROL_INTERVAL = 10

CAMERA_ID = "PARKING_CAMERA_01"


def run_scheduler():

    print("===================================")
    print(" CAMERA PATROL SCHEDULER")
    print("===================================")

    print(f"Camera ID      : {CAMERA_ID}")
    print(f"Patrol interval: {PATROL_INTERVAL} seconds")

    print("\nMode:")
    print("TEST MODE - physical camera not connected")

    print("\nScheduler started.")
    print("Press CTRL+C to stop.")

    round_number = 0

    while True:

        round_number += 1

        print("\n")
        print("===================================")
        print(f" STARTING PATROL ROUND {round_number}")
        print("===================================")

        start_time = datetime.now()

        print("Start time:", start_time.strftime("%Y-%m-%d %H:%M:%S"))

        try:

            result = run_simulated_patrol()

            if result:

                print("\nPATROL ROUND COMPLETED")

            else:

                print("\nPATROL ROUND FAILED")

        except Exception as error:

            print("\nPATROL ERROR")
            print(error)

        print("\nNext patrol will start after")
        print(f"{PATROL_INTERVAL} seconds.")

        try:

            time.sleep(PATROL_INTERVAL)

        except KeyboardInterrupt:

            print("\n===================================")
            print(" CAMERA PATROL SCHEDULER STOPPED")
            print("===================================")

            break


if __name__ == "__main__":

    run_scheduler()