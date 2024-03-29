#!/usr/bin/env python3

import asyncio
import aiohttp
import argparse
import random
import logging
import socket
from aiohttp import ClientError, ClientSession
from scapy.all import sr1, IP, ICMP, TCP, send
from urllib.parse import urlparse

# ASCII Art Section - Add your ASCII art here
ASCII_ART = r"""
 _____ __  __ __ _____ __ _____    ___ __  __     
(_  | |__)|_ (_ (_  | |_ (_  |  __  | /  \/  \|   
__) | | \ |____)__) | |____) |      | \__/\__/|__ 
 __        __  __  __  __       ______            
|__)\_/.  |  \/  \/ _ |_ |\/| /\ |  | |           
|__) | .  |__/\__/\__)|__|  |/--\|  | |           
                                                  
"""


# User Agents List with the specified user-agents added
user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6)...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Safari/602.1.50",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:49.0) Gecko/20100101 Firefox/49.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Safari/602.1.50",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0",
]
# Configure logging
logger = logging.getLogger(__name__)

def configure_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def fetch_url(session: ClientSession, url: str, headers: dict):
    try:
        async with session.get(url, headers=headers) as response:
            logger.info(f"Request to {url} returned {response.status}")
            await response.read()
    except ClientError as e:
        logger.error(f"Request to {url} failed: {e}")

async def async_https_get_request(target_url, num_requests, headers):
    async with ClientSession() as session:
        tasks = [fetch_url(session, target_url, headers) for _ in range(num_requests)]
        await asyncio.gather(*tasks)

async def async_tcp_test(target_host, target_port, num_connections):
    for _ in range(num_connections):
        try:
            reader, writer = await asyncio.open_connection(target_host, target_port)
            logger.info(f"Connected to TCP {target_host}:{target_port}")
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            logger.error(f"TCP connection to {target_host}:{target_port} failed: {e}")

def send_icmp_echo(target_host, num_requests):
    for _ in range(num_requests):
        packet = IP(dst=target_host)/ICMP()
        resp = sr1(packet, timeout=1, verbose=0)
        if resp:
            logger.info(f"ICMP Reply from {target_host}: {resp.summary()}")
        else:
            logger.info(f"No ICMP Reply from {target_host}")

def send_tcp_syn(target_host, target_port, num_requests):
    for _ in range(num_requests):
        syn_packet = IP(dst=target_host)/TCP(dport=target_port, flags='S')
        resp = sr1(syn_packet, timeout=1, verbose=0)
        if resp and resp.getlayer(TCP).flags & 0x12:  # SYN/ACK flags
            logger.info(f"Received SYN/ACK from {target_host}:{target_port}")
            # Properly tear down the connection by sending a RST packet
            rst_packet = IP(dst=target_host)/TCP(dport=target_port, flags='R', seq=resp.ack)
            send(rst_packet, verbose=0)
        else:
            logger.info(f"No SYN/ACK from {target_host}:{target_port}")

def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def validate_ip(ip_address):
    try:
        socket.inet_aton(ip_address)
        return True
    except socket.error:
        return False

def parse_args():
    parser = argparse.ArgumentParser(description="Asynchronous Network Test Script")
    parser.add_argument("--test_type", choices=['http', 'tcp', 'icmp', 'syn'], required=True, help="Type of test to perform")
    parser.add_argument("--target_host", required=True, help="Target host for testing")
    parser.add_argument("--target_port", type=int, default=80, help="Target port for testing")
    parser.add_argument("--num_requests", type=int, default=100, help="Number of requests to send")
    parser.add_argument("--verbose", action='store_true', help="Enable verbose logging")
    return parser.parse_args()

async def main():
    args = parse_args()
    configure_logging(args.verbose)
    headers = {'User-Agent': get_random_user_agent()}

    if args.test_type == "http":
        if not validate_url(args.target_host):
            logger.error("Invalid URL format.")
            return
        await async_https_get_request(args.target_host, args.num_requests, headers)
    elif args.test_type == "tcp":
        if not validate_ip(args.target_host):
            logger.error("Invalid IP address format.")
            return
        await async_tcp_test(args.target_host, args.target_port, args.num_requests)
    elif args.test_type == "icmp":
        send_icmp_echo(args.target_host, args.num_requests)
    elif args.test_type == "syn":
        send_tcp_syn(args.target_host, args.target_port, args.num_requests)

if __name__ == "__main__":
    asyncio.run(main())
