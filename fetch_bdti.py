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
    df.columns =
