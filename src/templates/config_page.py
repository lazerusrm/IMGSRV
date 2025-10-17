"""
Analytics Configuration Web Interface.

Provides a web-based interface for configuring analytics settings,
location, and overlay preferences.
"""

from datetime import datetime
from typing import Dict, Any

import structlog
from fastapi import Request
from fastapi.responses import HTMLResponse

logger = structlog.get_logger(__name__)


def create_config_page_html(config_data: Dict[str, Any]) -> str:
    """Create the analytics configuration page HTML."""
    
    # Extract current values
    analytics_enabled = config_data.get("analytics_enabled", True)
    weather_latitude = config_data.get("weather_latitude", 40.0)
    weather_longitude = config_data.get("weather_longitude", -111.8)
    location_name = config_data.get("weather_location_name", "Woodland Hills, Utah")
    overlay_style = config_data.get("analytics_overlay_style", "minimal")
    overlay_enabled = config_data.get("analytics_overlay_enabled", True)
    update_interval = config_data.get("analytics_update_interval_minutes", 5)
    snow_threshold = config_data.get("snow_detection_threshold", 0.7)
    ice_temp = config_data.get("ice_warning_temperature", 32)
    hazardous_depth = config_data.get("hazardous_snow_depth", 2.0)
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snow Load Analytics Configuration</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header h2 {{
            font-size: 1.2em;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .form-section {{
            margin-bottom: 40px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #3498db;
        }}
        
        .form-section h3 {{
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.4em;
            display: flex;
            align-items: center;
        }}
        
        .form-section h3::before {{
            content: "⚙️";
            margin-right: 10px;
            font-size: 1.2em;
        }}
        
        .form-group {{
            margin-bottom: 20px;
        }}
        
        .form-group label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #34495e;
        }}
        
        .form-group input, .form-group select {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }}
        
        .form-group input:focus, .form-group select:focus {{
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }}
        
        .form-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        
        .checkbox-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .checkbox-group input[type="checkbox"] {{
            width: auto;
            transform: scale(1.2);
        }}
        
        .help-text {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        
        .button-group {{
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }}
        
        .btn {{
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(52, 152, 219, 0.3);
        }}
        
        .btn-secondary {{
            background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
            color: white;
        }}
        
        .btn-secondary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(149, 165, 166, 0.3);
        }}
        
        .btn-danger {{
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
        }}
        
        .btn-danger:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(231, 76, 60, 0.3);
        }}
        
        .status-message {{
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-weight: 600;
            display: none;
        }}
        
        .status-success {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        
        .status-error {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        
        .location-info {{
            background: #e8f4fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }}
        
        .location-info h4 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .coordinates {{
            font-family: monospace;
            background: white;
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }}
        
        @media (max-width: 768px) {{
            .form-row {{
                grid-template-columns: 1fr;
            }}
            
            .button-group {{
                flex-direction: column;
            }}
            
            .container {{
                margin: 10px;
            }}
            
            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Snow Load Analytics</h1>
            <h2>Configuration Dashboard</h2>
        </div>
        
        <div class="content">
            <div id="status-message" class="status-message"></div>
            
            <form id="config-form">
                <!-- Location Settings -->
                <div class="form-section">
                    <h3>Location Settings</h3>
                    
                    <div class="location-info">
                        <h4>Current Location</h4>
                        <p><strong>{location_name}</strong></p>
                        <p class="coordinates">{weather_latitude}, {weather_longitude}</p>
                    </div>
                    
                    <div class="form-group">
                        <label for="location_name">Location Name</label>
                        <input type="text" id="location_name" name="location_name" value="{location_name}" required>
                        <div class="help-text">Descriptive name for this monitoring location</div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="weather_latitude">Latitude</label>
                            <input type="number" id="weather_latitude" name="weather_latitude" 
                                   value="{weather_latitude}" step="0.0001" min="-90" max="90" required>
                            <div class="help-text">Latitude coordinate (-90 to 90)</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="weather_longitude">Longitude</label>
                            <input type="number" id="weather_longitude" name="weather_longitude" 
                                   value="{weather_longitude}" step="0.0001" min="-180" max="180" required>
                            <div class="help-text">Longitude coordinate (-180 to 180)</div>
                        </div>
                    </div>
                </div>
                
                <!-- Analytics Settings -->
                <div class="form-section">
                    <h3>Analytics Settings</h3>
                    
                    <div class="form-group">
                        <div class="checkbox-group">
                            <input type="checkbox" id="analytics_enabled" name="analytics_enabled" 
                                   {"checked" if analytics_enabled else ""}>
                            <label for="analytics_enabled">Enable Snow Load Analytics</label>
                        </div>
                        <div class="help-text">Enable computer vision analysis of snow coverage and road conditions</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="analytics_update_interval_minutes">Update Interval (minutes)</label>
                        <select id="analytics_update_interval_minutes" name="analytics_update_interval_minutes">
                            <option value="1" {"selected" if update_interval == 1 else ""}>1 minute</option>
                            <option value="5" {"selected" if update_interval == 5 else ""}>5 minutes</option>
                            <option value="10" {"selected" if update_interval == 10 else ""}>10 minutes</option>
                            <option value="15" {"selected" if update_interval == 15 else ""}>15 minutes</option>
                            <option value="30" {"selected" if update_interval == 30 else ""}>30 minutes</option>
                        </select>
                        <div class="help-text">How often to update analytics data</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="snow_detection_threshold">Snow Detection Threshold</label>
                        <input type="range" id="snow_detection_threshold" name="snow_detection_threshold" 
                               value="{snow_threshold}" min="0" max="1" step="0.1">
                        <div class="help-text">Sensitivity for snow detection (0.0 = very sensitive, 1.0 = less sensitive)</div>
                    </div>
                </div>
                
                <!-- Overlay Settings -->
                <div class="form-section">
                    <h3>Overlay Settings</h3>
                    
                    <div class="form-group">
                        <div class="checkbox-group">
                            <input type="checkbox" id="analytics_overlay_enabled" name="analytics_overlay_enabled" 
                                   {"checked" if overlay_enabled else ""}>
                            <label for="analytics_overlay_enabled">Enable Analytics Overlays</label>
                        </div>
                        <div class="help-text">Show analytics data as overlays on camera images</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="analytics_overlay_style">Overlay Style</label>
                        <select id="analytics_overlay_style" name="analytics_overlay_style">
                            <option value="full" {"selected" if overlay_style == "full" else ""}>Full Analytics Panel</option>
                            <option value="minimal" {"selected" if overlay_style == "minimal" else ""}>Minimal Timestamp</option>
                            <option value="mobile" {"selected" if overlay_style == "mobile" else ""}>Mobile Optimized</option>
                            <option value="none" {"selected" if overlay_style == "none" else ""}>No Overlay</option>
                        </select>
                        <div class="help-text">Style of analytics overlay on images</div>
                    </div>
                </div>
                
                <!-- Warning Thresholds -->
                <div class="form-section">
                    <h3>Warning Thresholds</h3>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="ice_warning_temperature">Ice Warning Temperature (°F)</label>
                            <input type="number" id="ice_warning_temperature" name="ice_warning_temperature" 
                                   value="{ice_temp}" min="-50" max="100" step="1">
                            <div class="help-text">Temperature below which ice warnings are issued</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="hazardous_snow_depth">Hazardous Snow Depth (inches)</label>
                            <input type="number" id="hazardous_snow_depth" name="hazardous_snow_depth" 
                                   value="{hazardous_depth}" min="0" max="50" step="0.1">
                            <div class="help-text">Snow depth above which road is considered hazardous</div>
                        </div>
                    </div>
                </div>
                
                <div class="button-group">
                    <button type="submit" class="btn btn-primary">Save Configuration</button>
                    <button type="button" class="btn btn-secondary" onclick="resetToDefaults()">Reset to Defaults</button>
                    <a href="/" class="btn btn-secondary">Back to Monitor</a>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        // Show status message
        function showStatus(message, type) {{
            const statusDiv = document.getElementById('status-message');
            statusDiv.textContent = message;
            statusDiv.className = `status-message status-${{type}}`;
            statusDiv.style.display = 'block';
            
            setTimeout(() => {{
                statusDiv.style.display = 'none';
            }}, 5000);
        }}
        
        // Handle form submission
        document.getElementById('config-form').addEventListener('submit', async function(e) {{
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const config = Object.fromEntries(formData.entries());
            
            // Convert checkbox values
            config.analytics_enabled = document.getElementById('analytics_enabled').checked;
            config.analytics_overlay_enabled = document.getElementById('analytics_overlay_enabled').checked;
            
            // Convert numeric values
            config.weather_latitude = parseFloat(config.weather_latitude);
            config.weather_longitude = parseFloat(config.weather_longitude);
            config.analytics_update_interval_minutes = parseInt(config.analytics_update_interval_minutes);
            config.snow_detection_threshold = parseFloat(config.snow_detection_threshold);
            config.ice_warning_temperature = parseFloat(config.ice_warning_temperature);
            config.hazardous_snow_depth = parseFloat(config.hazardous_snow_depth);
            
            try {{
                const response = await fetch('/config/analytics', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify(config)
                }});
                
                const result = await response.json();
                
                if (result.status === 'success') {{
                    showStatus('Configuration saved successfully!', 'success');
                }} else {{
                    showStatus(`Error: ${{result.message}}`, 'error');
                }}
            }} catch (error) {{
                showStatus(`Error: ${{error.message}}`, 'error');
            }}
        }});
        
        // Reset to defaults
        async function resetToDefaults() {{
            if (confirm('Are you sure you want to reset all settings to defaults?')) {{
                try {{
                    const response = await fetch('/config/analytics/reset', {{
                        method: 'POST'
                    }});
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {{
                        showStatus('Configuration reset to defaults!', 'success');
                        setTimeout(() => {{
                            location.reload();
                        }}, 2000);
                    }} else {{
                        showStatus(`Error: ${{result.message}}`, 'error');
                    }}
                }} catch (error) {{
                    showStatus(`Error: ${{error.message}}`, 'error');
                }}
            }}
        }}
        
        // Update slider value display
        document.getElementById('snow_detection_threshold').addEventListener('input', function(e) {{
            const value = parseFloat(e.target.value);
            e.target.nextElementSibling.textContent = 
                `Sensitivity for snow detection (${{value.toFixed(1)}} - ${{value < 0.5 ? 'very sensitive' : value < 0.8 ? 'moderate' : 'less sensitive'}})`;
        }});
    </script>
</body>
</html>
"""
    
    return html
