"""
Google Trends scraper (via pytrends) — gets the two CSVs you see in the UI:
1) Interest over time
2) Interest by region (countries)

Usage examples:
  # Basic: terms inline, custom date range
  python trends_scraper.py --terms "inteligencia artificial, machine learning,
   datos" --start 2022-01-01 --end 2025-08-31

  # From CSV file with a 'term' column (one term per row)
  python trends_scraper.py --input terms.csv --start 2023-01-01 --end
   2025-08-31

  # YouTube search only
  python trends_scraper.py --terms "python" --start 2024-01-01 --end
   2024-12-31 --gprop youtube

Notes:
- The 'Interest by region' is fetched at the country level (worldwide). If you
  want subregions, run again with --geo=AR (for example) to get provinces.
- Be mindful of Google rate limits. This script implements simple backoff.
- Requires: pip install pytrends pandas tqdm
"""

import argparse
import time
from pathlib import Path
from typing import List

import pandas as pd
from pytrends.request import TrendReq
from tqdm import tqdm

GPROP_MAP = {
    "web": "",               # default web search
    "images": "images",
    "news": "news",
    "youtube": "youtube",
    "shopping": "froogle",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download Google Trends CSV-like"
                                            " data using pytrends.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--terms", type=str,
                     help="Comma-separated list of search terms.")
    src.add_argument("--input", type=str,
                     help="CSV with a column named 'term'. One term per row.")
    p.add_argument("--start", type=str, required=True,
                   help="Start date YYYY-MM-DD")
    p.add_argument("--end", type=str, required=True,
                   help="End date YYYY-MM-DD")
    p.add_argument("--geo", type=str, default="",
                   help="Geography code ('' for worldwide, 'AR'"
                   " for Argentina, etc).")
    p.add_argument("--cat", type=int, default=0,
                   help="Category ID (0=all).")
    p.add_argument("--gprop", type=str, choices=list(GPROP_MAP.keys()),
                   default="web", help="Search property.")
    p.add_argument("--tz", type=int, default=0,
                   help="Timezone offset minutes from UTC"
                   "(0=UTC, -180 for Buenos Aires).")
    p.add_argument("--hl", type=str, default="es-AR",
                   help="Host language, e.g., 'es-AR', 'en-US'.")
    p.add_argument("--sleep", type=float, default=3,
                   help="Seconds to sleep between requests (baseline).")
    p.add_argument("--retries", type=int, default=4,
                   help="Max retries per request with exponential backoff.")
    p.add_argument("--outdir", type=str, default="trends_output",
                   help="Output folder.")
    p.add_argument("--combine", action="store_true",
                   help="Also create combined CSVs across all terms.")
    return p.parse_args()


def load_terms(args: argparse.Namespace) -> List[str]:
    if args.terms:
        terms = [t.strip() for t in args.terms.split(",") if t.strip()]
        return terms
    df = pd.read_csv(args.input)
    if "term" not in df.columns:
        raise ValueError("Input CSV must have a 'term' column.")
    return df["term"].dropna().astype(str).str.strip().tolist()


def timeframe_str(start: str, end: str) -> str:
    return f"{start} {end}"


def mk_client(hl: str, tz: int) -> TrendReq:
    return TrendReq(hl=hl, tz=tz, retries=0, backoff_factor=0)


def safe_build_payload(py: TrendReq, kw_list: List[str], timeframe: str,
                       geo: str, cat: int, gprop: str,
                       base_sleep: float, retries: int) -> None:
    for attempt in range(retries):
        try:
            py.build_payload(kw_list=kw_list, timeframe=timeframe,
                             geo=geo, cat=cat, gprop=gprop)
            time.sleep(base_sleep * (1 + 0.15 * attempt))
            return
        except Exception as e:
            last_err = e
            sleep_for = base_sleep * (2 ** attempt)
            time.sleep(sleep_for)
    raise RuntimeError(f"Failed to build payload for {kw_list}. Last"
                       f"error: {last_err}")


def fetch_interest_over_time(py: TrendReq) -> pd.DataFrame:
    df = py.interest_over_time()
    if df is not None and 'isPartial' in df.columns:
        df = df.drop(columns=['isPartial'])
    return df


def fetch_interest_by_region(py: TrendReq,
                             resolution: str = "COUNTRY"
                             ) -> pd.DataFrame:
    return py.interest_by_region(resolution=resolution, inc_low_vol=True,
                                 inc_geo_code=True)


def sanitize_filename(name: str) -> str:
    bad = '<>:"/\\|?*'
    for ch in bad:
        name = name.replace(ch, "_")
    return name


def save_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=True)


def main():
    args = parse_args()
    terms = load_terms(args)
    tf = timeframe_str(args.start, args.end)
    gprop_val = GPROP_MAP[args.gprop]

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    per_term_dir = outdir / "per_term"
    combined_dir = outdir / "combined"
    per_term_dir.mkdir(exist_ok=True)
    if args.combine:
        combined_dir.mkdir(exist_ok=True)

    py = mk_client(args.hl, args.tz)

    all_iot_frames = []
    all_ibr_frames = []

    for term in tqdm(terms, desc="Processing terms"):
        kw = [term]
        safe_build_payload(py, kw_list=kw, timeframe=tf, geo=args.geo,
                           cat=args.cat, gprop=gprop_val,
                           base_sleep=args.sleep, retries=args.retries)

        iot = fetch_interest_over_time(py)
        if iot is not None and not iot.empty:
            iot_path = (per_term_dir
                        / f"{sanitize_filename(term)}__interest_over_time.csv")
            save_csv(iot, iot_path)
            if args.combine:
                tmp = iot.copy()
                tmp["__term"] = term
                all_iot_frames.append(tmp.reset_index()
                                      .rename(columns={"index": "date"}))

        resolution = "REGION" if args.geo else "COUNTRY"
        ibr = fetch_interest_by_region(py, resolution=resolution)
        if ibr is not None and not ibr.empty:
            ibr_path = (
                        per_term_dir
                        / f"{sanitize_filename(term)}__interest_by_{resolution
                                                                    .lower()}"
                        ".csv"
                        )
            save_csv(ibr, ibr_path)
            if args.combine:
                tmp = ibr.copy().reset_index(
                ).rename(columns={ibr.index.name or "geoName": "region"})
                tmp["__term"] = term
                all_ibr_frames.append(tmp)

    if args.combine:
        if all_iot_frames:
            iot_combined = pd.concat(all_iot_frames, ignore_index=True)
            save_csv(iot_combined, combined_dir
                     / "interest_over_time__combined.csv")
        if all_ibr_frames:
            ibr_combined = pd.concat(all_ibr_frames, ignore_index=True)
            save_csv(ibr_combined, combined_dir
                     / f"interest_by_{'region' if args.geo else 'country'}"
                     "__combined.csv")

    print(f"Done. Outputs in: {outdir.resolve()}")


if __name__ == "__main__":
    main()
