#!/usr/bin/env python

from prometheus_client import start_http_server, Gauge, Counter
import argparse
import httplib
import time
import collections
import json
import socket

version = 0.50

# Check if IP is valid
def validIP(ip):
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except socket.error:
        parser.error("Invalid IP Address.")
    return ip

# Parse commandline arguments
parser = argparse.ArgumentParser(description="Claymore Prometheus exporter v" + str(version))
parser.add_argument("-t", "--target", metavar="<ip>", required=True, help="Target IP Address", type=validIP)
parser.add_argument("-f", "--frequency", metavar="<seconds>", required=False, help="Interval in seconds between checking measures", default=1, type=int)
parser.add_argument("-p", "--port", metavar="<port>", required=False, help="Port for listenin", default=8601, type=int)
parser.add_argument("-c", "--claymoreport", metavar="<claymoreport>", required=False, help="Port where claymore will be watching", default=3333, type=int)
args = parser.parse_args()

# Set target IP, port and command to send
ip = args.target
listen_port = args.port
sleep_time = args.frequency
port = args.claymoreport

received_data = {'claymore_version': '', 'running_time': '', 'gpu': {} , 'coin1': {}, 'coin2': {}}

REQUEST_HIGHEST_TEMP = Gauge('claymore_highest_temp','Highest GPU Temp')
REQUEST_GPU_TEMP  = Gauge('claymore_gpu_temp','Claymore GPU temp', ['gpu_id'])
REQUEST_GPU_FAN  = Gauge('claymore_gpu_fan','Claymore GPU fan', ['gpu_id'])
REQUEST_TOTAL_HR = Gauge('claymore_total_hashrate','Claymore Total Hashrate')
REQUEST_GPU_HR = Gauge('claymore_gpu_hr', 'Claymore GPU HR', ['gpu_id'])
REQUEST_TIME_RUNNING = Gauge('claymore_total_runtime','Claymore Total Runtime')

# Sample for getting data from Claymore
# $ echo '{"id":0,"jsonrpc":"2.0","method":"miner_getstat1"}' | nc 192.168.1.34 3333
#
# Return Value:
# {"id": 0, "error": null, "result": ["9.3 - ETH", "25", "32490;6;0", "26799;5690", "649800;9;0", "535999;113801", "", "eth-eu1.nanopool.org:9999;sia-eu1.nanopool.org:7777", "0;0;0;0"]}

def netcat(hostname, port, content):
    """ Netcat equivalent to get data from Claymore. Normal http get doesn't works."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    s.settimeout(3)
    try:
        s.connect((hostname, port))
        s.sendall(content)
        s.shutdown(socket.SHUT_WR)
        fulltext = ''
        while 1:
            data = s.recv(1024)
            if data == "":
                break
            fulltext += data
    except socket.error, e:
        fulltext='{"error": true, "id": 0, "result": ["No client", "6", "0;0;0", "0;0", "0;0;0", "0;0", "0;0;0;0", "-;--", "0;0;0;0"]}'
        print "Socket error: ", e
    except IOError, e:
        fulltext='{"error": true, "id": 0, "result": ["No client", "6", "0;0;0", "0;0", "0;0;0", "0;0", "0;0;0;0", "-;--", "0;0;0;0"]}'
        print "IOError: error: ", e
    finally:
        s.close()
    return parse_response(fulltext)


def parse_response(data):
    """ Get json from data."""
    received_data = json.loads(data)
    return received_data

if __name__ == "__main__":
    # Start up the server to expose the metrics.
    start_http_server(listen_port)

    # Main loop
    while True:
        data = netcat(ip, port, '{"id":0,"jsonrpc":"2.0","method":"miner_getstat1"}' )
        received_data['claymore_version'] = data['result'][0]

    #Get total time miner has been running    
        REQUEST_TIME_RUNNING.set(data['result'][1])
    
    #Get the Total Hashrate
        total_coin_array = data['result'][2].split(';')
        total_hr = (float(total_coin_array[0])/1000)
        REQUEST_TOTAL_HR.set(total_hr)

    #Get each GPU Hashrate
        gpu_hash_array = data['result'][3].split(';')
        for i, item in enumerate(gpu_hash_array):
            REQUEST_GPU_HR.labels(i).set(gpu_hash_array[i])

    #Get Highest Temp 
        gpu_maxtemp_array = data['result'][6].split(';')
        gpu_maxtemp_array = gpu_maxtemp_array[::2]
        REQUEST_HIGHEST_TEMP.set(max(gpu_maxtemp_array))

    #Get each GPU Temp
        gpu_temp_array = data['result'][6].split(';')
        gpu_temp_array = gpu_temp_array[::2]
        for i, item in enumerate(gpu_temp_array):
            REQUEST_GPU_TEMP.labels(i).set(gpu_temp_array[i])

    #Get each GPU Fan Speed 
        gpu_fan_array = data['result'][6].split(';')
        gpu_fan_array = gpu_fan_array[1::2]
        for i, item in enumerate(gpu_fan_array):
            REQUEST_GPU_FAN.labels(i).set(gpu_fan_array[i])

    #Sleep before run again
        time.sleep(sleep_time)
#    main()