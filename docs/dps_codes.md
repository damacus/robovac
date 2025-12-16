# Understanding and Working with DPS Codes

## What is a DPS Code?

DPS (Data Point Specification) codes are numeric identifiers used in Tuya-based devices like Eufy RoboVacs to control various functions and retrieve device states. Each DPS code maps to a specific function or feature of your vacuum, such as:

- Battery level
- Cleaning mode
- Fan speed
- Error status
- Cleaning area
- Cleaning time

In the RoboVac integration, these codes are used to communicate with your vacuum via the Tuya local API. Think of them as the language that allows Home Assistant to talk to your vacuum.

## How to Find DPS Codes for Your Device

Finding the correct DPS codes for your vacuum model is essential for adding support for new devices. Here are methods to discover these codes:

### Method 1: Use the Model DPS Analysis Tool

The repository includes a test that analyzes DPS codes for all supported models:

1. Navigate to the `tests/test_vacuum/test_model_dps_analysis.py` file (or run `analyze_model_dps.py` in the root directory).
2. Run this script to generate a report showing:
   - Which models use default codes
   - Which models use custom codes
   - What specific custom codes are used by each model

This can help you understand patterns in how different models use DPS codes.

### Method 2: Enable Debug Logging

1. Enable debug logging for the RoboVac component in your Home Assistant configuration:

   ```yaml
   logger:
     default: info
     logs:
       custom_components.robovac: debug
   ```

2. Restart Home Assistant and monitor the logs while operating your vacuum.
3. Look for log entries showing `"Updating entity values from data points: ..."` which will display all the DPS codes and values being reported by your device.

### Method 3: Analyze Network Traffic (Advanced)

For more advanced users:

1. Use a tool like Wireshark to capture traffic between your Home Assistant instance and your vacuum.
2. Filter for traffic to/from your vacuum's IP address.
3. Look for Tuya protocol messages, which contain DPS code information in their payload.
4. Decode these messages to identify which DPS codes your vacuum is using and their functions.

### Method 4: External Tools

If you're comfortable with Python, you can try these tools to capture raw device data:

- [eufy-device-id-python](https://github.com/markbajaj/eufy-device-id-python) - Gets device info from Eufy servers
- `tinytuya scan` - Scans local network for Tuya devices (after you have credentials)

## Adding Support for a New Device

To add support for a new device, you'll need to:

1. **Determine your model code**: This is typically the first 5 characters of the full model number.
2. **Identify required DPS codes**: Using the methods above, determine which DPS codes your vacuum uses.
3. **Create a model-specific class**: If your vacuum uses non-default DPS codes, you'll need to create a model-specific class in the `custom_components/robovac/vacuums/` directory.
4. **Map commands to DPS codes**: In your model class, create mappings between RoboVac commands and the DPS codes your vacuum uses.

### Example Implementation

Here's a simplified example of how a model-specific class looks:

```python
from custom_components.robovac.vacuums.base import RobovacModelDetails, RoboVacEntityFeature, RobovacCommand

class YourModel(RobovacModelDetails):
    """Implementation for Your Specific Model."""
    
    # Define which Home Assistant features this vacuum supports
    homeassistant_features = (
        # Add relevant features here
    )
    
    # Define which RoboVac features this vacuum supports
    robovac_features = (
        # Add relevant features here
    )
    
    # Map commands to DPS codes - override any that differ from defaults
    dps_codes = {
        "BATTERY_LEVEL": "104",  # Example - use actual codes from your device
        "STATUS": "15",
        # Add other codes as needed
    }
    
    # Define available commands
    commands = {
        RobovacCommand.START_PAUSE: True,
        RobovacCommand.BATTERY: True,
        # Add other commands as appropriate
    }
```
