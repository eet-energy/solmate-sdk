# EET SolMate SDK

All you need to integrate your [EET SolMate](https://www.eet.energy) into your home automation system - or really any Python-based system!
Keep in mind that this is **work in progress**.

This Python SDK provides a class-based API Client which lets you:

1. Login to your SolMate with serial number and password which returns an authentication token.
2. Connect to your SolMate with the authentication token.
3. Get live values of your SolMate.
4. Check if your SolMate is online.

For any inquiries about, or problems with, the usage of this API endpoint, please create an issue in this repository.

## How to use

Install the package via:

`pip install solmate-sdk`

Import the `SolMateAPIClient` class and connect to your SolMate:

```python
from solmate_sdk import SolMateAPIClient

client = SolMateAPIClient("serial_num")
client.connect()
print(f"Your SolMate online status is: {client.check_online()}")

# or for the protected API:
client.quickstart()
print(client.get_live_values())
```

The SolMate SDK communicates via a Websocket API with your SolMate.

## Roadmap

- Quickstart supports multiple serial numbers (and multiple device ids?)
- Publish docs on Read The Docs
- More Examples
- Full Unit Testing
- Car Charger Example

## Links

- Our Homepage: [www.eet.energy](https://www.eet.energy)
- The project on PyPi: [pypi.org/project/solmate-sdk](https://pypi.org/project/solmate-sdk/)
- Read the docs page: https://solmate-sdk.readthedocs.io/en/latest/
