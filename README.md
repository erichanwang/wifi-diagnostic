# WiFi Diagnostic Tool

A comprehensive WiFi diagnostic tool that tests your network connection quality and speed. The tool includes both a web interface and a Python backend for accurate network diagnostics.

## Features

- **WiFi Connection Status**: Check if you're connected and get network details (SSID, signal strength, IP address)
- **Ping Tests**: Measure latency to popular websites (Google, Amazon, Cloudflare, GitHub)
- **Speed Tests**: Test download and upload speeds
- **Overall Assessment**: Get a letter grade (A-F) with personalized recommendations
- **Export Results**: Download test results as JSON

## Quick Start

### Option 1: Web-Only (No Installation)

Simply open `index.html` in your web browser. The JavaScript version will run basic diagnostics using browser APIs.

```bash
# On Windows
start index.html

# On macOS
open index.html

# On Linux
xdg-open index.html
```

### Option 2: Full Version with Python Backend

For more accurate results including real ping tests and speed measurements, use the Python backend.

#### Prerequisites

- Python 3.6 or higher
- pip (Python package manager)

#### Running the Server

1. Open a terminal/command prompt in this directory
2. Run the server:

```bash
python server.py
```

3. Open your browser and go to: `http://localhost:8080`

The server will serve the web interface and provide real network diagnostics.

## API Endpoints

The Python server provides the following API endpoints:

| Endpoint | Description |
|----------|-------------|
| `/api/wifi-status` | Get WiFi connection status and details |
| `/api/ping` | Run ping tests to multiple websites |
| `/api/speed-test` | Run download/upload speed tests |
| `/api/full-diagnostic` | Run complete diagnostic suite |

### Example API Response

```json
{
  "timestamp": "2024-01-15 10:30:45",
  "duration_seconds": 12.5,
  "wifi_status": {
    "connected": true,
    "ssid": "MyNetwork",
    "signal_strength": 85,
    "ip_address": "192.168.1.100"
  },
  "ping_results": {
    "results": {
      "google.com": {
        "success": true,
        "avg_ping": 23.5,
        "min_ping": 20,
        "max_ping": 28
      }
    },
    "average_ping": 35.2
  },
  "speed_results": {
    "download_speed": 85.5,
    "upload_speed": 42.3
  },
  "assessment": {
    "grade": "B",
    "text": "Good! Your WiFi connection is performing well."
  }
}
```

## Understanding Results

### Ping Times
- **Good**: < 50ms (green)
- **Fair**: 50-100ms (yellow)
- **Poor**: > 100ms (red)

### Speed Ratings
- **Excellent**: > 100 Mbps download
- **Good**: 50-100 Mbps download
- **Fair**: 25-50 Mbps download
- **Poor**: < 25 Mbps download

### Overall Grade
- **A** (85+ points): Excellent performance
- **B** (70-84 points): Good performance
- **C** (50-69 points): Fair performance
- **D** (30-49 points): Poor performance
- **F** (< 30 points): Very poor performance

## Platform Support

| Feature | Windows | macOS | Linux |
|---------|---------|-------|-------|
| WiFi Status | ✅ | ✅ | ✅ |
| Ping Tests | ✅ | ✅ | ✅ |
| Speed Tests | ✅ | ✅ | ✅ |
| SSID Detection | ✅ | ✅ | ✅ |

## Troubleshooting

### Server won't start
- Make sure port 8080 is not already in use
- Check if you have Python installed: `python --version`

### Speed test fails
- The test requires downloading files from external servers
- Check your firewall settings
- Some networks may block speed test servers

### WiFi info not showing
- On macOS, the Airport utility must be available
- On Linux, `iwconfig` or `nmcli` must be installed
- Administrator/root privileges may be required for some features

## File Structure

```
wifi-diagnostic/
├── index.html      # Main HTML page
├── styles.css      # CSS styling (blue gradient theme)
├── app.js          # Frontend JavaScript
├── server.py       # Python backend server
└── README.md       # This file
```

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Suggestions and improvements are welcome!