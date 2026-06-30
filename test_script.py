from oil.analyzers.n9030 import N9030
from oil.sig_gens.smr20 import SMR20

from time import sleep
from random import random

import matplotlib.pyplot as plt

sa_conn_string = "TCPIP::169.254.156.140::INSTR"
sg_conn_string = "ASRL8::INSTR"

if __name__ == "__main__":

    f = 13.345E9

    #sa = N9030(sa_conn_string)
    sg = SMR20(sg_conn_string)

    #print(sa.identify())
    print(sg.identify())

    #sa.frequency_span = 20E6
    #sa.frequency_center = f

    sg.frequency = f
    sg.power = -4.5
    sg.rf_enable = True

    sleep(1)

    """sa.marker[1].enabled = True
    sa.marker[1].peak_search()
    peak_f = sa.marker[1].frequency/1E9
    peak_p = sa.marker[1].power
    print(f"Marker: {peak_f}GHz, {peak_p}dBm")
    sa.marker[1].frequency = 10E9 + 1E6

    peak_f = sa.marker[1].frequency/1E9
    peak_p = sa.marker[1].power

    print(f"Marker: {peak_f}GHz, {peak_p}dBm")

    data = sa.download_trace(1)

    plt.plot(data["frequency"], data["power"])

    plt.show()"""
    pass
