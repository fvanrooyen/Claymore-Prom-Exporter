# Claymore Prometheus Endpoint

sudo docker build -t core/claymorexp:0.5 .

sudo docker run --restart=always -e IP=IPADDRESS -e CLAYMOREPORT=3333 -d -p 8601:8601 -t core/claymorex
p:0.5
