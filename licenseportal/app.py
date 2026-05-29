import code

from flask import Flask, render_template, jsonify, request, redirect, session
import sqlite3
import time
from datetime import datetime
import argparse

LICENSE_NAME = "CHANGEME" ## Change this to your orgs name for licensing reasons.

parser = argparse.ArgumentParser(description="LicensePortal Parking Management System")

parser.add_argument(
    "--cpm",
    type=float,
    default=6.50,
    help="Parking cost per minute"
)

parser.add_argument(
    "--mdr",
    type=float,
    default=24.00,
    help="Maximum daily rate"
)

parser.add_argument(
    "--exitfee",
    type=float,
    default=6.70,
    help="Unpaid exit fee"
)

parser.add_argument(
    "--sc",
    type=str,
    default="1234",
    help="Staff code for waiving tickets and exit payments"
)

parser.add_argument(
    "--peak",
    type=float,
    default=1.5,
    help="Peak hour multiplier"
)

parser.add_argument(
    "--dispeak",
    action="store_true",
    help="Disable peak hours"
)

parser.add_argument(
    "--disfree",
    action="store_true",
    help="Disable first 15 minutes free"
)

args = parser.parse_args()

COST_PER_MINUTE = args.cpm
FIRST_15_MINUTES_FREE = not args.disfree
MAX_DAILY_RATE = args.mdr
EXIT_GRACE_MINUTES = 10
PEAK_HOUR_ENABLED = not args.dispeak
PEAK_HOUR_MULTIPLIER = args.peak
STAFF_CODE = args.sc
UNPAID_EXIT_FEE = args.exitfee ## Yes I really just did 67, for the memes but whatever.
PEAK_HOURS = {
    (7, 9), ## this is just 7am to 9am
    (16, 18) ## this one is just 4pm to 6pm tho
}
ticket_number = 0

app = Flask(__name__)
app.secret_key = "supersecretkey"

def create_app():
    return app

def calculate_price(entry_time):
    now = int(time.time())
    minutes = max(1, int((now - entry_time) // 60))

    if FIRST_15_MINUTES_FREE and minutes <= 15:
        return 0.0, minutes
    price = minutes * COST_PER_MINUTE

    if PEAK_HOUR_ENABLED:
        current_hour = datetime.now().hour
        for start, end in PEAK_HOURS:
            if start <= current_hour < end:
                price*= PEAK_HOUR_MULTIPLIER
                break

    if price > MAX_DAILY_RATE:
        price = MAX_DAILY_RATE
    return round(price, 2), minutes

def init_db():

    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            message TEXT
            )
        """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            code TEXT PRIMARY KEY,
            paid INTEGER DEFAULT 0,
            exited INTEGER DEFAULT 0,
            entry_time INTEGER,
            price REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
    """)

    c.execute("""
        INSERT OR IGNORE INTO meta (key, value)
        VALUES ('ticket', 40)
    """)

    conn.commit()
    conn.close()

init_db()

