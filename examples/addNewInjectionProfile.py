from solmate_sdk import SolMateAPIClient
from solmate_sdk.utils import DATETIME_FORMAT_INJECTION_PROFILES

import datetime

client = SolMateAPIClient("")
client.quickstart()

# get saved injection profile settings on solmate
injection_profiles_settings_from_solmate = client.get_injection_profiles()
injection_profiles_from_solmate = injection_profiles_settings_from_solmate["injection_profiles"]
# define new injection profile where key is the name displayed in the App
new_injection_profile = {
    "my awesome test profile": {
        "min": [0.2 for _ in range(24)],
        "max": [0.8 for _ in range(24)],
    }
}
# extend injection profiles with new injection profile
injection_profiles_from_solmate.update(new_injection_profile)
# get new timestamp
new_timestamp = datetime.datetime.now().strftime(DATETIME_FORMAT_INJECTION_PROFILES)
# send old + new injection profile to solmate
client.set_injection_profiles(injection_profiles_from_solmate, new_timestamp)
# apply the newly created injection profile
client.apply_injection_profile("my awesome test profile")
