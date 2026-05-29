# Boot Arguments
You can use multiple different boot arguments for running LicensePortal (I'm stealing this format from my other project). These let you change pricing and other things without the need to manually go into the code (not good).

---

## Arguments

### Change Cost per Minute (CPM)

If you want to set the parking cost per minute, use:

```bash
python app.py --cpm <value>
```
The default is 6.50

---

### Change MDR (Max Daily Rate)

To set the maximum charge a ticket can reach in one day, use:

```bash
python app.py --mdr <value>
```
The default is 24.00

---

### Change Unpaid Exit Fee

To set the additional fee charged when not paying beforehand at a terminal, use:

```bash
python app.py --exitfee <value>
```

The default is 6.70 (yes yes 67)

---

### Change Staff Code
>[!WARN]
> It is **heavily recommended** that you change this code, do not leave it as the default '1234'

To change the staff auth code (used for staff login, waiving tickets and exit payments), use:

```bash
python app.py -sc <code>
```

The default is 1234

---

### Change PHM (Peak Hour Multiplier)

In peak hours, you may want to multiply the price due to demand. To do this, use:

```bash
python app.py --peak <multiplier>
```

The default is 1.5 (x0.5 increase)

---

### Disable Peak Hour Pricing (and multiplier)

If you would like to not have peak hour pricing, then use:

```bash
python app.py --dispeak
```

Nothing else is required.

---

### Disable First 15 Minutes free

Some car parks may want to offer a free 15 minutes of parking, mainly for change of mind or for other reasons. If you don't want the grace period, use:

```bash
python app.py --disfree
```

If this is enabled, all time is billed instantly from the minute the ticket is issued.
