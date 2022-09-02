from solmate_sdk import SolMateAPIClient

client = SolMateAPIClient("test1")
client.connect()
print(f"Your SolMate online status is: {client.check_online()}")
