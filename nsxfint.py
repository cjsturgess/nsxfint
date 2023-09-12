"""
File: nsxfint.py
Author: CJ Sturgess
Date: 2023-09-12
Description: Identifies the NSX features in use per-VM, given a Usage Meter report (VMH).
"""

# Imports
import argparse
from pathlib import Path
import pandas as pd
import numpy as np


# Arguments
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Identified NSX features in use per-VM, given a Usage Meter report (VMH)."
    )

    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default="vmh.tsv",
        help="Input file (VMH) to parse. CSV or TSV format accepted. Defaults to vmh.tsv.",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default="nsxfint.csv",
        help="Output file (CSV) to write. Defaults to nsxfint.csv.",
    )

    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enables debug mode and disabled cleanup.",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enables verbose logging."
    )

    return parser.parse_args()


# Helper Functions
def log(msg, debug=False, verbose=False, fatal=False):
    """Prints a log message."""
    if debug and args.debug:
        print(f"DEBUG: {msg}")
    elif verbose and args.verbose:
        print(f"VERBOSE: {msg}")
    elif fatal:
        print(f"FATAL: {msg}")
        exit(1)
    else:
        print(f"INFO: {msg}")


def skip_rows(vmh_path):
    log("Determining rows to skip...", debug=True)
    skip_rows = []
    with open(vmh_path, "r") as f:
        for i, line in enumerate(f.readlines()):
            if len(line.split("\t")) == 1:
                skip_rows.append(i)
    log(f"Rows to skip: {skip_rows}", debug=True)
    return skip_rows


# Main Function
def main():
    """Main function."""

    # Check provided file exists and is CSV or TSV.
    if not args.input.exists():
        log(f"Input file {args.input} does not exist.", fatal=True)
    elif args.input.suffix not in [".csv", ".tsv"]:
        log(f"Input file {args.input} is not CSV or TSV.", fatal=True)

    # Parse and clean input file.
    log(f"Reading input file {args.input}...", verbose=True)
    vmh_df = pd.read_csv(args.input, sep="\t", skiprows=skip_rows(args.input))
    vmh_df.rename(inplace=True, columns={"#Name": "Name"})

    # Read in NSX Features
    log("Reading NSX Features...", verbose=True)
    nsxf_df = pd.read_csv("nsx_features.csv").dropna()

    # Replace "-" with 0 for NSXFInt in VMH
    vmh_df["NsxFInt"] = vmh_df["NsxFInt"].fillna(0).replace("-", 0).astype(int)

    # Create new DF with VM names and NSX Features
    nsxfint_df = vmh_df[["Name", "NsxFInt"]]

    # Add column for each NSX Feature
    editions = ["", "Base", "Professional", "Advanced", "Enterprise Plus"]
    for _, row in nsxf_df.iterrows():
        nsxfint_df[row["NSX Feature Name"]] = np.where(
            (nsxfint_df["NsxFInt"] & row["NSXFINT"]) > 0,
            editions.index(row["Edition"]),
            0,
        )

    # Calculate the NSX edition for each row
    nsxfint_df["NSX Edition"] = nsxfint_df[nsxf_df["NSX Feature Name"]].max(axis=1)
    nsxfint_df[nsxf_df["NSX Feature Name"]] = np.where(
        nsxfint_df[nsxf_df["NSX Feature Name"]] > 0, True, ""
    )
    nsxfint_df["NSX Edition"] = nsxfint_df["NSX Edition"].apply(lambda x: editions[x])

    # Save to CSV
    nsxfint_df.to_csv(args.output, index=False)


if __name__ == "__main__":
    global args
    args = parse_args()
    main()
