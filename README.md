# Enphase Production Toggle

A minimal Home Assistant custom integration for toggling Enphase solar production on/off.

## Features

- Simple production on/off switch
- Automatic authentication with Enphase Envoy
- Real-time production status monitoring
- Minimal resource usage

## Installation

1. Copy the `custom_components/enphase_production_toggle` directory to your Home Assistant `custom_components` folder
2. Restart Home Assistant
3. Add the integration through the UI (Settings > Devices & Services > Add Integration)

## Configuration

During setup, you'll need to provide:

- **Envoy IP Address**: The local IP address of your Enphase Envoy (e.g., `192.168.1.100`)
- **Enphase Account Username**: Your Enphase installer account email (e.g., `installer@example.com`)
- **Enphase Account Password**: Your Enphase account password

**Important**: You need an Enphase installer account to control production. Regular homeowner accounts may only have read access to production data.

## Usage

Once configured, you'll have a switch entity named "Enphase Production" that you can use to:

- Turn solar production on/off
- View current production power
- Check if the system is actively producing

## Development

This project uses `uv` for dependency management and `pytest` for testing. Requires Python 3.13.1 or later.

### Setup Development Environment

```bash
# Install uv if not already installed
pip install uv

# Install dependencies
uv sync

# Install development dependencies
uv sync --group test
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=custom_components.enphase_production_toggle

# Run specific test file
uv run pytest tests/test_switch.py
```

### Testing with Debug Scripts

The repository includes several debug scripts for testing the integration outside of Home Assistant. Before using them:

1. Update the credentials in each script:
   - Replace `192.168.1.xxx` with your Envoy IP address
   - Replace `your-email@example.com` with your Enphase installer account email
   - Set your password via environment variable: `export ENPHASE_PASSWORD="your_password"`

2. Run debug scripts:
```bash
# Test authentication only
uv run debug_connection.py

# Test production control endpoints
uv run test_production_control.py
```

### Code Quality

#### Pre-commit Hooks (Recommended)

Set up pre-commit hooks to automatically format and lint code before commits:

```bash
# Install pre-commit hooks (one-time setup)
uv run pre-commit install

# Run hooks on all files (optional)
uv run pre-commit run --all-files
```

After setup, ruff and black will automatically run on staged files before each commit.

#### Manual Code Quality Commands

```bash
# Format code with black
uv run black custom_components/ tests/

# Format code with ruff
uv run ruff format custom_components/

# Lint and fix code with ruff
uv run ruff check custom_components/ --fix

# Type checking
uv run basedpyright
```

## API Reference

The integration communicates with the Enphase Envoy using local API endpoints:

- Authentication via Enphase cloud service
- Production status via `/production.json`
- Production control via `/ivp/mod/603980032/mode/power`

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Verify your Enphase account credentials
2. **Cannot Connect**: Ensure the Envoy IP address is correct and reachable
3. **Production Control Not Working**: Some Envoy models may use different endpoints

### Debugging

The integration includes comprehensive logging at debug and info levels to help troubleshoot issues. Enable debug logging by adding this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.enphase_production_toggle: debug
```

#### What Gets Logged

- **INFO level**: Important operations (authentication success, production changes, setup/teardown)
- **DEBUG level**: Detailed flow information (API requests/responses, data parsing, state changes)
- **ERROR level**: Authentication failures, API errors, connection issues

#### Example Log Output

```
INFO: Setting up Enphase Production Toggle integration for Enphase Envoy (192.168.1.100)
DEBUG: Entry data: host=192.168.1.100, username=user@example.com
DEBUG: Initializing coordinator for host: 192.168.1.100
INFO: Coordinator initialized with 30 second update interval
DEBUG: Starting authentication process
INFO: Successfully authenticated with Enphase Envoy at 192.168.1.100
INFO: Data update successful - Production: 4500 W, Enabled: True
INFO: User requested to turn OFF production
INFO: Setting production power to: disabled
INFO: Successfully set production power to disabled
```

This detailed logging helps identify exactly where issues occur in the authentication or control process.

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Disclaimer

This integration is not affiliated with Enphase Energy. Use at your own risk.
