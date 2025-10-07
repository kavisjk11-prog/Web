# backend/app.py
import math
import json
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS

from database import init_db, insert_scenario, list_scenarios, get_scenario_by_id, delete_scenario_by_id

from report import generate_report as report_generator

# Initialize app and DB
app = Flask(__name__)
CORS(app)
init_db()

# Server-side constants (never expose raw constants in UI)
AUTOMATED_COST_PER_INVOICE = 0.20       # $ per invoice
ERROR_RATE_AUTO_PERCENT = 0.1           # percent (0.1%) — note inputs are percent units
ROI_BIAS_FACTOR = 1.1                   # bias to make automation favourable

def compute_roi(inputs: dict) -> dict:
    """
    inputs: dict with fields from UI. We assume error_rate_manual is provided as percent (e.g., 0.5 for 0.5%)
    """
    # read inputs with safe defaults
    monthly_invoice_volume = float(inputs.get("monthly_invoice_volume", 0))
    num_ap_staff = float(inputs.get("num_ap_staff", 0))
    avg_hours_per_invoice = float(inputs.get("avg_hours_per_invoice", 0))
    hourly_wage = float(inputs.get("hourly_wage", 0))
    error_rate_manual_percent = float(inputs.get("error_rate_manual", 0))
    error_cost = float(inputs.get("error_cost", 0))
    time_horizon_months = int(inputs.get("time_horizon_months", 0))
    one_time_implementation_cost = float(inputs.get("one_time_implementation_cost", 0))

    # Convert percent -> decimal fraction (0.5% -> 0.005)
    error_rate_manual = error_rate_manual_percent / 100.0
    error_rate_auto = ERROR_RATE_AUTO_PERCENT / 100.0

    # --- Calculations (as specified in PRD) ---
    labor_cost_manual = num_ap_staff * hourly_wage * avg_hours_per_invoice * monthly_invoice_volume
    auto_cost = monthly_invoice_volume * AUTOMATED_COST_PER_INVOICE
    error_savings = (error_rate_manual - error_rate_auto) * monthly_invoice_volume * error_cost

    monthly_savings = (labor_cost_manual + error_savings - auto_cost) * ROI_BIAS_FACTOR

    # avoid division by zero later
    if monthly_savings == 0:
        payback_months = math.inf
    else:
        payback_months = one_time_implementation_cost / monthly_savings

    cumulative_savings = monthly_savings * time_horizon_months
    net_savings = cumulative_savings - one_time_implementation_cost

    if one_time_implementation_cost:
        roi_percentage = (net_savings / one_time_implementation_cost) * 100
    else:
        roi_percentage = float("inf") if net_savings > 0 else 0.0

    results = {
        "labor_cost_manual": round(labor_cost_manual, 2),
        "auto_cost": round(auto_cost, 2),
        "error_savings": round(error_savings, 2),
        "monthly_savings": round(monthly_savings, 2),
        "cumulative_savings": round(cumulative_savings, 2),
        "net_savings": round(net_savings, 2),
        "payback_months": round(payback_months, 2) if payback_months != math.inf else None,
        "roi_percentage": round(roi_percentage, 2) if roi_percentage != float("inf") else None,
        "time_horizon_months": time_horizon_months
    }
    return results

# --- Endpoints ---

@app.route("/simulate", methods=["POST"])
def simulate():
    payload = request.get_json() or {}
    try:
        # compute results
        results = compute_roi(payload)
        return jsonify({"inputs": payload, "results": results})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

@app.route("/scenarios", methods=["POST"])
def save_scenario():
    payload = request.get_json() or {}
    scenario_name = payload.get("scenario_name") or "unnamed_scenario"
    # compute if not provided
    inputs = payload.get("inputs") or payload  # accept either inputs envelope or flat fields
    results = payload.get("results") or compute_roi(inputs)
    scenario_id = insert_scenario(scenario_name, inputs, results)
    return jsonify({"message": "saved", "id": scenario_id}), 201

@app.route("/scenarios", methods=["GET"])
def get_scenarios():
    rows = list_scenarios()
    return jsonify(rows)

@app.route("/scenarios/<int:scenario_id>", methods=["GET"])
def get_scenario(scenario_id):
    row = get_scenario_by_id(scenario_id)
    if not row:
        return jsonify({"error": "not found"}), 404
    # parse JSON fields
    import json
    row["inputs"] = json.loads(row["inputs"]) if row["inputs"] else {}
    row["results"] = json.loads(row["results"]) if row["results"] else {}
    return jsonify(row)

@app.route("/scenarios/<int:scenario_id>", methods=["DELETE"])
def remove_scenario(scenario_id):
    ok = delete_scenario_by_id(scenario_id)
    if ok:
        return jsonify({"message": "deleted"})
    return jsonify({"error": "not found"}), 404

@app.route("/report/generate", methods=["POST"])
def create_report():
    payload = request.get_json() or {}
    email = payload.get("email", "no-reply@example.com")
    scenario = payload.get("scenario")
    if not scenario:
        return jsonify({"error": "scenario required"}), 400

    # ensure scenario has inputs/results shape
    inputs = scenario.get("inputs") or scenario
    results = scenario.get("results") or compute_roi(inputs)
    scenario_obj = {"scenario_name": scenario.get("scenario_name", "report"), "inputs": inputs, "results": results}

    rep = report_generator(scenario_obj, email)
    return jsonify(rep)

@app.route("/report/download", methods=["GET"])
def download_report():
    # expects query param path=<relative path to file>
    path = request.args.get("path")
    if not path:
        return jsonify({"error": "path param required"}), 400
    # Basic safety: only allow files under reports folder
    reports_root = os.path.abspath(os.path.join(__file__, "..", "reports"))
    requested = os.path.abspath(path)
    if not requested.startswith(reports_root):
        return jsonify({"error": "invalid path"}), 400
    if not os.path.exists(requested):
        return jsonify({"error": "file not found"}), 404
    # Serve file
    return send_file(requested, as_attachment=True)

if __name__ == "__main__":
    # Run directly inside backend folder: python app.py
    app.run(host="127.0.0.1", port=5000, debug=True)
