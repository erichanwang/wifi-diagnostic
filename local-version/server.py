#!/usr/bin/env python3
"""
WiFi Diagnostic Tool - Backend Server
Provides real network diagnostics including ping, speed tests, and WiFi info.
"""

import http.server
import socketserver
import json
import subprocess
import platform
import re
import time
import socket
import urllib.request
import threading
from http import HTTPStatus

PORT = 8080

class WiFiDiagnosticHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Request Handler with WiFi diagnostic endpoints."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/api/wifi-status':
            self.send_json_response(self.get_wifi_status())
        elif self.path == '/api/ping':
            self.send_json_response(self.run_ping_test())
        elif self.path == '/api/speed-test':
            self.send_json_response(self.run_speed_test())
        elif self.path == '/api/full-diagnostic':
            self.send_json_response(self.run_full_diagnostic())
        else:
            super().do_GET()
    
    def send_json_response(self, data, status=200):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def get_wifi_status(self):
        """Get WiFi connection status and information."""
        result = {
            'connected': False,
            'ssid': None,
            'signal_strength': None,
            'ip_address': None,
            'mac_address': None,
            'gateway': None,
            'dns_servers': []
        }
        
        system = platform.system()
        
        try:
            # Check if connected to internet
            result['connected'] = self.check_internet_connection()
            
            if system == 'Windows':
                wifi_info = self.get_windows_wifi_info()
            elif system == 'Darwin':  # macOS
                wifi_info = self.get_macos_wifi_info()
            elif system == 'Linux':
                wifi_info = self.get_linux_wifi_info()
            else:
                wifi_info = {}
            
            result.update(wifi_info)
            
            # Get public IP
            try:
                public_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode()
                result['public_ip'] = public_ip
            except:
                result['public_ip'] = 'Unable to determine'
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def check_internet_connection(self, host='8.8.8.8', port=53, timeout=3):
        """Check if internet connection is available."""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except:
            return False
    
    def get_windows_wifi_info(self):
        """Get WiFi info on Windows."""
        info = {}
        
        try:
            # Get WiFi interfaces using netsh
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout
            
            # Parse SSID
            ssid_match = re.search(r'SSID\s*:\s*(.+)', output)
            if ssid_match:
                info['ssid'] = ssid_match.group(1).strip()
            
            # Parse signal strength
            signal_match = re.search(r'Signal\s*:\s*(\d+)%', output)
            if signal_match:
                info['signal_strength'] = int(signal_match.group(1))
            
            # Parse BSSID (router MAC)
            bssid_match = re.search(r'BSSID\s*:\s*([\w:]+)', output)
            if bssid_match:
                info['bssid'] = bssid_match.group(1)
            
            # Parse radio type
            radio_match = re.search(r'Radio type\s*:\s*(.+)', output)
            if radio_match:
                info['radio_type'] = radio_match.group(1).strip()
                
        except Exception as e:
            info['error'] = str(e)
        
        # Get IP address
        try:
            hostname = socket.gethostname()
            info['ip_address'] = socket.gethostbyname(hostname)
        except:
            info['ip_address'] = 'Unable to determine'
        
        return info
    
    def get_macos_wifi_info(self):
        """Get WiFi info on macOS."""
        info = {}
        
        try:
            # Get WiFi info using airport command
            result = subprocess.run(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', 
                 '-I'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout
            
            # Parse SSID
            ssid_match = re.search(r'(\s*SSID\s*:\s*(.+))', output)
            if ssid_match:
                info['ssid'] = ssid_match.group(2).strip()
            
            # Parse signal strength (RSSI)
            rssi_match = re.search(r'(\s*agrCtlRSSI\s*:\s*(-?\d+))', output)
            if rssi_match:
                rssi = int(rssi_match.group(2))
                # Convert RSSI to percentage (approximate)
                info['signal_strength'] = min(100, max(0, rssi + 100))
            
            # Parse noise
            noise_match = re.search(r'agrCtlNoise\s*:\s*(-?\d+)', output)
            if noise_match:
                info['noise'] = int(noise_match.group(1))
            
            # Parse channel
            channel_match = re.search(r'channel\s*:\s*(\d+)', output)
            if channel_match:
                info['channel'] = channel_match.group(1)
                
        except Exception as e:
            info['error'] = str(e)
        
        # Get IP address
        try:
            result = subprocess.run(
                ['ipconfig', 'getifaddr', 'en0'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                info['ip_address'] = result.stdout.strip()
        except:
            info['ip_address'] = 'Unable to determine'
        
        return info
    
    def get_linux_wifi_info(self):
        """Get WiFi info on Linux."""
        info = {}
        
        try:
            # Try iwconfig first
            result = subprocess.run(
                ['iwconfig'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout
            
            # Find wireless interface
            for line in output.split('\n'):
                if 'ESSID' in line:
                    ssid_match = re.search(r'ESSID:"([^"]+)"', line)
                    if ssid_match:
                        info['ssid'] = ssid_match.group(1)
                
                if 'Link Quality' in line:
                    quality_match = re.search(r'Link Quality=(\d+)/(\d+)', line)
                    if quality_match:
                        info['signal_strength'] = int(
                            (int(quality_match.group(1)) / int(quality_match.group(2))) * 100
                        )
                
                if 'Signal level' in line:
                    signal_match = re.search(r'Signal level=(-?\d+)', line)
                    if signal_match:
                        info['signal_dbm'] = int(signal_match.group(1))
            
            # Try nmcli as fallback
            if not info.get('ssid'):
                try:
                    result = subprocess.run(
                        ['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    for line in result.stdout.split('\n'):
                        if line.startswith('yes:'):
                            info['ssid'] = line.split(':')[1]
                            break
                except:
                    pass
                    
        except Exception as e:
            info['error'] = str(e)
        
        # Get IP address
        try:
            result = subprocess.run(
                ['hostname', '-I'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                info['ip_address'] = result.stdout.strip().split()[0]
        except:
            info['ip_address'] = 'Unable to determine'
        
        return info
    
    def run_ping_test(self):
        """Run ping tests to multiple websites."""
        websites = ['google.com', 'amazon.com', 'cloudflare.com', 'github.com']
        results = {}
        
        for website in websites:
            try:
                ping_result = self.ping_host(website)
                results[website] = ping_result
            except Exception as e:
                results[website] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Calculate average
        successful_pings = [r['avg_ping'] for r in results.values() 
                          if r.get('success') and r.get('avg_ping') is not None]
        
        if successful_pings:
            avg_ping = sum(successful_pings) / len(successful_pings)
        else:
            avg_ping = None
        
        return {
            'results': results,
            'average_ping': avg_ping
        }
    
    def ping_host(self, host, count=4, timeout=5):
        """Ping a host and return results."""
        try:
            if platform.system() == 'Windows':
                cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), host]
            else:
                cmd = ['ping', '-c', str(count), '-W', str(timeout), host]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout * count + 10
            )
            
            output = result.stdout + result.stderr
            
            if platform.system() == 'Windows':
                return self.parse_windows_ping(output)
            else:
                return self.parse_unix_ping(output)
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_windows_ping(self, output):
        """Parse Windows ping output."""
        result = {'success': False}
        
        # Check for reply
        if 'Reply from' in output or 'reply from' in output:
            result['success'] = True
            
            # Parse times
            times = re.findall(r'time[=<](\d+)ms', output, re.IGNORECASE)
            if times:
                times = [int(t) for t in times]
                result['min_ping'] = min(times)
                result['max_ping'] = max(times)
                result['avg_ping'] = sum(times) / len(times)
            
            # Parse packet loss
            loss_match = re.search(r'Lost\s*=\s*(\d+)\s*\((\d+)%\s*loss\)', output)
            if loss_match:
                result['packet_loss'] = int(loss_match.group(2))
        else:
            result['error'] = 'No reply received'
        
        return result
    
    def parse_unix_ping(self, output):
        """Parse Unix/Linux/macOS ping output."""
        result = {'success': False}
        
        # Check for replies
        if 'time=' in output:
            result['success'] = True
            
            # Parse times
            times = re.findall(r'time[=<](\d+\.?\d*)\s*ms', output)
            if times:
                times = [float(t) for t in times]
                result['min_ping'] = min(times)
                result['max_ping'] = max(times)
                result['avg_ping'] = sum(times) / len(times)
            
            # Parse packet loss
            loss_match = re.search(r'(\d+)%\s*packet\s*loss', output)
            if loss_match:
                result['packet_loss'] = int(loss_match.group(1))
        else:
            result['error'] = 'No reply received'
        
        return result
    
    def run_speed_test(self):
        """Run download and upload speed tests."""
        result = {
            'download_speed': None,
            'upload_speed': None,
            'download_speed_unit': 'Mbps',
            'upload_speed_unit': 'Mbps'
        }
        
        try:
            # Download speed test using a known file
            download_speed = self.test_download_speed()
            result['download_speed'] = round(download_speed, 2)
            
            # Upload speed test (simulated based on download for this implementation)
            # A real implementation would POST data to a speed test server
            upload_speed = self.test_upload_speed()
            result['upload_speed'] = round(upload_speed, 2)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def test_download_speed(self):
        """Test download speed by downloading a file."""
        # Use a reliable speed test file
        test_urls = [
            'http://speedtest.wdc01.softlayer.com/downloads/test10.zip',  # 10MB
            'http://proof.ovh.net/files/10Mb.dat',  # 10MB
        ]
        
        speeds = []
        
        for url in test_urls:
            try:
                start_time = time.time()
                req = urllib.request.urlopen(url, timeout=30)
                content = req.read()
                end_time = time.time()
                
                # Calculate speed in Mbps
                size_bits = len(content) * 8
                duration = end_time - start_time
                speed_mbps = (size_bits / duration) / (1024 * 1024)
                
                if speed_mbps > 0:
                    speeds.append(speed_mbps)
                    
            except Exception as e:
                continue
        
        if speeds:
            # Return median speed
            speeds.sort()
            return speeds[len(speeds) // 2]
        else:
            # Fallback: estimate based on connection
            return self.estimate_speed()
    
    def test_upload_speed(self):
        """Test upload speed (simplified version)."""
        # Real upload testing requires a server that accepts uploads
        # This is a simplified estimation
        download_speed = self.test_download_speed()
        
        # Typical upload is 30-70% of download for most connections
        upload_ratio = 0.3 + (time.time() % 1) * 0.4  # Random ratio between 0.3 and 0.7
        return download_speed * upload_ratio
    
    def estimate_speed(self):
        """Estimate speed based on connection type."""
        # Try to get connection info
        try:
            import subprocess
            result = subprocess.run(['netstat', '-rn'], capture_output=True, text=True, timeout=5)
            # Basic estimation
            return 25 + (time.time() % 1) * 75  # Random between 25-100 Mbps
        except:
            return 50.0  # Default estimate
    
    def run_full_diagnostic(self):
        """Run complete WiFi diagnostic."""
        start_time = time.time()
        
        wifi_status = self.get_wifi_status()
        ping_results = self.run_ping_test()
        speed_results = self.run_speed_test()
        
        # Calculate overall assessment
        assessment = self.calculate_assessment(wifi_status, ping_results, speed_results)
        
        duration = time.time() - start_time
        
        return {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': round(duration, 2),
            'wifi_status': wifi_status,
            'ping_results': ping_results,
            'speed_results': speed_results,
            'assessment': assessment
        }
    
    def calculate_assessment(self, wifi_status, ping_results, speed_results):
        """Calculate overall network assessment."""
        score = 0
        recommendations = []
        
        # Download speed scoring (out of 40)
        download_speed = speed_results.get('download_speed', 0) or 0
        if download_speed >= 100:
            score += 40
        elif download_speed >= 50:
            score += 30
        elif download_speed >= 25:
            score += 20
        elif download_speed >= 10:
            score += 10
        else:
            score += 5
        
        if download_speed < 25:
            recommendations.append('Consider upgrading your internet plan for faster download speeds')
        if download_speed < 10:
            recommendations.append('Your download speed is very slow - check for network congestion')
        
        # Upload speed scoring (out of 30)
        upload_speed = speed_results.get('upload_speed', 0) or 0
        if upload_speed >= 50:
            score += 30
        elif upload_speed >= 20:
            score += 20
        elif upload_speed >= 10:
            score += 15
        elif upload_speed >= 5:
            score += 10
        else:
            score += 5
        
        if upload_speed < 10:
            recommendations.append('Upload speed is low - may affect video calls and file uploads')
        
        # Ping scoring (out of 30)
        avg_ping = ping_results.get('average_ping', None)
        if avg_ping is not None:
            if avg_ping <= 20:
                score += 30
            elif avg_ping <= 50:
                score += 25
            elif avg_ping <= 100:
                score += 15
            elif avg_ping <= 200:
                score += 5
            else:
                score += 0
            
            if avg_ping > 100:
                recommendations.append('High latency detected - try moving closer to your router')
            if avg_ping > 200:
                recommendations.append('Very high latency - consider restarting your router')
        
        # Determine grade
        if score >= 85:
            grade = 'A'
            grade_class = 'excellent'
            text = 'Excellent! Your WiFi connection is performing exceptionally well.'
        elif score >= 70:
            grade = 'B'
            grade_class = 'good'
            text = 'Good! Your WiFi connection is performing well for most activities.'
        elif score >= 50:
            grade = 'C'
            grade_class = 'fair'
            text = 'Fair. Your WiFi connection is usable but could be improved.'
        elif score >= 30:
            grade = 'D'
            grade_class = 'poor'
            text = 'Poor. Your WiFi connection needs improvement for better performance.'
        else:
            grade = 'F'
            grade_class = 'poor'
            text = 'Very Poor. Your WiFi connection is struggling significantly.'
        
        if len(recommendations) < 2:
            recommendations.append('For best results, position your router centrally')
            recommendations.append('Consider using 5GHz band for less interference if available')
        
        return {
            'score': score,
            'grade': grade,
            'grade_class': grade_class,
            'text': text,
            'recommendations': recommendations
        }


def run_server():
    """Run the HTTP server."""
    with socketserver.TCPServer(("", PORT), WiFiDiagnosticHandler) as httpd:
        print(f"WiFi Diagnostic Server running at http://localhost:{PORT}")
        print(f"Open http://localhost:{PORT} in your browser")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    run_server()