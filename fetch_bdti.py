#!/usr/bin/env python3
import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
import json

OUTPUT_FILE = "bdti_latest.json"
CSV_FILE    = "bdti_data.csv"
DAYS_BACK   = 400
TICKER      = "BAID.F"

def fetch_bdti(ticker, days):
    end   = datetime.today()
    start = end - timedelta(days=days)
    url = (
        f"https://stooq.com/q/d/l/"
        f"?s={ticker}"
        f"&d1={start.strftime('%Y%m%d')}"
        f"&d2={end.strftime('%Y%m%d')}"
        f"&i=d"
    )
    print(f"  URL: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(resp.text))
    if df.empty or "Date" not in df.columns or "Close" not in df.columns:
        raise ValueError(f"No data: {resp.text[:200]}")
    df = df[["Date", "Close"]].copy()
df.columns = ["date", "value"]
df["date"]  = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna().sort_values("date").reset_index(drop=True)
    return df

def main():
    print(f"BDTI fetch started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        df = fetch_bdti(TICKER, DAYS_BACK)
        print(f"  Fetched {len(df)} rows, latest: {df['value'].iloc[-1]:.1f}")
        df.to_csv(CSV_FILE, index=False)
        latest = df.iloc[-1]
        result = {
            "date":    latest["date"],
            "value":   float(latest["value"]),
            "data":    df.tail(400).to_dict(orient="records"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f)
        print(f"  Saved {OUTPUT_FILE} and {CSV_FILE}")
    except Exception as e:
        print(f"  Skip: {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()
