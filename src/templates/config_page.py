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
    sequence_update_interval = config_data.get("sequence_update_interval_minutes", 5)
    max_images = config_data.get("max_images_per_sequence", 10)
    gif_frame_duration = config_data.get("gif_frame_duration_seconds", 1.0)
    gif_optimization = config_data.get("gif_optimization_level", "balanced")
    
    # Calculate capture interval for display
    capture_interval = (sequence_update_interval * 60) / max_images if max_images > 0 else 30
    
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
                        <label for="weather_location_name">Location Name</label>
                        <input type="text" id="weather_location_name" name="weather_location_name" value="{location_name}" required>
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
                
                <!-- Update Interval Settings -->
                <div class="form-section">
                    <h3>Update Interval Settings</h3>
                    
                    <div class="form-group">
                        <label for="sequence_update_interval_minutes">GIF Update Interval (minutes)</label>
                        <select id="sequence_update_interval_minutes" name="sequence_update_interval_minutes">
                            <option value="1" {"selected" if sequence_update_interval == 1 else ""}>1 minute</option>
                            <option value="2" {"selected" if sequence_update_interval == 2 else ""}>2 minutes</option>
                            <option value="5" {"selected" if sequence_update_interval == 5 else ""}>5 minutes</option>
                            <option value="10" {"selected" if sequence_update_interval == 10 else ""}>10 minutes</option>
                            <option value="15" {"selected" if sequence_update_interval == 15 else ""}>15 minutes</option>
                            <option value="30" {"selected" if sequence_update_interval == 30 else ""}>30 minutes</option>
                        </select>
                        <div class="help-text">How often to generate and update the GIF sequence</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="max_images_per_sequence">Images Per Sequence</label>
                        <input type="number" id="max_images_per_sequence" name="max_images_per_sequence" 
                               value="{max_images}" min="5" max="30" step="1">
                        <div class="help-text">Number of frames in each GIF (5-30)</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="gif_frame_duration_seconds">Frame Duration (seconds)</label>
                        <input type="number" id="gif_frame_duration_seconds" name="gif_frame_duration_seconds" 
                               value="{gif_frame_duration}" min="0.5" max="5.0" step="0.1">
                        <div class="help-text">How long each frame displays in the GIF</div>
                    </div>
                    
                    <div class="location-info">
                        <h4>Calculated Capture Interval</h4>
                        <p><strong>{capture_interval:.1f} seconds</strong> between photo captures</p>
                        <div class="help-text">Automatically calculated: (Update Interval × 60) ÷ Images Per Sequence</div>
                    </div>
                </div>
                
                <!-- GIF Optimization -->
                <div class="form-section">
                    <h3>GIF Optimization</h3>
                    
                    <div class="form-group">
                        <label for="gif_optimization_level">Optimization Level</label>
                        <select id="gif_optimization_level" name="gif_optimization_level">
                            <option value="low" {"selected" if gif_optimization == "low" else ""}>Low (256 colors, larger file)</option>
                            <option value="balanced" {"selected" if gif_optimization == "balanced" else ""}>Balanced (192 colors, good quality)</option>
                            <option value="aggressive" {"selected" if gif_optimization == "aggressive" else ""}>Aggressive (128 colors, smallest file)</option>
                        </select>
                        <div class="help-text">Balance between file size and image quality. All GIFs resized to 1280x720 for web.</div>
                    </div>
                </div>
                
                <!-- Debug Tools & ROI Editor -->
                <div class="form-section">
                    <h3>Road Detection & ROI Editor</h3>
                    
                    <div class="form-group">
                        <label>Live Camera Feed with ROI Editor</label>
                        <div class="help-text">Click on the image to define monitoring regions. Shows detected road boundaries (green overlay) and your custom ROI (blue overlay).</div>
                        
                        <div id="road-viz-container" style="margin-top: 15px; border: 2px solid #ddd; border-radius: 8px; padding: 15px; background: #f9f9f9;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <span style="font-weight: bold; color: #333;">Live Road Detection & ROI Editor</span>
                                <button type="button" onclick="refreshRoadVisualization()" class="btn btn-secondary" style="padding: 5px 15px;">
                                    <span id="refresh-icon">↻</span> Refresh
                                </button>
                            </div>
                            
                            <div id="viz-loading" style="display: none; text-align: center; padding: 40px; color: #666;">
                                <div style="font-size: 24px; margin-bottom: 10px;">⏳</div>
                                <div>Loading visualization...</div>
                            </div>
                            
                            <div id="viz-error" style="display: none; text-align: center; padding: 40px; color: #d32f2f;">
                                <div style="font-size: 24px; margin-bottom: 10px;">⚠️</div>
                                <div id="viz-error-message">Failed to load visualization</div>
                            </div>
                            
                            <div style="position: relative; display: inline-block; width: 100%;">
                                <img id="road-viz-image" 
                                     src="/analytics/road-boundaries?mode=raw&t={int(datetime.now().timestamp())}" 
                                     alt="Road Boundary Visualization"
                                     style="width: 100%; height: auto; border-radius: 4px; display: block; cursor: crosshair;"
                                     onload="document.getElementById('viz-loading').style.display='none'; initializeROIEditor();"
                                     onerror="showVizError();">
                                
                                <canvas id="roi-overlay-canvas" 
                                        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 10;"></canvas>
                            </div>
                            
                            <div id="viz-metadata" style="margin-top: 10px; padding: 10px; background: white; border-radius: 4px; font-size: 12px;">
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                                    <div>
                                        <strong>Road Pixels:</strong>
                                        <span id="meta-pixels">Loading...</span>
                                    </div>
                                    <div>
                                        <strong>Road Coverage:</strong>
                                        <span id="meta-percentage">Loading...</span>
                                    </div>
                                    <div>
                                        <strong>Contours:</strong>
                                        <span id="meta-contours">Loading...</span>
                                    </div>
                                    <div>
                                        <strong>Last Updated:</strong>
                                        <span id="meta-timestamp">Loading...</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- ROI Controls -->
                            <div style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;">
                                <h4 style="margin: 0 0 10px 0; color: #495057;">ROI Editor Controls</h4>
                                <div class="help-text" style="margin-bottom: 15px;">
                                    Click on the image above to define monitoring regions. Minimum 4 points, maximum 12 points. Click near the first point to close the polygon.
                                </div>
                                
                                <div class="form-group" style="margin-bottom: 15px;">
                                    <div class="checkbox-group">
                                        <input type="checkbox" id="road_roi_enabled" name="road_roi_enabled">
                                        <label for="road_roi_enabled">Enable Custom Road Monitoring Region</label>
                                    </div>
                                    <div class="help-text">Use the defined polygon for road analysis (unchecked = use default detection)</div>
                                </div>
                                
                                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px;">
                                    <button type="button" onclick="clearROIPoints()" class="btn btn-secondary">Clear Points</button>
                                    <button type="button" onclick="undoLastPoint()" class="btn btn-secondary">Undo Last</button>
                                    <button type="button" onclick="loadCurrentROI()" class="btn btn-secondary">Load Saved ROI</button>
                                    <button type="button" onclick="testROIVisualization()" class="btn btn-primary">Test ROI</button>
                                </div>
                                
                                <div id="roi-status" style="padding: 10px; background: white; border-radius: 4px; font-size: 14px;">
                                    <strong>Points:</strong> <span id="roi-point-count">0</span> / 12
                                    <span id="roi-valid" style="margin-left: 20px;"></span>
                                </div>
                                
                                <input type="hidden" id="road_roi_points" name="road_roi_points" value="">
                            </div>
                        </div>
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
            config.road_roi_enabled = document.getElementById('road_roi_enabled').checked;
            
            // Convert numeric values
            config.weather_latitude = parseFloat(config.weather_latitude);
            config.weather_longitude = parseFloat(config.weather_longitude);
            config.analytics_update_interval_minutes = parseInt(config.analytics_update_interval_minutes);
            config.snow_detection_threshold = parseFloat(config.snow_detection_threshold);
            config.ice_warning_temperature = parseFloat(config.ice_warning_temperature);
            config.hazardous_snow_depth = parseFloat(config.hazardous_snow_depth);
            config.sequence_update_interval_minutes = parseInt(config.sequence_update_interval_minutes);
            config.max_images_per_sequence = parseInt(config.max_images_per_sequence);
            config.gif_frame_duration_seconds = parseFloat(config.gif_frame_duration_seconds);
            
            // Parse ROI points if present
            if (config.road_roi_points) {
                try {
                    config.road_roi_points = JSON.parse(config.road_roi_points);
                } catch (e) {
                    console.error('Failed to parse ROI points:', e);
                    config.road_roi_points = [];
                }
            }
            
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
        
        // Road visualization functions
        function showVizError() {{
            document.getElementById('road-viz-image').style.display = 'none';
            document.getElementById('viz-loading').style.display = 'none';
            document.getElementById('viz-error').style.display = 'block';
        }}
        
        function refreshRoadVisualization() {{
            const img = document.getElementById('road-viz-image');
            const loading = document.getElementById('viz-loading');
            const error = document.getElementById('viz-error');
            const refreshIcon = document.getElementById('refresh-icon');
            
            // Show loading state
            loading.style.display = 'block';
            error.style.display = 'none';
            img.style.display = 'none';
            refreshIcon.style.display = 'inline-block';
            refreshIcon.style.animation = 'spin 1s linear infinite';
            
            // Fetch new image with timestamp to prevent caching
            const timestamp = new Date().getTime();
            const newSrc = `/analytics/road-boundaries?mode=raw&t=${{timestamp}}`;
            
            // Fetch to get headers (metadata)
            fetch(newSrc)
                .then(response => {{
                    if (!response.ok) throw new Error('Failed to load visualization');
                    
                    // Extract metadata from headers
                    const roadPixels = response.headers.get('X-Road-Pixels') || 'N/A';
                    const roadPercentage = response.headers.get('X-Road-Percentage') || 'N/A';
                    const contours = response.headers.get('X-Contours-Detected') || 'N/A';
                    const timestamp = response.headers.get('X-Timestamp') || new Date().toISOString();
                    
                    // Update metadata display
                    document.getElementById('meta-pixels').textContent = roadPixels;
                    document.getElementById('meta-percentage').textContent = roadPercentage + '%';
                    document.getElementById('meta-contours').textContent = contours;
                    document.getElementById('meta-timestamp').textContent = new Date(timestamp).toLocaleString();
                    
                    // Update image
                    img.src = newSrc;
                    img.style.display = 'block';
                    loading.style.display = 'none';
                    
                    // Reinitialize ROI editor when image loads
                    img.onload = function() {{
                        initializeROIEditor();
                    }};
                    
                    // Stop spin animation
                    refreshIcon.style.animation = '';
                }})
                .catch(err => {{
                    console.error('Road visualization error:', err);
                    document.getElementById('viz-error-message').textContent = err.message;
                    showVizError();
                    refreshIcon.style.animation = '';
                }});
        }}
        
        // Load initial metadata on page load
        window.addEventListener('load', function() {{
            setTimeout(refreshRoadVisualization, 1000);
        }});
        
        // Add CSS for spin animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {{
                from {{ transform: rotate(0deg); }}
                to {{ transform: rotate(360deg); }}
            }}
        `;
        document.head.appendChild(style);
        
        // ROI Editor State
        let roiPoints = [];
        let roiOverlayCanvas = null;
        let roiOverlayCtx = null;
        let roadVizImage = null;
        let imageScale = 1.0;
        const MAX_POINTS = 12;
        const MIN_POINTS = 4;
        const POINT_RADIUS = 6;
        const CLOSE_THRESHOLD = 20;

        function initializeROIEditor() {{
            roiOverlayCanvas = document.getElementById('roi-overlay-canvas');
            roiOverlayCtx = roiOverlayCanvas.getContext('2d');
            roadVizImage = document.getElementById('road-viz-image');
            
            // Set canvas size to match image display size
            const imgRect = roadVizImage.getBoundingClientRect();
            roiOverlayCanvas.width = imgRect.width;
            roiOverlayCanvas.height = imgRect.height;
            
            // Calculate scale factor for coordinate conversion
            imageScale = roadVizImage.naturalWidth / imgRect.width;
            
            // Load existing ROI if available
            loadCurrentROI();
            
            // Add click handler to image
            roadVizImage.addEventListener('click', handleROIImageClick);
            
            // Draw initial ROI overlay
            redrawROIOverlay();
        }}

        function handleROIImageClick(event) {{
            const rect = roadVizImage.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            // Check if clicking near first point to close polygon
            if (roiPoints.length >= MIN_POINTS) {{
                const firstPoint = roiPoints[0];
                const dist = Math.sqrt(Math.pow(x - firstPoint.x, 2) + Math.pow(y - firstPoint.y, 2));
                if (dist < CLOSE_THRESHOLD) {{
                    // Close polygon
                    updateROIStatus();
                    redrawROIOverlay();
                    return;
                }}
            }}
            
            // Add new point if under max
            if (roiPoints.length < MAX_POINTS) {{
                roiPoints.push({{x, y}});
                updateROIStatus();
                redrawROIOverlay();
            }}
        }}

        function redrawROIOverlay() {{
            if (!roiOverlayCtx) return;
            
            // Clear canvas
            roiOverlayCtx.clearRect(0, 0, roiOverlayCanvas.width, roiOverlayCanvas.height);
            
            if (roiPoints.length === 0) return;
            
            // Draw polygon lines
            roiOverlayCtx.strokeStyle = '#0066FF';
            roiOverlayCtx.lineWidth = 3;
            roiOverlayCtx.setLineDash([]);
            roiOverlayCtx.beginPath();
            roiOverlayCtx.moveTo(roiPoints[0].x, roiPoints[0].y);
            for (let i = 1; i < roiPoints.length; i++) {{
                roiOverlayCtx.lineTo(roiPoints[i].x, roiPoints[i].y);
            }}
            if (roiPoints.length >= MIN_POINTS) {{
                roiOverlayCtx.closePath();
            }}
            roiOverlayCtx.stroke();
            
            // Draw semi-transparent fill if closed
            if (roiPoints.length >= MIN_POINTS) {{
                roiOverlayCtx.fillStyle = 'rgba(0, 102, 255, 0.15)';
                roiOverlayCtx.fill();
            }}
            
            // Draw points
            roiPoints.forEach((point, index) => {{
                roiOverlayCtx.fillStyle = index === 0 ? '#FF0000' : '#0066FF';
                roiOverlayCtx.beginPath();
                roiOverlayCtx.arc(point.x, point.y, POINT_RADIUS, 0, 2 * Math.PI);
                roiOverlayCtx.fill();
                roiOverlayCtx.strokeStyle = '#FFFFFF';
                roiOverlayCtx.lineWidth = 2;
                roiOverlayCtx.stroke();
            }});
        }}

        function clearROIPoints() {{
            roiPoints = [];
            updateROIStatus();
            redrawROIOverlay();
        }}

        function undoLastPoint() {{
            if (roiPoints.length > 0) {{
                roiPoints.pop();
                updateROIStatus();
                redrawROIOverlay();
            }}
        }}

        function updateROIStatus() {{
            const countEl = document.getElementById('roi-point-count');
            const validEl = document.getElementById('roi-valid');
            
            countEl.textContent = roiPoints.length;
            
            if (roiPoints.length >= MIN_POINTS) {{
                validEl.innerHTML = '<span style="color: green;">✓ Valid polygon</span>';
            }} else if (roiPoints.length > 0) {{
                validEl.innerHTML = '<span style="color: orange;">⚠ Need ' + (MIN_POINTS - roiPoints.length) + ' more points</span>';
            }} else {{
                validEl.innerHTML = '';
            }}
            
            // Update hidden field with normalized coordinates
            if (roiPoints.length >= MIN_POINTS && roadVizImage) {{
                const normalized = roiPoints.map(p => [
                    p.x * imageScale / roadVizImage.naturalWidth,
                    p.y * imageScale / roadVizImage.naturalHeight
                ]);
                document.getElementById('road_roi_points').value = JSON.stringify(normalized);
            }} else {{
                document.getElementById('road_roi_points').value = '';
            }}
        }}

        async function loadCurrentROI() {{
            try {{
                const response = await fetch('/config/analytics');
                const result = await response.json();
                
                if (result.status === 'success' && result.config.road_roi_points) {{
                    const normalized = result.config.road_roi_points;
                    roiPoints = normalized.map(p => ({{
                        x: p[0] * roadVizImage.naturalWidth / imageScale,
                        y: p[1] * roadVizImage.naturalHeight / imageScale
                    }}));
                    
                    document.getElementById('road_roi_enabled').checked = result.config.road_roi_enabled || false;
                    
                    updateROIStatus();
                    redrawROIOverlay();
                    showStatus('Loaded saved ROI', 'success');
                }}
            }} catch (error) {{
                console.error('Failed to load ROI:', error);
            }}
        }}

        async function testROIVisualization() {{
            if (roiPoints.length < MIN_POINTS) {{
                showStatus('Please define at least 4 points', 'error');
                return;
            }}
            
            // Save temporarily to test
            const config = {{
                road_roi_points: roiPoints.map(p => [
                    p.x * imageScale / roadVizImage.naturalWidth,
                    p.y * imageScale / roadVizImage.naturalHeight
                ]),
                road_roi_enabled: true
            }};
            
            try {{
                await fetch('/config/analytics', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(config)
                }});
                
                // Refresh visualization
                setTimeout(() => refreshRoadVisualization(), 500);
                showStatus('Testing ROI - check visualization below', 'success');
            }} catch (error) {{
                showStatus('Test failed: ' + error.message, 'error');
            }}
        }}

        // Update form submission to include ROI data
        document.getElementById('config-form').addEventListener('submit', function(e) {{
            // Ensure ROI points are up to date in hidden field
            updateROIStatus();
        }});
    </script>
</body>
</html>
"""
    
    return html
