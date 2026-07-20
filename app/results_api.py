import logging

import requests
from flask import Flask, jsonify, request

from app import config
from app.db import get_connection

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)


@app.route("/patient/<patient_id>/results")
def patient_results(patient_id):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM mart.patient_results WHERE patient_id = '" + patient_id + "'"
    logging.info(f"query = {query}")
    cur.execute(query)
    return jsonify(cur.fetchall())


@app.route("/kpi")
def kpi():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT lab_id, n_results, avg_turnaround_hours FROM mart.kpi_lab_daily")
    return jsonify(cur.fetchall())


@app.route("/dashboard")
def dashboard():
    # Dashboard interne branché sur `mart`, utilisé par le pilotage ET par les médecins.
    # Aucun contrôle de profil : tout utilisateur connecté voit les résultats de tous les patients.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT patient_id, patient_last_name, analysis_code, result_value, result_flag, sample_date "
        "FROM mart.patient_results"
    )
    rows = cur.fetchall()
    html = ["<h1>Vitalab — Dashboard pilotage</h1>", "<table border='1'>"]
    html.append(
        "<tr><th>patient_id</th><th>nom</th><th>analyse</th>"
        "<th>résultat</th><th>flag</th><th>date</th></tr>"
    )
    for row in rows:
        html.append("<tr>" + "".join(f"<td>{col}</td>" for col in row) + "</tr>")
    html.append("</table>")
    return "\n".join(html)


@app.route("/report")
def report():
    # Récupère un rapport distant à partir de l'URL passée en paramètre
    url = request.args.get("url")
    return requests.get(url).content


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
