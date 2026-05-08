from flask import Flask, render_template, jsonify, request
import sqlite3

app = Flask(__name__)

ticket_number = 0

def init_db():
    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            code TEXT PRIMARY KEY,
            paid INTEGER DEFAULT 0
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

    c.execute("INSERT INTO tickets (code) VALUES (?)", (code,))

    conn.commit()
    conn.close()

    return jsonify({"code": code})

@app.route("/pay")
def pay():
    return render_template("pay.html")

@app.route("/check_ticket", methods=["POST"])
def check_ticket():
    code = request.json.get("code")

    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute("SELECT * FROM tickets WHERE code = ?", (code,))
    ticket = c.fetchone()
    conn.close()

    if ticket:
        return jsonify({
            "success": True,
            "paid": bool(ticket[1])
        })
    
    return jsonify({
        "success": False
    })

@app.route("/mark_paid", methods=["POST"])
def mark_paid():
    code = request.json.get("code")
    conn = sqlite3.connect("tickets.db")
    c = conn.cursor()

    c.execute("UPDATE tickets SET paid = 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)