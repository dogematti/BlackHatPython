#!/usr/bin/env python3

import socket
import argparse
import time
import random
import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from scapy.all import send
from scapy.layers.inet import IP, ICMP, TCP
from tqdm import tqdm

# Configure basic logging settings for the application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_verbose(message, verbose):
    if verbose:
        logging.info(message)

def parallel_https_get_request(target_url, num_requests, delay, num_threads, verify_ssl=True, verbose=False):
    def single_request():
        try:
            response = requests.get(target_url, verify=verify_ssl, timeout=10)
            log_verbose(f"HTTPS GET request to {target_url} returned status code: {response.status_code}", verbose)
            time.sleep(delay)
        except requests.exceptions.RequestException as e:
            log_verbose(f"Failed to send HTTPS GET request to {target_url}: {e}", verbose)
        except Exception as e:
            log_verbose(f"Unexpected error in HTTPS GET request to {target_url}: {e}", verbose)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        list(tqdm(executor.map(lambda _: single_request(), range(num_requests)), total=num_requests))

def parallel_send_udp_packet(target_host, target_port, min_size, max_size, num_packets, num_threads, verbose=False, delay=0.1):
    def single_udp_packet():
        packet_size = random.randint(min_size, max_size)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                data = b'X' * packet_size
                udp_socket.sendto(data, (target_host, target_port))
                log_verbose(f"Sent UDP packet to {target_host}:{target_port} (size: {packet_size} bytes)", verbose)
                time.sleep(delay)
        except socket.error as e:
            log_verbose(f"Socket error in UDP packet sending: {e}", verbose)
        except Exception as e:
            log_verbose(f"Unexpected error in UDP packet sending: {e}", verbose)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        list(tqdm(executor.map(lambda _: single_udp_packet(), range(num_packets)), total=num_packets))

def send_icmp_packet(target_host, num_packets, timeout, verbose=False, delay=0.1):
    def single_icmp_packet():
        packet = IP(dst=target_host)/ICMP()
        try:
            send(packet, timeout=timeout, verbose=0)
            log_verbose(f"Sent ICMP packet to {target_host}", verbose)
            time.sleep(delay)
        except Exception as e:
            log_verbose(f"Failed to send ICMP packet: {e}", verbose)

    with ThreadPoolExecutor(max_workers=1) as executor:
        list(tqdm(executor.map(lambda _: single_icmp_packet(), range(num_packets)), total=num_packets))

def tcp_test(target_host, target_port, num_connections, verbose=False, num_threads=5):
    def single_connection():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
                tcp_socket.connect((target_host, target_port))
                log_verbose(f"Connected to TCP {target_host}:{target_port}", verbose)
                tcp_socket.close()
        except socket.error as e:
            log_verbose(f"TCP connection failed to {target_host}:{target_port}: {e}", verbose)
        except Exception as e:
            log_verbose(f"Unexpected error in TCP connection: {e}", verbose)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        list(tqdm(executor.map(lambda _: single_connection(), range(num_connections)), total=num_connections))

def tcp_syn_flood(target_host, target_port, num_packets, verbose=False, num_threads=5):
    def single_syn_packet():
        syn_packet = IP(dst=target_host)/TCP(dport=target_port, flags='S')
        try:
            send(syn_packet, verbose=0)
            log_verbose(f"Sent TCP SYN packet to {target_host}:{target_port}", verbose)
            time.sleep(random.uniform(0.1, 1))
        except Exception as e:
            log_verbose(f"Failed to send TCP SYN packet: {e}", verbose)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        list(tqdm(executor.map(lambda _: single_syn_packet(), range(num_packets)), total=num_packets))

