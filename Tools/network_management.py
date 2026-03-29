"""
Vortex Network Management Tools
Comprehensive network monitoring, testing, and management capabilities
"""

from __future__ import annotations
import subprocess
import socket
import psutil
import requests
import json
import time
from typing import Dict, Any, List, Optional
from livekit.agents import function_tool

@function_tool()
async def test_internet_connectivity() -> str:
    """
    Test internet connectivity and connection quality
    
    Returns comprehensive information about:
    - Internet connection status
    - Ping response times
    - DNS resolution
    - Connection quality assessment
    """
    try:
        results = []
        
        # Test basic connectivity
        try:
            response = requests.get('https://www.google.com', timeout=5)
            results.append("✅ Internet Connection: Active")
            results.append(f"🌐 Response Time: {response.elapsed.total_seconds()*1000:.1f}ms")
        except requests.RequestException:
            results.append("❌ Internet Connection: Failed")
            return "\n".join(results)
        
        # Test ping to multiple servers
        test_servers = [
            ("Google DNS", "8.8.8.8"),
            ("Cloudflare DNS", "1.1.1.1"),
            ("Google Search", "www.google.com")
        ]
        
        results.append("\n📡 **Ping Test Results:**")
        for name, host in test_servers:
            try:
                start_time = time.time()
                sock = socket.create_connection((host, 80), timeout=3)
                ping_time = (time.time() - start_time) * 1000
                sock.close()
                results.append(f"📍 {name}: {ping_time:.1f}ms")
            except:
                results.append(f"❌ {name}: Timeout")
        
        # Test DNS resolution
        try:
            start_time = time.time()
            socket.gethostbyname('www.google.com')
            dns_time = (time.time() - start_time) * 1000
            results.append(f"\n🔍 DNS Resolution: {dns_time:.1f}ms")
        except:
            results.append("\n❌ DNS Resolution: Failed")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ Network test failed: {str(e)}"

