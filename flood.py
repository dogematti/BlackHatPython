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

# ASCII Art Section
ASCII_ART = r"""


 ____   ___  ____      _____           _     ____          
|  _ \ / _ \/ ___|    |_   _|__   ___ | |   | __ ) _   _ _ 
| | | | | | \___ \ _____| |/ _ \ / _ \| |   |  _ \| | | (_)
| |_| | |_| |___) |_____| | (_) | (_) | |_  | |_) | |_| |_ 
|____/ \___/|____/      |_|\___/ \___/|_( ) |____/ \__, (_)
 ____                                   |/  _   _  |___/   
|  _ \  ___   __ _  ___ _ __ ___   __ _| |_| |_(_)         
| | | |/ _ \ / _` |/ _ \ '_ ` _ \ / _` | __| __| |         
| |_| | (_) | (_| |  __/ | | | | | (_| | |_| |_| |         
|____/ \___/ \__, |\___|_| |_| |_|\__,_|\__|\__|_|         
             |___/                                         


"""

# User Agents List
user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6)...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    # ... (Your full list of user agents)
]

# Configure logging
logger = logging.getLogger(__name__)


def configure_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def get_random_user_agent():
    return random.choice(user_agents)


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
    tasks = [tcp_connection(target_host, target_port) for _ in range(num_connections)]
    await asyncio.gather(*tasks)


async def tcp_connection(target_host, target_port):
    try:
        reader, writer = await asyncio.open_connection(target_host, target_port)
        logger.info(f"Connected to TCP {target_host}:{target_port}")
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        logger.error(f"TCP connection to {target_host}:{target_port} failed: {e}")


def send_icmp_echo(target_host, num_requests):
    for _ in range(num_requests):
        packet = IP(dst=target_host) / ICMP()
        resp = sr1(packet, timeout=1, verbose=0)
        if resp:
            logger.info(f"ICMP Reply from {target_host}: {resp.summary()}")
        else:
            logger.info(f"No ICMP Reply from {target_host}")


def send_tcp_syn(target_host, target_port, num_requests):
    for _ in range(num_requests):
        syn_packet = IP(dst=target_host) / TCP(dport=target_port, flags="S")
        resp = sr1(syn_packet, timeout=1, verbose=0)
        if resp and resp.getlayer(TCP).flags & 0x12:  # SYN/ACK flags
            logger.info(f"Received SYN/ACK from {target_host}:{target_port}")
            # Properly tear down the connection by sending a RST packet
            rst_packet = IP(dst=target_host) / TCP(
                dport=target_port, flags="R", seq=resp.ack
            )
            send(rst_packet, verbose=0)
        else:
            logger.info(f"No SYN/ACK from {target_host}:{target_port}")


def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False


def validate_ip(ip_address):
    try:
        socket.inet_aton(ip_address)
        return True
    except socket.error as e:
        logger.error(f"IP validation error: {e}")
        return False


def parse_args():
    parser = argparse.ArgumentParser(description="Asynchronous Network Test Script")
    parser.add_argument("--test_type", required=True, choices=["http", "tcp", "icmp", "syn"], help="Type of test to perform")
    parser.add_argument("--target_host", required=True, help="Target URL (for HTTP) or IP address (for TCP, ICMP, SYN)")
    parser.add_argument("--target_port", type=int, help="Target port (for TCP and SYN)")
    parser.add_argument("--num_requests", type=int, default=1, help="Number of requests or connections to send")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


async def main():
    args = parse_args()
    configure_logging(args.verbose)
    headers = {"User-Agent": get_random_user_agent()}

    print(ASCII_ART)

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
        if not validate_ip(args.target_host):
            logger.error("Invalid IP address format.")
            return
        send_icmp_echo(args.target_host, args.num_requests)
    elif args.test_type == "syn":
        if not validate_ip(args.target_host):
            logger.error("Invalid IP address format.")
            return
        send_tcp_syn(args.target_host, args.target_port, args.num_requests)


if __name__ == "__main__":
    asyncio.run(main())
