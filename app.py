from flask import Flask, request, jsonify, render_template
import pyodbc
import os
import datetime
from db_connect import get_conn

app = Flask(__name__)



@app.route("/")
def home():
    return render_template("service_attempts.html")

@app.route("/api/service_attempts")
def service_attempts():
    
    name = request.args.get("name", "")
    activity_type = request.args.get("activity_type", "")
    start = request.args.get("start")
    end = request.args.get("end")
    event_number = request.args.get("event_number", "")

    start_epoch = None
    end_epoch = None

    if start:
        start_epoch = int(datetime.datetime.fromisoformat(start).timestamp() * 1000)

    if end:
        end_epoch = int(datetime.datetime.fromisoformat(end).timestamp() * 1000)
 

    conn = get_conn()
    cur = conn.cursor()
    print("DEBUG PARAMS:", f"%{name}%", activity_type, start_epoch, end_epoch)
    cur.execute("""
        SELECT
            event_number,
            name,
            event_status,
            force_used,
            bwc_recording,
            activity_type,
            DATEADD(SECOND, arrival_time / 1000, '1970-01-01') AS arrival_dt
        FROM esri_events
        WHERE arrival_time IS NOT NULL

        AND ( ? = '' OR LOWER(name) LIKE LOWER(?) )
        AND ( ? = '' OR LOWER(activity_type) LIKE LOWER(?) )

        AND (
            ? = '' OR
            REPLACE(REPLACE(event_number, '-', ''), ' ', '') =
            REPLACE(REPLACE(?, '-', ''), ' ', '')
        )

        AND ( ? IS NULL OR arrival_time >= ? )
        AND ( ? IS NULL OR arrival_time <= ? )

        ORDER BY arrival_time DESC
    """,
    name, f"%{name}%",
    activity_type, f"%{activity_type}%",
    event_number, event_number,
    start_epoch, start_epoch,
    end_epoch, end_epoch
    )

    rows = cur.fetchall()

    data = []
    for r in rows:
        data.append({
            "event_number": r[0],
            "name": r[1],
            
            "event_status": r[2],
            "force_used": r[3],
            "bwc": r[4],
            "activity_type": r[5],
            "arrival_time": r[6].strftime("%Y-%m-%d %H:%M")
        })

    return jsonify({
        "count": len(data),
        "records": data
    })

if __name__ == "__main__":
    app.run(debug=True)