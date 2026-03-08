#!/usr/bin/env python3
"""
========================================================
Step 2: BDTI 運賃データ自動取得スクリプト
========================================================
概要:
  Baltic Dirty Tanker Index (BDTI) を stooq.com から取得し、
  ダッシュボードが読み込める bdti.csv として保存します。

使い方:
  1. 必要ライブラリのインストール:
       pip install pandas requests

  2. 実行:
       python fetch_bdti.py

  3. 生成されるファイル:
       bdti.csv  ← dashboard_v2.html と同フォルダに置く

  4. 自動更新（毎朝8時に実行する例 — cron/タスクスケジューラ）:
       # macOS/Linux の cron に追加:
       0 8 * * 1-5 /usr/bin/python3 /path/to/fetch_bdti.py

  注意:
    - stooq.com のデータは非公式利用です。
      サイト側の仕様変更でフォーマットが変わる可能性があります。
    - BDTI は "Dubai → Japan VLCC 運賃" の直接値ではなく、
      原油タンカー運賃全体の代替指標（proxy）です。
    - BDTIティッカー: stooq では "BAID.F" として公開されています。
========================================================
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# ── 設定 ─────────────────────────────────────────────
OUTPUT_FILE = "bdti.csv"   # ダッシュボードHTMLと同フォルダに出力
DAYS_BACK   = 400          # 取得する日数（余裕をもたせる）
TICKER      = "BAID.F"     # stooq における BDTI のティッカー
# ────────────────────────────────────────────────────

def fetch_bdti(ticker: str, days: int) -> pd.DataFrame:
    """
    stooq.com から指定ティッカーの日次データを取得する。
    URL形式: https://stooq.com/q/d/l/?s=TICKER&d1=YYYYMMDD&d2=YYYYMMDD&i=d
    返り値: Date, Close カラムを持つ DataFrame
    """
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

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    # stooq は CSV 形式で返す: Date,Open,High,Low,Close,Volume
    from io import StringIO
    df = pd.read_csv(StringIO(resp.text))

    if df.empty or "Date" not in df.columns:
        raise ValueError(f"データが取得できませんでした。レスポンス:\n{resp.text[:300]}")

    # 必要カラムのみ抽出
    df = df[["Date", "Close"]].copy()
    df.columns = ["date", "value"]
    df["date"]  = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna().sort_values("date").reset_index(drop=True)

    return df


def save_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False)
    print(f"  保存完了: {path}  ({len(df)} 行)")


def main():
    print("=" * 55)
    print("  BDTI 自動取得スクリプト (Step 2)")
    print(f"  実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    # ── BDTI 取得 ──────────────────────────────────
    print(f"\n[1] BDTI ({TICKER}) を stooq から取得中...")
    try:
        df = fetch_bdti(TICKER, DAYS_BACK)
        print(f"  取得件数: {len(df)} 件")
        print(f"  期間: {df['date'].min()} 〜 {df['date'].max()}")
        print(f"  最新値: {df['value'].iloc[-1]:.1f} pt")
        save_csv(df, OUTPUT_FILE)
    except Exception as e:
        print(f"  [エラー] {e}")
        sys.exit(1)

    # ── 確認表示 ──────────────────────────────────
    print("\n[2] 最新5件:")
    print(df.tail(5).to_string(index=False))

    print("\n" + "=" * 55)
    print(f"  完了! '{OUTPUT_FILE}' を dashboard_v2.html と")
    print(f"  同じフォルダに置いてブラウザで開いてください。")
    print("=" * 55)

    # ── 追加データソースのヒント ──────────────────
    print("""
[補足] stooq で取得できる他の関連ティッカー:
  BAID.F  = BDTI (Baltic Dirty Tanker Index)  ← このスクリプト
  BAIT.F  = BCTI (Baltic Clean Tanker Index)
  BADI.F  = BDI  (Baltic Dry Index)
  CL.F    = WTI 原油先物
  BRN.F   = Brent 原油先物 (参考)

[次のステップ]
  Step 3: 戦争保険料の自動取得 or 手動入力フォームの追加
    → war_insurance_input.py を参照してください
""")


if __name__ == "__main__":
    main()
