# Installation Guide

## Requirements

- Home Assistant 2025.1.0 or later
- Python 3.13.1 or later
- Access to your local Enphase Envoy device
- Valid Enphase account credentials

## Installation Methods

### Method 1: Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/enphase_production_toggle` directory to your Home Assistant `custom_components` folder:
   ```
   /config/custom_components/enphase_production_toggle/
   ```
3. Restart Home Assistant
4. Add the integration through the UI (Settings > Devices & Services > Add Integration)
5. Search for "Enphase Production Toggle"

### Method 2: HACS Installation (Future)

This integration could be added to HACS in the future for easier installation.

## Configuration

### Required Information

You'll need to gather the following information before setup:

1. **Envoy IP Address**: Find your Enphase Envoy's local IP address
   - Check your router's admin panel for connected devices
   - Look for a device named "Envoy" or similar
   - Usually starts with `192.168.` or `10.0.`

2. **Enphase Account Credentials**:
   - Username (email address used for Enphase account)
   - Password for your Enphase account

### Setup Steps

1. In Home Assistant, go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "Enphase Production Toggle"
4. Enter the required information:
   - **Envoy IP Address**: Your Envoy's local IP
   - **Username**: Your Enphase account email
   - **Password**: Your Enphase account password
5. Click **Submit**

## Usage

Once configured, you'll have a switch entity called "Enphase Production" that allows you to:

- **Turn On**: Enable solar production
- **Turn Off**: Disable solar production
- **Monitor**: View current production power and status

### Entity Information

- **Entity ID**: `switch.enphase_production`
- **Attributes**:
  - `current_power`: Current production in watts
  - `is_producing`: Whether the system is actively producing power

### Automation Example

```yaml
automation:
  - alias: "Disable solar during peak hours"
    trigger:
      - platform: time
        at: "14:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.enphase_production
  
  - alias: "Enable solar after peak hours"
    trigger:
      - platform: time
        at: "18:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.enphase_production
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify your Enphase account credentials
   - Ensure you're using the correct email and password
   - Try logging into the Enphase website to verify credentials

2. **Cannot Connect to Envoy**
   - Check the IP address is correct
   - Ensure Home Assistant and Envoy are on the same network
   - Try pinging the Envoy IP from Home Assistant host

3. **Production Control Not Working**
   - Some older Envoy models may not support production control
   - Ensure your Envoy firmware is up to date
   - Check Enphase account has proper permissions

### Debug Logging

The integration includes comprehensive logging to help with troubleshooting. To enable debug logging, add this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.enphase_production_toggle: debug
```

#### Logging Levels

- **INFO**: Key operations (setup, authentication success, production changes)
- **DEBUG**: Detailed flow (API calls, data parsing, state updates)  
- **ERROR**: Failures (authentication errors, API failures, connection issues)

Then restart Home Assistant and check the logs for detailed error information. The logs will show exactly where in the process any issues occur, making troubleshooting much easier.

### Getting Help

1. Check the [README](README.md) for additional information
2. Review the debug logs for specific error messages
3. Create an issue on the GitHub repository with:
   - Home Assistant version
   - Envoy model and firmware version
   - Error logs (with sensitive information removed)

## Security Notes

- Your Enphase credentials are stored securely in Home Assistant
- Communication with the Envoy uses local network connections
- No data is sent to external services beyond Enphase authentication

## Limitations

- Requires internet connection for initial authentication
- Some Envoy models may not support production control
- Production changes may take a few seconds to take effect
- System monitors production status every 30 seconds by default