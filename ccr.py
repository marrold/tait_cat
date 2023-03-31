import sys
import tait_cat as tait
import time

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = sys.argv[1]
        radio = tait.Radio(port)

        # print("Exiting CCR")
        # radio.ccr_exit()

        # time.sleep(5)

        # # print(f"Pulse: {print(radio.ccr_pulse())}")

        print("Entering CCR")
        radio.ccr_enter()

        time.sleep(1)

        print(f"Pulse: {radio.ccr_pulse()}")

        # print("Set Rx")
        # print(radio.ccr_rx("144500000"))

        # time.sleep(1)

        # print("Set Tx")
        # print(radio.ccr_tx("144500000"))

        # time.sleep(1)

        # print("Set Tx")
        # print(radio.ccr_tx("144500000"))

        # time.sleep(1)

        # print("Set Power")
        # print(radio.ccr_pwr("1"))

    else:
        print("Please provide a port.")

