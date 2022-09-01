# EET SolMate SDK

All you need to integrate your [EET](https://www.eet.energy) SolMate into your home automation system and any python based system. 
Keep in mind that this is **work in progress**.

This python based SDK provides a class based API Client which let you:

1. Login to your SolMate with serial number and password which returns an authentification token.
2. Connect to your SolMate with the authentification token.
3. Get live values of your SolMate.
4. Check if your SolMate is online.

## How to use

Install the package via:

`pip install solmate-sdk`

Import the `SolMateAPIClient` class and connect to your SolMate:

```python
from solmate_sdk.apiclient import SolMateAPIClient

client = SolMateAPIClient("serial_num")
client.connect()
print(f"Your SolMate online status is: {client.check_online()}")
```

## Implementation Details

The SolMate SDK communicate over the SolMate Websocket API with your SolMate.

## Links

- [www.eet.energy](https://www.eet.energy)
- [pypi.org/project/solmate-sdk](https://pypi.org/project/solmate-sdk/)