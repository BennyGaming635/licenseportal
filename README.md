# Welcome to LicensePortal!
LicensePortal was originally an idea in my mind to have a sort of license-plate scanning system for commerical usage, but I personally tried to make something like that and it proved too difficult to try and do, so I instead came up with another idea to make something that could be used in a car park since I was really bored and uhh yeah it became this.

## How can I run it?
Since it's just Flask and Python, it's pretty easy to set up. In fact, you can run this in *4* easy steps!
> [!NOTE]
> If you're interested in editing or making changes to this project, visit [DEV.md](/DEV.md).

1. Pull/download this repository
2. Run the following command:
(Requires Python to be installed)
```bash
pip install -r requirements.txt
```
3. Simply run the app.py script
4. Visit the IP Address that is prompted in the Python window, the first IP Address is locally (your device only) and the second one is internally (your local network, accessible on local networked devices).

## Can I change any variables?
Yes, and in fact you very much should change some variables. I recommend you change the following variables which are listed below.
```
COST_PER_MINUTE = 0.00
STAFF_CODE = "NUMERICAL CODE"
UNPAID_EXIT_FEE = 0.00

app = Flask(__name__)
app.secret_key = "Use a SHA256 key here or something in production"

## So how does it work?
Glad you asked, this works by using Flask which hosts the local html files over the network, while SQLITE powers the database and Javascript in the .html files interact with Flask, which in turn talks to the SQLITE databases. (It looks confusing but on paper it gets simpler).

## Can I contribute?
Wow, if you're really interested I mean you can submit changes and such in the form of a PR, learn more [here](/DEV.md).