"""Read-only data and audited actions for the Stitch-derived local web interface.

The calculation endpoints in web_api remain the authoritative Python engines.
"""

from io import BytesIO
from typing import Literal

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.config_model import get_decision_params_registry
from backend.data_loader import validate_user_csv
from backend.data_quality import get_system_data_quality
from backend.features import generate_features
from backend.integrations.integration_manager import IntegrationManager
from backend.route_market import get_all_route_market_histories, get_route_market_history
from backend.storage import append_audit_log, get_audit_trail, get_decision_versions, save_decision_version, save_shipment
from backend.validation import build_validation_chart_data, run_real_validation
from backend.web_api import WebRequest, calculate, clean

router = APIRouter(prefix="/stitch", tags=["Stitch interface"])


def _processed():
    from backend.data_loader import load_raw_datasets
    return generate_features(load_raw_datasets())


@router.get("/explorer")
def explorer(kind: Literal["route", "dataset"] = "route", route_key: str = "AU_HPT -> IN_PDP",
             offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    if kind == "route":
        try:
            df = get_all_route_market_histories() if route_key == "All Routes" else get_route_market_history(route_key)
        except (KeyError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc
    else:
        df = _processed()
    return clean({"rows": df.iloc[offset:offset + limit], "total": len(df),
                  "columns": list(df.columns), "offset": offset, "is_demo_data": True})


@router.get("/explorer-summary")
def explorer_summary():
    df = _processed()
    numeric = df.select_dtypes(include="number")
    quality = [{"column": c, "missing": int(df[c].isna().sum()),
                "missing_pct": round(float(df[c].isna().mean() * 100), 2),
                "type": str(df[c].dtype)} for c in df.columns]
    return clean({"observations": len(df), "features": len(df.columns),
                  "start_date": df.date.min(), "end_date": df.date.max(),
                  "quality": quality, "correlation": numeric.corr().reset_index(),
                  "is_demo_data": True})


@router.get("/export/{kind}")
def export(kind: Literal["route", "dataset"]):
    df = get_all_route_market_histories() if kind == "route" else _processed()
    name = "FreightIQ_route_freight_rates.csv" if kind == "route" else "FreightIQ_modelling_dataset.csv"
    return Response(df.to_csv(index=False), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(422, "Choose a CSV file.")
    contents = await file.read(2_000_001)
    if len(contents) > 2_000_000:
        raise HTTPException(413, "CSV exceeds the 2 MB preview limit.")
    try:
        df = pd.read_csv(BytesIO(contents))
        valid, missing, cleaned = validate_user_csv(df)
    except Exception as exc:
        raise HTTPException(422, f"CSV could not be parsed: {exc}") from exc
    return clean({"filename": file.filename, "is_valid": valid, "missing_columns": missing,
                  "rows_count": len(cleaned), "columns": list(cleaned.columns),
                  "sample_data": cleaned.head(10), "preview_only": True})


@router.get("/integrations")
def integrations():
    quality = get_system_data_quality("DEMO")
    weather = run_real_validation()
    return clean({"connectors": IntegrationManager(mode="DEMO").get_connector_status_summary(),
                  "quality": quality, "parameters": get_decision_params_registry(),
                  "weather_status": weather, "audit": get_audit_trail(limit=100)})


@router.get("/audit")
def audit():
    return clean({"events": get_audit_trail(limit=100)})


class OperatorNote(BaseModel):
    congestion: float = Field(ge=0, le=100)
    vessel_count: int = Field(ge=1, le=100)
    demurrage_inr_day: float = Field(ge=0)


@router.post("/operator-note")
def operator_note(note: OperatorNote):
    row_id = append_audit_log(
        action="MANUAL_OVERRIDE_RECORDED", source_mode="MANUAL_OVERRIDE",
        details=f"Operator Note: Congestion={note.congestion:.0f}, Vessels={note.vessel_count}, Demurrage=₹{note.demurrage_inr_day:,.0f}/d",
    )
    return {"id": row_id, "message": "Operator note recorded. Model inputs were not changed."}


@router.post("/solve")
def solve(req: WebRequest):
    result = calculate("optimize", req)
    if not result.get("success"):
        raise HTTPException(422, result.get("error", "No feasible candidate."))
    shipment_id = "FIQ-2026-0001"
    origin, destination = req.route_key.split(" -> ")
    save_shipment({"shipment_id": shipment_id, "cargo_type": req.cargo_type,
                   "quantity_tonnes": req.quantity_tonnes, "origin": origin,
                   "destination": destination, "vessel_class": req.vessel_class,
                   "risk_tolerance": req.risk_tolerance,
                   "earliest_date": req.earliest_date, "latest_date": req.latest_date,
                   "demurrage_rate": req.demurrage_rate or 22000.0})
    version = save_decision_version(shipment_id, result["recommendation"])
    return clean({**result, "decision_version": version})


@router.get("/decisions")
def decisions():
    return clean({"versions": get_decision_versions("FIQ-2026-0001")})


@router.get("/weather-chart")
def weather_chart():
    chart = build_validation_chart_data(model_name="SARIMA", horizon=30)
    if chart is None:
        return {"status": "UNAVAILABLE", "message": "Cached public observations are unavailable."}
    return clean({"status": "OK", **chart})