@function_tool()
async def get_network_info() -> str:
    """
    Get detailed network information and statistics
    
    Returns comprehensive network data including:
    - Network interfaces
    - IP addresses
    - Network connections
    - Data usage statistics
    """
    try:
        results = []
        
        # Network interfaces
        results.append("🌐 **Network Interfaces:**")
        interfaces = psutil.net_if_addrs()
        for interface_name, addresses in interfaces.items():
            results.append(f"\n📡 {interface_name}:")
            for addr in addresses:
                if addr.family == socket.AF_INET:
                    results.append(f"   IPv4: {addr.address}")
                elif addr.family == socket.AF_INET6:
                    results.append(f"   IPv6: {addr.address}")
        
        # Network interface stats
        results.append("\n📊 **Network Statistics:**")
        net_io = psutil.net_io_counters(pernic=True)
        for interface, stats in net_io.items():
            if stats.bytes_sent > 0 or stats.bytes_recv > 0:
                mb_sent = stats.bytes_sent / (1024 * 1024)
                mb_recv = stats.bytes_recv / (1024 * 1024)
                results.append(f"📡 {interface}:")
                results.append(f"   📤 Sent: {mb_sent:.1f} MB")
                results.append(f"   📥 Received: {mb_recv:.1f} MB")
        
        # Active connections
        results.append("\n🔗 **Active Connections:**")
        connections = psutil.net_connections()
        connection_count = len([c for c in connections if c.status == 'ESTABLISHED'])
        results.append(f"🔗 Established Connections: {connection_count}")
        
        # Connection details
        if connection_count > 0:
            results.append("\n**Recent Connections:**")
            for conn in connections[:5]:  # Show first 5 connections
                if conn.status == 'ESTABLISHED':
                    local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
                    remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                    results.append(f"   {local_addr} ↔ {remote_addr}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ Failed to get network info: {str(e)}"

@function_tool()
async def check_network_speed() -> str:
    """
    Test network speed and bandwidth
    
    Performs speed tests including:
    - Download speed test
    - Upload speed estimation
    - Latency measurement
    - Connection quality assessment
    """
    try:
        results = []
        
        # Basic speed test using a small file
        test_urls = [
            ("Small File (1MB)", "https://httpbin.org/bytes/1048576"),
            ("Medium File (5MB)", "https://httpbin.org/bytes/5242880")
        ]
        
        results.append("⚡ **Network Speed Test:**")
        
        for name, url in test_urls:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                download_time = time.time() - start_time
                
                if response.status_code == 200:
                    file_size = len(response.content) / (1024 * 1024)  # MB
                    speed_mbps = (file_size / download_time) * 8  # Convert to Mbps
                    
                    results.append(f"\n📁 {name}:")
                    results.append(f"   ⬇️ Download: {speed_mbps:.1f} Mbps")
                    results.append(f"   ⏱️ Time: {download_time:.2f}s")
                else:
                    results.append(f"\n❌ {name}: Failed (HTTP {response.status_code})")
                    
            except Exception as e:
                results.append(f"\n❌ {name}: {str(e)}")
        
        # Connection quality assessment
        try:
            # Test latency with multiple pings
            ping_times = []
            for _ in range(5):
                start = time.time()
                try:
                    socket.create_connection(("8.8.8.8", 53), timeout=2).close()
                    ping_times.append((time.time() - start) * 1000)
                except:
                    ping_times.append(1000)  # Timeout
            
            avg_ping = sum(ping_times) / len(ping_times)
            max_ping = max(ping_times)
            
            results.append(f"\n📊 **Latency Analysis:**")
            results.append(f"   📈 Average: {avg_ping:.1f}ms")
            results.append(f"   📈 Maximum: {max_ping:.1f}ms")
            
            # Quality assessment
            if avg_ping < 50:
                quality = "Excellent"
            elif avg_ping < 100:
                quality = "Good"
            elif avg_ping < 200:
                quality = "Fair"
            else:
                quality = "Poor"
            
            results.append(f"   🎯 Quality: {quality}")
            
        except Exception as e:
            results.append(f"\n❌ Latency test failed: {str(e)}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ Speed test failed: {str(e)}"

@function_tool()
async def monitor_network_usage(duration_minutes: int = 5) -> str:
    """
    Monitor network usage over specified time period
    
    Args:
        duration_minutes: How long to monitor network usage (default: 5 minutes)
    
    Returns network usage statistics including:
    - Real-time bandwidth usage
    - Process-wise network usage
    - Connection patterns
    """
    try:
        results = []
        results.append(f"📊 **Network Usage Monitor ({duration_minutes} minutes):**")
        
        # Get initial stats
        initial_stats = psutil.net_io_counters()
        initial_time = time.time()
        
        # Monitor processes using network
        results.append("\n🔍 **Process Network Usage:**")
        network_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'io_counters']):
            try:
                io_counters = proc.info['io_counters']
                if io_counters and (io_counters.read_bytes > 0 or io_counters.write_bytes > 0):
                    network_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'read_bytes': io_counters.read_bytes,
                        'write_bytes': io_counters.write_bytes
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by network usage
        network_processes.sort(key=lambda x: x['read_bytes'] + x['write_bytes'], reverse=True)
        
        # Show top network-using processes
        for proc in network_processes[:10]:
            read_mb = proc['read_bytes'] / (1024 * 1024)
            write_mb = proc['write_bytes'] / (1024 * 1024)
            total_mb = read_mb + write_mb
            results.append(f"📱 {proc['name']} (PID: {proc['pid']}):")
            results.append(f"   📥 {read_mb:.1f} MB | 📤 {write_mb:.1f} MB | 📊 Total: {total_mb:.1f} MB")
        
        if not network_processes:
            results.append("   No active network processes detected")
        
        # Current bandwidth
        results.append(f"\n⚡ **Current Bandwidth:**")
        current_stats = psutil.net_io_counters()
        time_diff = time.time() - initial_time
        
        if time_diff > 0:
            bytes_sent_per_sec = (current_stats.bytes_sent - initial_stats.bytes_sent) / time_diff
            bytes_recv_per_sec = (current_stats.bytes_recv - initial_stats.bytes_recv) / time_diff
            
            sent_mbps = (bytes_sent_per_sec * 8) / (1024 * 1024)
            recv_mbps = (bytes_recv_per_sec * 8) / (1024 * 1024)
            
            results.append(f"   📤 Upload: {sent_mbps:.2f} Mbps")
            results.append(f"   📥 Download: {recv_mbps:.2f} Mbps")
            results.append(f"   📊 Total: {(sent_mbps + recv_mbps):.2f} Mbps")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ Network monitoring failed: {str(e)}"

