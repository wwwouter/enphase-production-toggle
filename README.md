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

- **Envoy IP Address**: The local IP address of your Enphase Envoy
- **Enphase Account Username**: Your Enphase account email
- **Enphase Account Password**: Your Enphase account password

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

### Code Quality

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type checking
uv run mypy custom_components/
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

Enable debug logging by adding this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.enphase_production_toggle: debug
```

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