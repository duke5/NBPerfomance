import re

dis_result = "Discovered 44992 IP address(es), found 44991 device(s). Detail info: Alcatel Lucent Service Router(111) Arista Switch(29) Arris Router(363) Cache Engine(1) Call Manager(11) Checkpoint Firewall(1) Cisco ACE(132) Cisco ASA Firewall(412) Cisco Catalyst Switch(18) Cisco IOS Switch(25254) Cisco IOS XR(870) Cisco Nexus Switch(673) Cisco Router(8530) Cisco WAP(6844) Cisco WLC(151) End System(730) Extreme Switch(70) F5 Load Balancer(15) HP ProCurve Switch(83) HP Virtual Connect(14) Juniper EX Switch(238) Juniper Router(98) Juniper SRX Firewall(161) Netscaler Load Balancer(8) Printer(2) Riverbed WAN Optimizer(86) Ubuntu Server(3) Unclassified Device(67) Unclassified Switch(10) Windows Server(6) \r\n"
parten1 = "Discovered (\d+) IP address\(es\)"
pipei = re.findall(parten1, dis_result)
print(pipei[0])