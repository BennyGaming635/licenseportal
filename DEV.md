## Develop a change to LicensePortal
So you want to make a change?

Simply follow these steps below to access the actual platform, but to make changes, make sure what you add is defined as a '@app.route' in the python script (app.py) as this is where all the code is stored (unless you want to the code to talk to another Python script/file).

> [WARNING]
> Ensure you create a .env file when making development changes to LicensePortal, to avoid your local database from being pushed to your PR.

1. Pull/download this repository
2. Run the following command:
(Requires Python to be installed)
```
pip install -r requirements.txt
```
3. Simply run the app.py script
4. Visit the IP Address that is prompted in the Python window, the first IP Address is locally (your device only) and the second one is internally (your local network, accessible on local networked devices).