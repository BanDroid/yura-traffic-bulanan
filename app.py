from flask import Flask, render_template, request, jsonify
from jinja2 import environment
from os import environ
from datetime import datetime
import json
from requests import get

__import__("dotenv").load_dotenv()

app = Flask(__name__)
BASE_API_URL: str = environ.get("BASE_API_URL", "http://localhost:8090")


@app.route("/")
def home():
    r = get(
        f"{BASE_API_URL}/api/collections/traffic_bulanan/records?skipTotal=1&fields=id,tgl_bulan&sort=-tgl_bulan"
    )
    traffic_bulanan = r.json()
    return render_template(
        "pages/home.html",
        title="Traffic Bulan Ini",
        traffic_bulanan=traffic_bulanan,
    )


@app.route("/<string:id>")
def past_month(id):
    r = get(
        f"{BASE_API_URL}/api/collections/traffic_bulanan/records?skipTotal=1&fields=id,tgl_bulan&sort=-tgl_bulan"
    )
    traffic_bulanan = r.json()
    selected_month_data_response = get(
        f"{BASE_API_URL}/api/collections/traffic_bulanan/records/{id}"
    )
    selected_month_data = selected_month_data_response.json()
    month_before_response = get(
        f"{BASE_API_URL}/api/collections/traffic_bulanan/records?sort=-created&perPage=1&page=1&filter=tgl_bulan<\"{selected_month_data['tgl_bulan']}\""
    )
    month_before = (
        month_before_response.json()["items"][0]
        if len(month_before_response.json()["items"]) == 1
        else None
    )
    date_object = datetime.strptime(
        selected_month_data["tgl_bulan"], "%Y-%m-%d %H:%M:%S.%fZ"
    )
    title = f"{date_object.strftime('%B')} - {date_object.year}"
    if not month_before:
        return render_template(
            "pages/month.html",
            title=title,
            traffic_bulanan=traffic_bulanan,
            bulan_ini=sorted(
                json.loads(selected_month_data["data"]),
                key=lambda traffic: traffic["views"],
                reverse=True,
            ),
            bulan_kemarin=[],
        )
    return render_template(
        "pages/month.html",
        title=title,
        traffic_bulanan=traffic_bulanan,
        bulan_ini=sorted(
            json.loads(selected_month_data["data"]),
            key=lambda traffic: traffic["views"],
            reverse=True,
        ),
        bulan_kemarin=json.loads(month_before["data"]),
    )


@app.route("/api/now", methods=["GET"])
def get_current_month_data():
    past_traffic_response = get(
        f"{BASE_API_URL}/api/collections/traffic_bulanan/records?skipTotal=1&fields=data&sort=-tgl_bulan"
    )
    latest_data_response = get(
        f"{BASE_API_URL}/api/collections/daftar_pj/records?skipTotal=1&fields=judul,views&sort=-views"
    )
    if len(past_traffic_response.json()["items"]) == 0:
        return jsonify({"total_terbaru": latest_data_response.json()["items"]})
    return jsonify(
        {
            "total_terbaru": latest_data_response.json()["items"],
            "bulan_kemarin": json.loads(
                past_traffic_response.json()["items"][0]["data"]
            ),
        }
    )


@app.template_filter("format_date_output")
def format_date_output(date: str):
    date_object = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%fZ")
    return f"{date_object.strftime('%B')} - {date_object.year}"


debug: bool = (
    True if environ.get("PYTHON_ENV", "development") == "development" else False
)
if __name__ == "__main__":
    app.run(
        host=environ.get("HOST", "0.0.0.0"),
        port=int(environ.get("PORT", "5000")),
        debug=debug,
    )
