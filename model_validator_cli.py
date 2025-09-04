#!/usr/bin/env python3
"""
Command-line tool to validate and get information about Eufy RoboVac models.
This tool helps users identify if their vacuum model is supported and provides
troubleshooting information.

Usage:
    python3 model_validator_cli.py T2277
    python3 model_validator_cli.py --list-all
    python3 model_validator_cli.py --series L
"""

import sys
import argparse
from pathlib import Path

# Add the project directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Simplified standalone implementation
ROBOVAC_MODELS = {
    "T2103", "T2117", "T2118", "T2119", "T2120", "T2123", "T2128", "T2130", "T2132",
    "T1250", "T2150", "T2181", "T2182", "T2190", "T2192", "T2193", "T2194", 
    "T2250", "T2251", "T2252", "T2253", "T2254", "T2255", "T2256", "T2257", "T2258", "T2259",
    "T2261", "T2262", "T2266", "T2267", "T2268", "T2270", "T2272", "T2273", "T2275", "T2276", "T2277", "T2278",
    "T2320", "T2351"
}

MODEL_SERIES = {
    "C": {
        "name": "C Series",
        "description": "Entry-level models with basic cleaning features",
        "examples": ["T2103", "T2117", "T2118", "T2119", "T2120", "T2123"],
        "features": ["Basic cleaning", "Remote control", "Auto-return"],
    },
    "G": {
        "name": "G Series", 
        "description": "Mid-range models with enhanced navigation",
        "examples": ["T2250", "T2251", "T2252", "T2253", "T2254", "T2255"],
        "features": ["BoostIQ", "Drop-sensing", "Boundary strips"],
    },
    "L": {
        "name": "L Series",
        "description": "Advanced models with laser navigation and mapping",
        "examples": ["T2267", "T2268", "T2275", "T2276", "T2277"],
        "features": ["Laser navigation", "App mapping", "Room cleaning", "No-go zones"],
    },
    "X": {
        "name": "X Series",
        "description": "Premium models with advanced features and self-emptying",
        "examples": ["T2276", "T2278", "T2320"],
        "features": ["Self-emptying", "Advanced mapping", "Multi-floor maps", "Voice control"],
    },
}

MODEL_NAME_MAPPINGS = {
    "T2103": "RoboVac 11S",
    "T2117": "RoboVac 15C", 
    "T2118": "RoboVac 15C Max",
    "T2119": "RoboVac 12",
    "T2120": "RoboVac 25C",
    "T2123": "RoboVac 30C",
    "T2250": "RoboVac G10 Hybrid",
    "T2251": "RoboVac G15",
    "T2252": "RoboVac G20",
    "T2253": "RoboVac G20 Hybrid",
    "T2254": "RoboVac G30",
    "T2255": "RoboVac G30 Edge",
    "T2267": "RoboVac L60",
    "T2268": "RoboVac L60 Hybrid", 
    "T2275": "RoboVac L50 SES",
    "T2276": "RoboVac X8 Pro SES",
    "T2277": "RoboVac L60 SES",
    "T2278": "RoboVac X9 Pro",
    "T2320": "RoboVac X10 Pro Omni",
}

def get_supported_models():
    return sorted(ROBOVAC_MODELS)

def is_model_supported(model_code):
    return model_code in ROBOVAC_MODELS

def get_model_series(model_code):
    if len(model_code) >= 5 and model_code.startswith('T'):
        numeric_part = model_code[1:]
        if numeric_part.startswith('21'):
            return "C"
        elif numeric_part.startswith('225'):
            return "G"
        elif numeric_part.startswith('226') or numeric_part.startswith('227'):
            return "L"
        elif (numeric_part.startswith('228') or numeric_part.startswith('229') or 
              numeric_part.startswith('23') or model_code in ['T2276', 'T2278']):
            return "X"
    return "Unknown"

def validate_and_suggest(model_code):
    result = {
        "model_code": model_code,
        "is_supported": False,
        "suggestions": [],
        "message": "",
    }
    
    if not model_code:
        result["message"] = "Please provide a model code (e.g., T2277)"
        return result
    
    model_code = model_code.strip().upper()
    
    if is_model_supported(model_code):
        result["is_supported"] = True
        result["message"] = f"✅ Model {model_code} is fully supported!"
    else:
        target_series = get_model_series(model_code)
        similar_models = []
        
        if target_series != "Unknown":
            series_models = [m for m in get_supported_models() 
                           if get_model_series(m) == target_series]
            for model in series_models[:3]:
                similar_models.append((model, f"Same {target_series} series"))
        
        result["suggestions"] = similar_models
        
        if similar_models:
            result["message"] = (
                f"❌ Model {model_code} is not supported yet. "
                f"However, these similar models are supported and might work:"
            )
        else:
            result["message"] = (
                f"❌ Model {model_code} is not supported yet. "
                f"Please create an issue on GitHub to request support."
            )
    
    return result