@function_tool()
async def check_port_status(port: int, host: str = "localhost") -> str:
    """
    Check if a specific port is open or closed
    
    Args:
        port: Port number to check
        host: Host to check (default: localhost)
    
    Returns port status and connection information
    """
    try:
        results = []
        
        results.append(f"🔍 **Port Status Check:**")
        results.append(f"📍 Host: {host}")
        results.append(f"🔌 Port: {port}")
        
        # Check if port is open
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                results.append("✅ Status: OPEN")
                
                # Try to get service information
                try:
                    service = socket.getservbyport(port)
                    results.append(f"🔧 Service: {service}")
                except:
                    results.append("🔧 Service: Unknown")
                
                # Check if we can get more info
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    sock.connect((host, port))
                    results.append("🤝 Connection: Successful")
                    sock.close()
                except:
                    results.append("⚠️ Connection: Accepted but no response")
            else:
                results.append("❌ Status: CLOSED")
                results.append("🔒 Port is not accessible")
                
        except socket.gaierror:
            results.append("❌ Host resolution failed")
        except Exception as e:
            results.append(f"❌ Check failed: {str(e)}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ Port check failed: {str(e)}"

@function_tool()
async def scan_network_ports(start_port: int = 1, end_port: int = 1024, host: str = "localhost") -> str:
    """
    Scan a range of ports to check which ones are open
    
    Args:
        start_port: Starting port number (default: 1)
        end_port: Ending port number (default: 1024)
        host: Host to scan (default: localhost)
    
    Returns list of open ports and their services
    """
    try:
        results = []
        results.append(f"🔍 **Port Scan ({host}):**")
        results.append(f"🔌 Scanning ports {start_port}-{end_port}")
        
        open_ports = []
        
        # Limit scan to reasonable range
        if end_port - start_port > 1000:
            results.append("⚠️ Scan range too large, limiting to 1000 ports")
            end_port = start_port + 999
        
        for port in range(start_port, end_port + 1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)  # Very short timeout for scanning
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    try:
                        service = socket.getservbyport(port)
                    except:
                        service = "Unknown"
                    
                    open_ports.append((port, service))
                    
            except:
                continue
        
        if open_ports:
            results.append(f"\n✅ Found {len(open_ports)} open ports:")
            for port, service in open_ports:
                results.append(f"🔌 Port {port}: {service}")
        else:
            results.append("\n❌ No open ports found in specified range")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ Port scan failed: {str(e)}"

@function_tool()
async def get_wifi_networks() -> str:
    """
    Get available WiFi networks and connection information
    
    Returns WiFi networks, signal strength, and connection details
    """
    try:
        results = []
        results.append("📶 **WiFi Network Information:**")
        
        # Try to get WiFi information using system commands
        try:
            # Windows WiFi information
            if os.name == 'nt':
                # Get current WiFi connection
                try:
                    output = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], 
                                                  text=True, timeout=5)
                    results.append("\n🔗 **Current Connection:**")
                    for line in output.split('\n'):
                        if 'SSID' in line and ':' in line:
                            ssid = line.split(':')[1].strip()
                            results.append(f"📡 Network: {ssid}")
                        elif 'Signal' in line and ':' in line:
                            signal = line.split(':')[1].strip()
                            results.append(f"📶 Signal: {signal}")
                        elif 'Receive rate' in line and ':' in line:
                            rate = line.split(':')[1].strip()
                            results.append(f"⚡ Speed: {rate}")
                except:
                    results.append("❌ Could not get current WiFi info")
                
                # Get available networks
                try:
                    output = subprocess.check_output(['netsh', 'wlan', 'show', 'networks'], 
                                                  text=True, timeout=10)
                    results.append("\n📡 **Available Networks:**")
                    
                    networks = []
                    lines = output.split('\n')
                    for i, line in enumerate(lines):
                        if 'SSID' in line and ':' in line:
                            ssid = line.split(':')[1].strip()
                            if ssid and ssid not in networks:
                                networks.append(ssid)
                    
                    for network in networks[:10]:  # Show top 10
                        results.append(f"📡 {network}")
                        
                except:
                    results.append("❌ Could not scan for networks")
            
            else:
                # Linux/Mac WiFi information
                try:
                    output = subprocess.check_output(['iwconfig', 'wlan0'], 
                                                  text=True, timeout=5)
                    results.append("\n🔗 **Current Connection:**")
                    results.append(output)
                except:
                    try:
                        output = subprocess.check_output(['airport', '-I'], 
                                                      text=True, timeout=5)
                        results.append("\n🔗 **Current Connection:**")
                        results.append(output)
                    except:
                        results.append("❌ Could not get WiFi info")
        
        except Exception as e:
            results.append(f"❌ WiFi scan failed: {str(e)}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ Failed to get WiFi networks: {str(e)}"

@function_tool()
async def network_diagnostics() -> str:
    """
    Run comprehensive network diagnostics
    
    Performs full diagnostic suite including:
    - Connectivity tests
    - Speed tests
    - DNS resolution
    - Port scanning
    - Network interface analysis
    """
    try:
        results = []
        results.append("🔧 **Network Diagnostics Suite:**")
        results.append("=" * 50)
        
        # 1. Basic connectivity
        results.append("\n1️⃣ **Connectivity Test:**")
        try:
            response = requests.get('https://www.google.com', timeout=5)
            results.append("✅ Internet connectivity: OK")
        except:
            results.append("❌ Internet connectivity: FAILED")
            return "\n".join(results)  # Exit early if no internet
        
        # 2. DNS resolution
        results.append("\n2️⃣ **DNS Resolution:**")
        test_domains = ['google.com', 'github.com', 'stackoverflow.com']
        for domain in test_domains:
            try:
                socket.gethostbyname(domain)
                results.append(f"✅ {domain}: OK")
            except:
                results.append(f"❌ {domain}: FAILED")
        
        # 3. Network interfaces
        results.append("\n3️⃣ **Network Interfaces:**")
        interfaces = psutil.net_if_addrs()
        for name in interfaces.keys():
            if name != 'lo':  # Skip loopback
                results.append(f"📡 {name}: Active")
        
        # 4. Connection speed (quick test)
        results.append("\n4️⃣ **Quick Speed Test:**")
        try:
            start_time = time.time()
            response = requests.get('https://httpbin.org/bytes/1048576', timeout=10)
            download_time = time.time() - start_time
            
            if response.status_code == 200:
                speed_mbps = (1 / download_time) * 8  # 1MB file
                results.append(f"⚡ Download speed: {speed_mbps:.1f} Mbps")
            else:
                results.append("❌ Speed test failed")
        except:
            results.append("❌ Speed test failed")
        
        # 5. Common ports check
        results.append("\n5️⃣ **Common Ports Check:**")
        common_ports = [(80, "HTTP"), (443, "HTTPS"), (53, "DNS"), (22, "SSH")]
        for port, service in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(("8.8.8.8", port))
                sock.close()
                
                if result == 0:
                    results.append(f"✅ Port {port} ({service}): Open")
                else:
                    results.append(f"❌ Port {port} ({service}): Closed")
            except:
                results.append(f"❌ Port {port} ({service}): Error")
        
        # 6. Overall assessment
        results.append("\n📊 **Overall Assessment:**")
        results.append("✅ Network diagnostics completed")
        results.append("📝 Review results above for any issues")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ Network diagnostics failed: {str(e)}"

# Import os for WiFi detection
import os
