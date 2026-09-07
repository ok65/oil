
from oil.analyzers import E5071C, E5071C_Marker
from oil.core import ip_address_string
from oil.switches import RFSwitchMatrix
import time

if __name__ == "__main__":

    VNA_IP = "169.254.156.80"
    RFSW_IP = "169.254.156.200"

    vna = E5071C(ip_address_string(VNA_IP))
    rfsw = RFSwitchMatrix(ip_address_string(RFSW_IP))

    print(vna.frequency_start)

    print(vna.identify())
    print(rfsw.identify())


    while True:

        print("setting rfsw")
        rfsw.rfa = 1
        rfsw.rfb = 1

        print("downloading trace")
        vna.download_trace() # Throw away data for now

        print("Sleeping")
        time.sleep(10)



    pass