def get_troubleshooting_info(model_code):
    series = get_model_series(model_code)
    
    common_steps = [
        "1. Ensure your vacuum is connected to the same network as Home Assistant",
        "2. Check that the vacuum's IP address is correctly configured",
        "3. Verify the vacuum is powered on and not in sleep mode",
        "4. Try restarting both the vacuum and Home Assistant",
    ]
    
    series_specific = {
        "C": [
            "5. C Series models may need manual IP configuration",
            "6. Check if your router supports 2.4GHz WiFi (required for C Series)",
        ],
        "G": [
            "5. G Series models support both 2.4GHz and 5GHz WiFi",
            "6. Try using the Eufy app to verify connectivity first",
        ],
        "L": [
            "5. L Series models require strong WiFi signal for mapping features",
            "6. Ensure the vacuum has completed initial mapping if using room cleaning",
        ],
        "X": [
            "5. X Series models may need firmware updates for full compatibility",
            "6. Check if self-emptying station is properly connected (if applicable)",
        ],
    }
    
    all_steps = common_steps + series_specific.get(series, [])
    
    return {
        "model_code": model_code,
        "series": series,
        "troubleshooting_steps": all_steps,
        "documentation_url": "https://github.com/damacus/robovac#debugging",
    }


def print_model_info(model_code: str) -> None:
    """Print detailed information about a specific model."""
    series = get_model_series(model_code)
    series_info = MODEL_SERIES.get(series, {})
    friendly_name = MODEL_NAME_MAPPINGS.get(model_code, f"RoboVac {model_code}")
    
    print(f"\n📱 Model Information:")
    print(f"   Code: {model_code}")
    print(f"   Name: {friendly_name}")
    print(f"   Series: {series_info.get('name', 'Unknown Series')}")
    print(f"   Description: {series_info.get('description', '')}")
    print(f"   Features: {', '.join(series_info.get('features', []))}")
    
    # Add troubleshooting info
    troubleshooting = get_troubleshooting_info(model_code)
    print(f"\n🔧 Troubleshooting Steps:")
    for step in troubleshooting['troubleshooting_steps']:
        print(f"   {step}")
    print(f"\n📚 Documentation: {troubleshooting['documentation_url']}")


def list_all_models() -> None:
    """List all supported models organized by series."""
    print("🤖 All Supported Eufy RoboVac Models:")
    print("=" * 50)
    
    for series_code, series_info in MODEL_SERIES.items():
        print(f"\n📂 {series_info['name']} ({series_code} Series)")
        print(f"   {series_info['description']}")
        print(f"   Features: {', '.join(series_info['features'])}")
        print("   Models:")
        
        series_models = [model for model in get_supported_models() 
                        if model in series_info['examples']]
        
        for model in series_models:
            friendly_name = MODEL_NAME_MAPPINGS.get(model, f"RoboVac {model}")
            print(f"     • {model} - {friendly_name}")


def list_series_models(series: str) -> None:
    """List models for a specific series."""
    series = series.upper()
    if series not in MODEL_SERIES:
        print(f"❌ Unknown series '{series}'. Available series: {', '.join(MODEL_SERIES.keys())}")
        return
    
    series_info = MODEL_SERIES[series]
    print(f"\n📂 {series_info['name']} Models:")
    print(f"   {series_info['description']}")
    print(f"   Features: {', '.join(series_info['features'])}")
    print("\n   Supported Models:")
    
    series_models = [model for model in get_supported_models() 
                    if model in series_info['examples']]
    
    for model in series_models:
        friendly_name = MODEL_NAME_MAPPINGS.get(model, f"RoboVac {model}")
        print(f"     • {model} - {friendly_name}")


def main():
    """Main function for the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Validate Eufy RoboVac model compatibility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 model_validator_cli.py T2277              # Check if T2277 is supported
  python3 model_validator_cli.py T9999              # Check unsupported model (get suggestions)
  python3 model_validator_cli.py --list-all         # List all supported models
  python3 model_validator_cli.py --series L         # List L series models only
  python3 model_validator_cli.py --help             # Show this help message
        """
    )
    
    parser.add_argument(
        "model_code", 
        nargs="?", 
        help="Model code to validate (e.g., T2277)"
    )
    parser.add_argument(
        "--list-all", 
        action="store_true", 
        help="List all supported models"
    )
    parser.add_argument(
        "--series", 
        help="List models for a specific series (C, G, L, X)"
    )
    
    args = parser.parse_args()
    
    print("🔍 Eufy RoboVac Model Validator")
    print("=" * 40)
    
    if args.list_all:
        list_all_models()
    elif args.series:
        list_series_models(args.series)
    elif args.model_code:
        result = validate_and_suggest(args.model_code)
        print(f"\n{result['message']}")
        
        if result['is_supported']:
            print_model_info(result['model_code'])
        elif result['suggestions']:
            print(f"\n💡 Suggested alternatives:")
            for model, reason in result['suggestions']:
                friendly_name = MODEL_NAME_MAPPINGS.get(model, f"RoboVac {model}")
                print(f"   • {model} ({friendly_name}) - {reason}")
            
            print(f"\n🔧 You can try using one of these models' configurations.")
            print(f"📝 Or create an issue: https://github.com/damacus/robovac/issues/new")
    else:
        parser.print_help()
        print(f"\n💡 Quick start: python3 {sys.argv[0]} T2277")


if __name__ == "__main__":
    main()