def add_log(message):
    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO logs (timestamp, message)
        VALUES (?, ?)
    """, (int(time.time()), message))
    conn.commit()
    conn.close()

@app.route("/")

def kiosk():
    return render_template("kiosk.html")
add_log(f"Accessed kiosk page")

@app.route("/waive_ticket", methods=["POST"])
def waive_ticket():
    if not session.get("staff_logged_in"):
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 403
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    if not code:
        return jsonify({
            "success": False,
            "error": "No ticket code provided"
        }), 400
    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()
    c.execute("""
        SELECT code
        FROM tickets
        WHERE code = ?
    """, (code,))

    ticket = c.fetchone()
    if not ticket:
        conn.close()
        return jsonify({
            "success": False,
            "error": "Ticket not found"
        }), 404
    
    c.execute("""
        UPDATE tickets
        SET price = 0,
            paid = 1
        WHERE code = ?
    """, (code,))

    conn.commit()
    conn.close()
    add_log(f"Waived parking fee for ticket {code}")
    return jsonify({
        "success": True
    })

@app.route("/staff/log")
def staff_logs():
    if not session.get("staff_logged_in"):
        return redirect("/staff-login")
    
    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute("""
        SELECT timestamp, message
        FROM logs
        ORDER BY id DESC
        LIMIT 200
    """)

    rows = c.fetchall()
    conn.close()
    formatted_logs = []
    for row in rows:
        ts, msg = row
        formatted_logs.append({
            "time": time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(ts)),
            "message": msg
        })

        return render_template("logs.html", logs=formatted_logs)

@app.route("/exit")
def exit_terminal():
    return render_template("exit.html")
add_log(f"Accessed exit page")

@app.route("/exit_check", methods=["POST"])
def exit_check():
    data = request.get_json(silent=True) or {}
    code = data.get("code")

    if not code:
        return jsonify({
            "success": False,
            "error": "No ticket code"
        }), 400
    
    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute("""
        SELECT paid, exited, entry_time, price
        FROM tickets
        WHERE code = ?
    """, (code,))

    ticket = c.fetchone()
    conn.close()

    if not ticket:
        add_log(f"Failed exit check. Error: Ticket {code} not found")
        return jsonify({
            "success": False,
            "error": "Ticket not found"
        }), 404
    
    paid, exited, entry_time, stored_price = ticket
    if exited:
        add_log(f"Automatically rejected ticket due to a reused code. The code was {code}.")
        return jsonify({
            "success": False,
            "error": "This ticket has been used"
        }), 403
    
    if paid:
        add_log(f"Exit check successful for ticket {code}. Ticket already paid, gate opening.")
        conn = sqlite3.connect("tickets.db")
        c = conn.cursor()

        c.execute("""
            UPDATE tickets
            SET exited = 1
            WHERE code = ?
        """, (code,))

        conn.commit()
        conn.close()

        add_log(f"Gate opened for ticket {code}")

        return jsonify({
            "success": True,
            "paid": True,
            "message": "Gate Open"
        })
    
    total_due = round(
        stored_price + UNPAID_EXIT_FEE,
        2
    )

    add_log(f"Exit check for ticket {code}. Ticket unpaid, total due: ${total_due}")
    return jsonify({
        "success": True,
        "paid": False,
        "parking": stored_price,
        "exit_fee": UNPAID_EXIT_FEE,
        "total": total_due
    })

@app.route("/exit_pay", methods=["POST"])
def exit_pay():
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    auth = data.get("auth")
    if auth != "1234":
        add_log(f"Failed exit payment attempt. Error: Invalid auth code {auth}")
        return jsonify({
            "success": False,
            "error": "Invalid auth code"
        }), 403

    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()
    c.execute("""
        SELECT paid
        FROM tickets
        WHERE code = ?
    """, (code,))

    ticket = c.fetchone()
    if not ticket:
        add_log(f"Failed exit payment attempt. Error: Ticket {code} not found")
        conn.close()
        return jsonify({
            "success": False,
            "error": "Ticket not found"
        }), 404
    
    c.execute("""
        UPDATE tickets
        SET paid = 1,
        exited = 1
        WHERE code = ?
        """, (code,))
    
    conn.commit()
    conn.close()

    add_log(f"Payment successful for ticket {code}. Gate opening.")
    return jsonify({
        "success": True,
        "message": "Payment successful, gate opening"
        })


@app.route("/staff-login", methods=["GET", "POST"])
def staff_login():
    error = None
    
    if request.method == "POST":
        code = request.form.get("code")
        if code == STAFF_CODE:
            session["staff_logged_in"] = True
            return redirect("/staff")
        else:
            error = "Invalid code. Please try again."
    return render_template("staff_login.html", error=error)

@app.route("/staff-logout")
def staff_logout():
    session.clear()
    return redirect("/staff-login")

@app.route("/staff/terminal")
def staff_terminal():
    if not session.get("staff_logged_in"):
        add_log("Unauthorized access attempt to staff terminal. Redirected to login.")
        return redirect("/staff-login")
    output = ""

    if request.method == "POST":
        cmd = request.form.get("cmd", "").strip().lower()
        conn = sqlite3.connect("tickets.db")
        c = conn.cursor()

        if cmd.startswith("show tickets"):
            c.execute("SELECT code, paid, exited FROM tickets")
            rows = c.fetchall()
            output = "\n".join(
                [f"{r[0]} | paid={r[1]} | exited={r[2]}" for r in rows]
            )

        elif cmd.startswith("waive "):
            code = cmd.replace("waive ", "").strip()
            c.execute("""
                UPDATE tickets
                SET price = 0, paid = 1
                WHERE code = ?
            """, (code,))

            conn.commit()
            add_log(f"Terminal console has waived ticket {code}")
            output = f"Waived ticket {code}"
        
        elif cmd.startswith("open gate "):
            code = cmd.replace("open gate ", "").strip()
            add_log(f"Manually opened gate for ticket {code} using terminal console")
            output = f"Gate opened for ticket {code}"

        elif cmd == "help":
            output = (
                "Commands:\n"
                "show tickets\n"
                "waive <code>\n"
                "open gate <code>\n"
            )
        else:
            output = "Unknown command. Type 'help' for a list of commands."
        conn.close()
    return render_template("terminal.html", output=output)

@app.route("/staff")
def staff():
    if "staff_logged_in" not in session:
        add_log("Unauthorized access attempt to staff page. Redirected to login.")
        return redirect("/staff-login")

    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()
    c.execute("""
        SELECT code, paid, entry_time, exited
        FROM tickets
        ORDER BY entry_time DESC
    """)

    tickets = c.fetchall()
    conn.close()
    ticket_data = []
    now = int(time.time())
    add_log(f"Fetching ticket data at {now}")
    for ticket in tickets:
        code, paid, entry_time, exited = ticket
        minutes = max(1, (now - entry_time) // 60)
        if paid:
            minutes = 0
            amount = 0
        else:
            amount, minutes = calculate_price(entry_time)

        ticket_data.append({
            "code": code,
            "paid": bool(paid),
            "exited": bool(exited),
            "minutes": minutes,
            "amount_due": amount,
            "entry_time": entry_time
        })

    return render_template("staff.html", tickets=ticket_data)

@app.route("/generate_ticket")
def generate_ticket():

    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()
    c.execute("""
              SELECT value FROM meta WHERE key ='ticket'
    """)

    row = c.fetchone()
    number = row[0] if row else 40
    new_number = number + 1
    code = f"A{new_number}"
    entry_time = int(time.time())
    initial_price = 0
    add_log(f"Generated ticket {code} at {entry_time}")

    c.execute("""
        UPDATE meta SET value=? WHERE key='ticket'
    """, (new_number,))
    
    c.execute("""
        INSERT INTO tickets (code, paid, entry_Time, price)
        VALUES (?, ?, ?, ?)
    """, (code, 0, entry_time, initial_price))

    conn.commit()
    conn.close()
    return jsonify({"code": code})

@app.route("/pay")
def pay():
    return render_template("pay.html")
add_log("Accessed pay page")

@app.route("/check_ticket", methods=["POST"])
def check_ticket():
    data = request.get_json(silent=True) or {}
    code = data.get("code")

    if not code:
        add_log(f"Failed ticket code check. Error: No code provided")
        return jsonify({
            "success": False,
            "error": "No code provided"
        }), 400
    
    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute(
        "SELECT code, paid FROM tickets WHERE code = ?",
        (code,)
    )
    ticket = c.fetchone()

    conn.close()

    if ticket is None:
        add_log(f"Failed ticket code check. Error: Ticket {code} not found")
        return jsonify({
            "success": False,
            "error": "Ticket not found"
        }), 404

    return jsonify({"success": True, "code": ticket[0], "paid": bool(ticket[1])})
    add_log(f"Successful ticket code check for ticket {code}")

@app.route("/mark_paid", methods=["POST"])
def mark_paid():

    data = request.get_json(silent=True) or {}

    code = data.get("code")

    if not code:
        add_log(f"Failed to mark ticket as paid. Error: No code provided")
        return jsonify({
            "success": False,
            "error": "No code provided"
        }), 400

    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute(
        """
        SELECT paid
        FROM tickets
        WHERE code = ?
        """,
        (code,)
    )

    ticket = c.fetchone()

    if ticket is None:
        add_log(f"Unable to mark ticket as paid. Error: Ticket {code} not found")
        conn.close()

        return jsonify({
            "success": False,
            "error": "Ticket not found"
        }), 404

    paid = ticket[0]

    if paid:

        add_log(f"Failed to mark ticket as paid. Error: Ticket {code} already paid")
        conn.close()

        return jsonify({
            "success": False,
            "error": "Ticket already paid"
        }), 400

    c.execute(
        """
        UPDATE tickets
        SET paid = 1
        WHERE code = ?
        """,
        (code,)
    )

    conn.commit()
    conn.close()

    add_log(f"Marked ticket {code} as paid successfully") 
    return jsonify({
        "success": True
    })


@app.route("/price", methods=["POST"])
def price():
    data = request.get_json(silent=True) or {}
    code = data.get("code")

    if not code:
        add_log(f"Failed to calculate price. Error: No code provided")
        return jsonify({
            "success": False,
            "error": "No code provided"
        }), 400
    
    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute(
        """
        SELECT entry_time, paid
        FROM tickets
        WHERE code = ?
        """,
        (code,)
    )
    ticket = c.fetchone()
    conn.close()

    if ticket is None:
        add_log(f"Failed to calculate price. Error: Ticket {code} not found")
        return jsonify({
            "success": False,
            "error": "Ticket not found"
        }), 404
    
    entry_time, paid = ticket
    if paid:
        return jsonify({
            "success": True,
            "amount_due": 0,
            "minutes": 0
        })
    
    now = int(time.time())
    minutes = max(1,(now - entry_time) // 60)

    amount, minutes = calculate_price(entry_time)
    add_log(f"Calculated price for ticket {code}: ${amount} for {minutes} minutes")
    return jsonify({
        "success": True,
        "amount": amount,
        "minutes": minutes
    })

if __name__ == "__main__":
    print()
    time.sleep(0.1)
    print("Starting LicensePortal v0.1")
    time.sleep(0.1)
    print("This software is licensed to " + LICENSE_NAME + " . (actually there is no license :P)")
    time.sleep(0.1)
    print("For support, please create a GitHub issue or contact @BennyGaming635")
    time.sleep(0.1)
    print("Note this software is provided as-is without any warranties, so use at your own risk.")
    time.sleep(0.1)
    print("Thank you, now loading")
    time.sleep(2)
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print("=============================================")
    print("             LICENSEPORTAL V0.1.1")
    print("=============================================")
    time.sleep(0.5)
    print()
    print("System Status")
    time.sleep(0.01)
    print(" ✓ Flask Server Running")
    time.sleep(1)
    print(" ✓ Ticket Database Running")
    time.sleep(1)
    print(" ✓ Dynamic Pricing Enabled")
    time.sleep(1)
    print(" ✓ Staff Portal Running")
    time.sleep(1)
    print()
    print("Entry Terminal:")
    time.sleep(0.2)
    print(" http://127.0.0.1:5000/")
    time.sleep(0.2)
    print()
    print("Payment Terminal")
    time.sleep(0.2)
    print(" http://127.0.0.1:5000/pay")
    time.sleep(0.2)
    print()
    print("Exit Terminal")
    time.sleep(0.2)
    print(" http://127.0.0.1:5000/exit")
    time.sleep(0.2)
    print()
    print(" Staff Portal")
    time.sleep(0.2)
    print(" http://127.0.0.1:5000/staff")
    time.sleep(0.2)
    print()
    print("Thank you for using LicensePortal!")
    time.sleep(2)
    print()
    app.run(host="0.0.0.0", port=5000)