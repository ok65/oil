
from oil.analyzers import ZNB
from oil.core import ip_address_string


def main():

    vna = ZNB(ip_address_string("192.168.100.50"))

    vna.