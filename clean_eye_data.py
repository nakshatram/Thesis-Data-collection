import sys
import pathlib
import pandas as pd
import numpy as np

N = 2  # multiplier for MAD threshold (procedure.docx)
COLS = ["Left Pupil Dilation", "Right Pupil Dilation"]

def mad(arr):
    """Median Absolute Deviation, scaled like SD (b = 1.4826)."""
    med = np.median(arr)
    return 1.4826 * np.median(np.abs(arr - med))

def clean_series(x: pd.Series) -> pd.Series:
    # Guard against empty series
    if x.empty:
        return x

    # 1. first-order differences
    diffs = np.maximum(
        np.abs(np.diff(x, prepend=x.iloc[0])),
        np.abs(np.diff(x, append=x.iloc[-1]))
    )
    # 2. threshold
    ts = np.median(diffs) + N * mad(diffs)
    # 3. flag positions where either neighbour jump > ts
    mask = (
        (np.abs(np.diff(x, prepend=x.iloc[0])) > ts) |
        (np.abs(np.diff(x, append=x.iloc[-1])) > ts)
    )
    x_clean = x.copy()
    x_clean[mask] = np.nan
    # 4. linear interpolation
    return x_clean.interpolate(limit_direction="both")

def clean_eye_file(fp: pathlib.Path):
    df = pd.read_csv(fp)

    # Skip completely empty files
    if df.empty:
        print(f"⚠️  Skipping empty file: {fp}")
        return

    for col in COLS:
        if col not in df.columns:
            print(f"⚠️  Column '{col}' not found in {fp}, skipping that column")
            continue
        df[col] = clean_series(df[col])

    out_fp = fp.with_name(fp.stem + "_clean.csv")
    df.to_csv(out_fp, index=False)
    print("✓ cleaned", fp)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_eye_data.py <participants_data_folder>")
        sys.exit(1)

    root = pathlib.Path(sys.argv[1])
    matches = list(root.rglob("eye_data.csv"))
    print(f"Found {len(matches)} eye_data.csv files:")
    for p in matches:
        print("   ", p)

    for eye_csv in matches:
        clean_eye_file(eye_csv)
