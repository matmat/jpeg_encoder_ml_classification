#!/usr/bin/env python3
import pandas as pd
import os
import argparse
import csv  # Import the csv module to use its quoting constants

def concatenate_tsv_files(directory, output_file):
    all_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.tsv')]
    df_list = []

    for file in all_files:
        # Read the data ensuring all data is treated as string type
        df = pd.read_csv(file, delimiter='\t', dtype=str)
        # Add filename column with .tsv replaced by .jpg
        df['filename'] = os.path.basename(file).replace('.tsv', '.jpg')
        df_list.append(df)

    # Concatenate all dataframes, aligning on columns
    concatenated_df = pd.concat(df_list, ignore_index=True, sort=False)

    # Save to a new TSV file, ensuring no index and minimal quoting
    concatenated_df.to_csv(output_file, sep='\t', index=False, quoting=csv.QUOTE_MINIMAL)

def main():
    parser = argparse.ArgumentParser(description="Concatenate TSV files into one, adding a filename column.")
    parser.add_argument("directory", type=str, help="Directory containing TSV files.")
    parser.add_argument("output_file", type=str, help="Output file name for the concatenated TSV.")
    
    args = parser.parse_args()
    
    concatenate_tsv_files(args.directory, args.output_file)

if __name__ == "__main__":
    main()

