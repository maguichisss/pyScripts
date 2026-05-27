from wsdiscovery.discovery import ThreadedWSDiscovery

wsd = ThreadedWSDiscovery()
wsd.start()

services = wsd.searchServices()

for service in services:
    print("Address:", service.getXAddrs())
    print("Types:", service.getTypes())
    print("Scopes:", service.getScopes())
    print("-" * 50)

wsd.stop()

# ffmpeg -t 60 -i rtsp://192.168.1.31 -c copy output.mp4
# ffplay rtsp://192.168.1.20
