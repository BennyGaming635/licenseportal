from flask import Flask, render_template, jsonify, request
import sqlite3
import time

COST_PER_MINUTE = 0.05

app = Flask(__name__)

ticket_number = 0

def init_db():
    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            code TEXT PRIMARY KEY,
            paid INTEGER DEFAULT 0
            entry_time INTEGER
        )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def kiosk():
    return render_template("kiosk.html")

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
    code = request.json.get("code")

    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute("SELECT paid FROM tickets WHERE code = ?", (code,))
    ticket = c.fetchone()

    if not ticket:
        conn.close()
        return jsonify({"success": False, "error": "Invalid ticket"})

    if ticket[0] == 1:
        conn.close()
        return jsonify({"success": False, "error": "Already paid"})

    c.execute("UPDATE tickets SET paid = 1 WHERE code = ?", (code,))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route("/price", methods=["POST"])
def price():
    code = request.json.get("code")

    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute("SELECT entry_time FROM tickets WHERE code = ?", (code,))
    ticket = c.fetchone()
    conn.close()

    if not ticket:
        return jsonify({"success": False})
    
    entry_time, paid = ticket
    if paid:
        return jsonify({"success": True, "amount": 0})
    
    now = int(time.time())
    minutes = max(1, (now - entry_time) // 60)
    amount = round(minutes * COST_PER_MINUTE, 2)

    return jsonify({"success": True, "amount": amount, "minutes": minutes})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)