def execute_all_tests(args):
    with ThreadPoolExecutor(max_workers=args.num_threads) as executor:
        executor.submit(parallel_https_get_request, args.http_url, args.http_requests, args.http_delay, args.num_threads, args.verify_ssl, args.verbose)
        executor.submit(parallel_send_udp_packet, args.target_host, args.target_port_udp, args.min_packet_size, args.max_packet_size, args.num_packets_udp, args.num_threads, args.verbose, args.delay)
        executor.submit(send_icmp_packet, args.target_host, args.num_packets_icmp, args.timeout_icmp, args.verbose, args.delay)
        executor.submit(tcp_test, args.target_host, args.target_port_tcp, args.num_connections_tcp, args.verbose, args.num_threads)
        executor.submit(tcp_syn_flood, args.target_host, args.target_port_tcp, args.num_packets_tcp, args.verbose, args.num_threads)

def parse_args():
    parser = argparse.ArgumentParser(description="Python3 program for stress-testing a target host using various methods.")
    parser.add_argument("test_type", choices=['udp', 'icmp', 'tcp', 'all', 'http', 'syn_flood'], nargs='?', help="Stress-test type")
    parser.add_argument("target_host", nargs='?', help="Target host IP address")
    parser.add_argument("-n", "--num_threads", type=int, default=5, nargs='?', help="Number of threads for parallel processing")
    parser.add_argument("-d", "--delay", type=float, default=0.1, nargs='?', help="Delay between packets (seconds)")
    parser.add_argument("-p", "--packet_size", type=int, default=1024, nargs='?', help="Packet size for UDP (bytes)")
    parser.add_argument("-x", "--num_packets_udp", type=int, default=100, nargs='?', help="Number of UDP packets to send")
    parser.add_argument("-e", "--timeout_icmp", type=float, default=1.0, nargs='?', help="ICMP test timeout (seconds)")
    parser.add_argument("-o", "--num_packets_icmp", type=int, default=5, nargs='?', help="Number of ICMP packets to send")
    parser.add_argument("-m", "--num_connections_tcp", type=int, default=10, nargs='?', help="Number of TCP connections to make")
    parser.add_argument("-r", "--target_port_udp", type=int, default=5000, nargs='?', help="Target port number for UDP")
    parser.add_argument("-a", "--target_port_tcp", type=int, default=80, nargs='?', help="Target port number for TCP")
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    parser.add_argument("--http-url", nargs='?', help="Target URL for HTTP GET requests")
    parser.add_argument("--http-requests", type=int, default=100, nargs='?', help="Number of HTTP GET requests to send")
    parser.add_argument("--http-delay", type=float, default=0.1, nargs='?', help="Delay between HTTP GET requests (seconds)")
    parser.add_argument("--verify_ssl", action="store_true", help="Verify SSL certificates")

    args = parser.parse_args()

    if not args.test_type:
        args.test_type = input("Enter stress-test type (udp, icmp, tcp, all, http, syn_flood): ")
    if not args.target_host:
        args.target_host = input("Enter target host IP address: ")

    return args

def main():
    args = parse_args()

    if args.test_type == "all":
        execute_all_tests(args)
    elif args.test_type == "http":
        parallel_https_get_request(args.http_url, args.http_requests, args.http_delay, args.num_threads, args.verify_ssl, args.verbose)
    elif args.test_type == "udp":
        parallel_send_udp_packet(args.target_host, args.target_port_udp, args.min_packet_size, args.max_packet_size, args.num_packets_udp, args.num_threads, args.verbose, args.delay)
    elif args.test_type == "icmp":
        send_icmp_packet(args.target_host, args.num_packets_icmp, args.timeout_icmp, args.verbose, args.delay)
    elif args.test_type == "tcp":
        tcp_test(args.target_host, args.target_port_tcp, args.num_connections_tcp, args.verbose, args.num_threads)
    elif args.test_type == "syn_flood":
        tcp_syn_flood(args.target_host, args.target_port_tcp, args.num_packets_tcp, args.verbose, args.num_threads)
    else:
        raise ValueError(f"Invalid test type: {args.test_type}")

if __name__ == "__main__":
    main()
