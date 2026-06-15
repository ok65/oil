from oil.analyzers.n9030 import N9030


from time import sleep
from random import random

import matplotlib.pyplot as plt

sa_conn_string = "TCPIP::169.254.156.140::INSTR"


if __name__ == "__main__":

    sa = N9030(sa_conn_string)
    print(sa.identify())

    sa.frequency_span = 200E6
    sa.frequency_center = 10E9

    sa.marker[1].enabled = True
    sa.marker[1].peak_search()
    peak_f = sa.marker[1].frequency/1E9
    peak_p = sa.marker[1].power
    print(f"Marker: {peak_f}GHz, {peak_p}dBm")
    sa.marker[1].frequency = 10E9 + 20E6

    peak_f = sa.marker[1].frequency/1E9
    peak_p = sa.marker[1].power

    print(f"Marker: {peak_f}GHz, {peak_p}dBm")

    data = sa.download_trace(1)

    plt.plot(data["frequency"], data["power"])

    plt.show()
    pass
