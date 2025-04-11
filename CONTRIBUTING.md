# Contributing

## Adding Support for New RoboVac Models

If you have a RoboVac model that's not currently supported by this integration, you can add support for it by following these steps:

1. **Identify Your Model Code**:
   - The model code is typically a "T" followed by 4 digits (e.g., T2103, T2250)
   - You can find this in your Eufy app or on the device itself

2. **Determine the Series**:
   - RoboVac models are organized into series (C, G, L, X) with different feature sets
   - Each series supports different cleaning modes and capabilities

3. **Add Your Model to the Codebase**:
   - Open `custom_components/robovac/robovac.py`
   - Add your model code to the appropriate series in the `ROBOVAC_SERIES` dictionary
   - Example: `"C": ["T2103", "T2117", ..., "YOUR_MODEL_CODE"],`
