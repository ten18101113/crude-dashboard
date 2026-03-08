#!/usr/bin/env python3
import requests
import pandas as pd
from datetime import datetime, timedelta
import sys
import json
from io import StringIO

OUTPUT_FILE = "bdti_latest.json"
CSV_FILE = "bdti_data.csv"
DAYS_BACK = 400
TICKER = "BAID.F"


def fetch_bdti(ticker, days):
    end = datetime.today()
    start = end - timedelta(days=days)
    url = (
        "https://stooq.com/q/d/l/"
        "?s=" + ticker
        + "&d1=" + start.strftime("%Y%m%d")
        + "&d2=" + end.strftime("%Y%m%d")
        + "&i=d"
    )
    print("  URL: " + url)
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))
    if df.empty or "Date" not in df.columns or "Close" not in df.columns:
        raise ValueError("No data: " + resp.text[:200])
    df = df[["Date", "Close"]].copy()
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna().sort_values("date").reset_index(drop=True)
    return df


def main():
    print("BDTI fetch started: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    try:
        df = fetch_bdti(TICKER, DAYS_BACK)
        print("  Fetched " + str(len(df)) + " rows")
        df.to_csv(CSV_FILE, index=False)
        latest = df.iloc[-1]
        result = {
            "date": latest["date"],
            "value": float(latest["value"]),
            "data": df.tail(400).to_dict(orient="records"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f)
        print("  Saved " + OUTPUT_FILE + " and " + CSV_FILE)
    except Exception as e:
        print("  Skip: " + str(e))
        sys.exit(0)


if __name__ == "__main__":
    main()
