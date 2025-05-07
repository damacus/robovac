# Contributing

## Adding Support for New RoboVac Models

If you have a RoboVac model that's not currently supported by this integration, you can add support for it by following these steps:

1. **Identify Your Model Code**:
   - The model code is typically a "T" followed by 4 digits (e.g., T2103, T2250)
   - You can find this in your Eufy app or on the device itself

2. **Add Your Model to the Codebase**:
   - Add your model to :
     - `custom_components/robovac/vacuums/__init__.py`
     - `custom_components/robovac/vacuums/<MODEL_CODE>.py`
        Adding all supported features for the model
