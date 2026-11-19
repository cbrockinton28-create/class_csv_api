import io
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI(
    title="Class Dataset API",
    description="Public API serving cleaned dataset records in CSV or JSON format.",
    version="1.0.0",
)

# Allow classmates/instructors to call the API from any script, browser, or notebook
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

CSV_PATH = Path(__file__).parent / "XXX.csv"


def get_clean_df() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise HTTPException(status_code=500, detail="Dataset file missing on server.")
    df = pd.read_csv(CSV_PATH, header=2, skiprows=[3, 4], na_values=["."])
    df = df[df["Status"].isin(["Dead", "Alive"])].copy()
    return df


@app.get("/")
def root():
    return {
        "message": "Dataset API is live.",
        "endpoints": {
            "interactive_docs": "/docs",
            "data_csv": "/data?format=csv",
            "data_json": "/data?format=json",
            "summary": "/summary",
        },
    }


@app.get("/summary")
def dataset_summary():
    df = get_clean_df()
    return {
        "total_rows": len(df),
        "columns": list(df.columns),
    }


@app.get("/data")
def get_data(
    limit: int = Query(100, ge=1, le=10000, description="Number of rows to return"),
    sex: Optional[str] = Query(None, description="Filter by Sex (e.g., Male, Female)"),
    status: Optional[str] = Query(None, description="Filter by Status (Dead, Alive)"),
    format: str = Query("csv", pattern="^(csv|json)$", description="Return format: csv or json"),
):
    df = get_clean_df()

    if sex:
        df = df[df["Sex"].str.lower() == sex.strip().lower()]
    if status:
        df = df[df["Status"].str.lower() == status.strip().lower()]

    df = df.head(limit)

    if format == "json":
        return df.to_dict(orient="records")

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dataset_export.csv"},
    )
