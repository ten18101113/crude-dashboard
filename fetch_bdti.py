#!/usr/bin/env python3
import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

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
    print(f"  取得URL: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(resp.text))
    if df.empty or "Date" not in df.columns or "Close" not in df.columns:
        raise ValueError(f"データなし: {resp.text[:200]}")
    df = df[["Date", "Close"]].copy()
    df.columns = ["date", "value"]
    df["date"]  = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna().sort_values("date").reset_index(drop=True)
    return df

def main():
    print("=" * 50)
    print(f"  BDTI 取得スクリプト")
    print(f"  実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    print(f"\n[1] BDTI ({TICKER}) を stooq から取得中...")
    try:
        df = fetch_bdti(TICKER, DAYS_BACK)
        print(f"  取得件数: {len(df)} 件")
        print(f"  最新値: {df['value'].iloc[-1]:.1f} pt")

        # CSV保存
        df.to_csv(CSV_FILE, index=False)
        print(f"  CSV保存: {CSV_FILE}")

        # JSON保存（ダッシュボード用）
        import json
        latest = df.iloc[-1]
        result = {
            "date":  latest["date"],
            "value": float(latest["value"]),
            "data":  df.tail(400).to_dict(orient="records"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f)
        print(f"  JSON保存: {OUTPUT_FILE}")

    except Exception as e:
        print(f"  [スキップ] {e}")
        print(f"  土日・祝日のためデータなし — 既存ファイルを維持します")
        sys.exit(0)

if __name__ == "__main__":
    main()
