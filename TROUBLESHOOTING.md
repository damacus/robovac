# RoboVac Troubleshooting Guide

This document provides solutions to common issues with the RoboVac integration.

## Table of Contents

- [Understanding and Working with DPS Codes](#understanding-and-working-with-dps-codes)
- [Common Connection Issues](#common-connection-issues)
- [Feature Support Issues](#feature-support-issues)

## Understanding and Working with DPS Codes

### What is a DPS Code?

DPS (Data Point Specification) codes are numeric identifiers used in Tuya-based devices like Eufy RoboVacs to control various functions and retrieve device states. Each DPS code maps to a specific function or feature of your vacuum, such as:

- Battery level
- Cleaning mode
- Fan speed
- Error status
- Cleaning area
- Cleaning time

In the RoboVac integration, these codes are used to communicate with your vacuum via the Tuya local API. Think of them as the language that allows Home Assistant to talk to your vacuum.

### How to Find DPS Codes for Your Device

Finding the correct DPS codes for your vacuum model is essential for adding support for new devices. Here are methods to discover these codes:

#### Method 1: Use the Model DPS Analysis Tool

The repository includes a test that analyzes DPS codes for all supported models:

1. Navigate to the `tests/test_vacuum/test_model_dps_analysis.py` file
2. Run this test to generate a report showing:
   - Which models use default codes
   - Which models use custom codes
   - What specific custom codes are used by each model

This can help you understand patterns in how different models use DPS codes.

#### Method 2: Enable Debug Logging

1. Enable debug logging for the RoboVac component in your Home Assistant configuration:

   ```yaml
   logger:
     default: info
     logs:
       custom_components.robovac: debug
   ```

2. Restart Home Assistant and monitor the logs while operating your vacuum
3. Look for log entries showing `"Updating entity values from data points: ..."` which will display all the DPS codes and values being reported by your device

#### Method 3: Analyze Network Traffic (Advanced)

For more advanced users:

1. Use a tool like Wireshark to capture traffic between your Home Assistant instance and your vacuum
2. Filter for traffic to/from your vacuum's IP address
3. Look for Tuya protocol messages, which contain DPS code information in their payload
4. Decode these messages to identify which DPS codes your vacuum is using and their functions

### Adding Support for a New Device

To add support for a new device, you'll need to:

1. **Determine your model code**: This is typically the first 5 characters of the full model number
2. **Identify required DPS codes**: Using the methods above, determine which DPS codes your vacuum uses
3. **Create a model-specific class**: If your vacuum uses non-default DPS codes, you'll need to create a model-specific class in the `custom_components/robovac/vacuums/` directory
4. **Map commands to DPS codes**: In your model class, create mappings between RoboVac commands and the DPS codes your vacuum uses

#### Example Implementation

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

### Tips for Successful Implementation

1. **Test incrementally**: Add support for basic functions first (start/stop, battery), then add more complex features
2. **Compare with similar models**: Look at implementations for similar vacuum models for guidance
3. **Use debug logging**: Keep debug logging enabled during development to monitor communication with the device
4. **Test systematically**: Create tests for your implementation similar to those for existing models
5. **Document your findings**: Once you've successfully added support, document any unique aspects of your model to help others

### Common Troubleshooting

- **Device not responding**: Verify your IP address and access token are correct
- **Command not working**: Check if the DPS code mapping is correct for that specific command
- **Values not updating**: Ensure the DPS code for status information is correctly mapped

## Common Connection Issues

### Coming Soon

This section will be expanded in the future.

## Feature Support Issues

### Coming Soon

This section will be expanded in the future.
