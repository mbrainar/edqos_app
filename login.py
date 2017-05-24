import os
from uniq.apis.nb.client_manager import NbClientManager

def login():
    apic = os.getenv("APIC_SERVER") or "sandboxapic.cisco.com"
    username = os.getenv("APIC_USERNAME") or "devnetuser"
    password = os.getenv("APIC_PASSWORD") or "Cisco123!"

    try:
        client = NbClientManager(server=apic,
                                 username=username,
                                 password=password,
                                 connect=True)
        return client
    except:
        return None