#!/usr/bin/env python

import pandas as pd
import csv
import argparse

def main():
    parser = argparse.ArgumentParser(description="Process combined and IDs TSV files, treating all data as strings and removing leading zeros from IDs and scenes.")
    parser.add_argument('combined_file', type=str, help="Path to the combined TSV file.")
    parser.add_argument('ids_file', type=str, help="Path to the IDs TSV file.")
    parser.add_argument('output_file', type=str, help="Path to save the augmented TSV file.")

    args = parser.parse_args()

    # Load both files with all columns as strings
    combined = pd.read_csv(args.combined_file, sep='\t', dtype=str)
    ids = pd.read_csv(args.ids_file, sep='\t', dtype=str)

    # Replace nan values generated after reading the files
    combined.fillna('', inplace=True)
    ids.fillna('', inplace=True)

    # Apply the function to extract data from the filename
    combined[['ID', 'prov', 'scene']] = combined['filename'].apply(lambda x: pd.Series(extract_info(x)))

    # Merge the combined data with the IDs data on 'ID' column using a left join
    combined = pd.merge(combined, ids, on='ID', how='left')

    # Remove leading zeros from the 'ID' field after merging
    combined['ID'] = combined['ID'].apply(lambda x: x.lstrip('0') if x.isdigit() else x)

    # Replace nan values that might be generated after merge
    combined.fillna('', inplace=True)

    # Add a constant column 'dataset' with all values set to 'Forchheim'
    combined['dataset'] = 'Forchheim'

    # Save the merged and augmented data to a TSV file without quoting unless necessary
    combined.to_csv(args.output_file, sep='\t', index=False, quoting=csv.QUOTE_NONE)

def extract_info(filename):
    parts = filename.split('_')
    id_part = parts[0][1:]  # Remove 'D' from ID but keep zero-padding for matching
    prov = parts[2]
    scene = parts[3].split('.')[0].lstrip('0')  # Remove '.jpg' and leading zeros from scene
    return id_part, prov, scene

if __name__ == "__main__":
    main()
