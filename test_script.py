
from oil.analyzers import E5071C, E5071C_Marker
from oil.core import ip_address_string

if __name__ == "__main__":

    VNA_IP = "169.254.156.80"

    vna = E5071C(ip_address_string(VNA_IP))

    pass
