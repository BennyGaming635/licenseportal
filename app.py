from flask import Flask, render_template, jsonify, request, redirect, session
import sqlite3
import time

COST_PER_MINUTE = 0.05
STAFF_CODE = "1234"

app = Flask(__name__)
app.secret_key = "supersecretkey"

ticket_number = 0

def init_db():
    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            code TEXT PRIMARY KEY,
            paid INTEGER DEFAULT 0,
            entry_time INTEGER
        )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def kiosk():
    return render_template("kiosk.html")

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

@app.route("/staff")
def staff():
    if "staff_logged_in" not in session:
        return redirect("/staff-login")

    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()
    c.execute("""
        SELECT code, paid, entry_time
        FROM tickets
        ORDER BY entry_time DESC
    """)

    tickets = c.fetchall()
    conn.close()
    ticket_data = []
    now = int(time.time())
    
    for ticket in tickets:
        code, paid, entry_time = ticket
        minutes = max(1, (now - entry_time) // 60)
        amount = 0 if paid else round(minutes * COST_PER_MINUTE, 2)

        ticket_data.append({
            "code": code,
            "paid": bool(paid),
            "minutes": minutes,
            "amount_due": amount,
            "entry_time": entry_time
        })

    return render_template("staff.html", tickets=ticket_data)

@app.route("/generate_ticket")
def generate_ticket():
    global ticket_number

    ticket_number += 1
    code = f"A{ticket_number}"

    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO tickets (code, entry_time) VALUES (?, ?)",
        (code, int(time.time()))
    )

    conn.commit()
    conn.close()
    return jsonify({"code": code})

@app.route("/pay")
def pay():
    return render_template("pay.html")

@app.route("/check_ticket", methods=["POST"])
def check_ticket():
    data = request.get_json(silent=True) or {}
    code = data.get("code")

    if not code:
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
        return jsonify({
            "success": False,
            "error": "Ticket not found"
        }), 404

    return jsonify({"success": True, "code": ticket[0], "paid": bool(ticket[1])})

@app.route("/mark_paid", methods=["POST"])
def mark_paid():

    data = request.get_json(silent=True) or {}

    code = data.get("code")

    if not code:

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

        conn.close()

        return jsonify({
            "success": False,
            "error": "Ticket not found"
        }), 404

    paid = ticket[0]

    if paid:

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

    return jsonify({
        "success": True
    })

@app.route("/price", methods=["POST"])
def price():
    data = request.get_json(silent=True) or {}
    code = data.get("code")

    if not code:
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

    amount = round(minutes * COST_PER_MINUTE, 2)
    return jsonify({
        "success": True,
        "amount": amount,
        "minutes": minutes
    })
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)