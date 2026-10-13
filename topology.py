# topology.py
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time

def create_hospital_topology():
    info('*** Initializing Mininet for Hospital IoMT Network\n')
    net = Mininet(
        switch=OVSSwitch,
        controller=RemoteController,
        link=TCLink
    )

    # 1. Controller
    info('*** Adding Ryu Controller\n')
    c0 = net.addController('c0', ip='127.0.0.1', port=6633)

    # 2. Switches (3 departments) - CRITICAL: OpenFlow13 must be set
    info('*** Adding Department Switches (OpenFlow 1.3)\n')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')  # ICU
    s2 = net.addSwitch('s2', protocols='OpenFlow13')  # Pharmacy
    s3 = net.addSwitch('s3', protocols='OpenFlow13')  # Admin

    # 3. ICU Devices
    info('*** Adding ICU Devices\n')
    h1 = net.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01')  # Ventilator
    h2 = net.addHost('h2', ip='10.0.0.2', mac='00:00:00:00:00:02')  # ICU Monitor
    h3 = net.addHost('h3', ip='10.0.0.3', mac='00:00:00:00:00:03')  # Infusion Pump

    # 4. Pharmacy Devices
    info('*** Adding Pharmacy Devices\n')
    h4 = net.addHost('h4', ip='10.0.0.4', mac='00:00:00:00:00:04')  # Pharmacy PC
    h5 = net.addHost('h5', ip='10.0.0.5', mac='00:00:00:00:00:05')  # Drug Dispenser
    h6 = net.addHost('h6', ip='10.0.0.6', mac='00:00:00:00:00:06')  # Pharmacy DB

    # 5. Admin Devices
    info('*** Adding Admin Devices\n')
    h7 = net.addHost('h7', ip='10.0.0.7', mac='00:00:00:00:00:07')  # Admin PC
    h8 = net.addHost('h8', ip='10.0.0.8', mac='00:00:00:00:00:08')  # Ward Monitor
    h9 = net.addHost('h9', ip='10.0.0.9', mac='00:00:00:00:00:09')  # Nurses Station

    # 6. Attacker — h10
    info('*** Adding Attacker Node\n')
    h10 = net.addHost('h10', ip='10.0.0.10', mac='00:00:00:00:00:10')

    # 7. Links — hosts to switches
    info('*** Creating Links\n')
    for h in [h1, h2, h3, h10]: # Attacker connected to ICU switch
        net.addLink(h, s1)
    for h in [h4, h5, h6]: 
        net.addLink(h, s2)
    for h in [h7, h8, h9]: 
        net.addLink(h, s3)

    # 8. Inter-switch links
    info('*** Connecting Departments\n')
    net.addLink(s1, s2)
    net.addLink(s2, s3)

    return net

if __name__ == '__main__':
    # Set logging to see Mininet output
    setLogLevel('info')
    
    # Create the network
    hospital_net = create_hospital_topology()
    
    # Start the network
    info('*** Starting Network\n')
    hospital_net.start()
    
    # Open the Mininet Command Line Interface     
    info('*** Running CLI\n')
    CLI(hospital_net)
    
    # Stop the network when the user exits the CLI
    info('*** Stopping Network\n')
    hospital_net.stop()