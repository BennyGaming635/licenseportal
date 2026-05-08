from flask import Flask, render_template, jsonify
import sqlite3

app = Flask(__name__)

ticket_number = 0

@app.route('/')
def kiosk():
    return render_template('kiosk.html')

@app.route("/generate_ticket")
def generate_ticket():
    global ticket_number

    ticket_number += 1
    code = ticket_number

    conn= sqlite3.connect('tickets.db')
    c = conn.cursor()

    c.execute("""
              CREATE TABLE IF NOT EXISTS tickets (
                    code INTEGER,
                    paid INTEGER DEFAULT 0
              )
        """)
    
    c.execute("INSERT INTO tickets (code) VALUES (?)", (code,))
    conn.commit()
    conn.close()

    return jsonify({"code": code})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)