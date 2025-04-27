"""
Utilities for Fandu
"""

import os
import re
import click
import pandas as pd


def test_function():
	return "Hello world!"

def standardize_string_columns(df, columns):
    """
    Ensure selected columns are converted to strings and stripped of leading/trailing spaces.

    Parameters:
    - df (pd.DataFrame): The DataFrame to clean.
    - columns (list[str]): List of column names to process.

    Returns:
    - pd.DataFrame: Updated DataFrame.
    """
    df = df.copy()

    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


def needs_mojibake_fixing(df):
    """
    Checks if mojibake-style broken characters exist in 'data' column.
    Returns True if fixing is needed.
    """
    if "data" not in df.columns:
        return False

    bad_patterns = ["â€“", "â€”", "â€œ", "â€", "â€˜", "â€™", "â€¦"]
    
    return df["data"].astype(str).str.contains('|'.join(map(re.escape, bad_patterns)), regex=True).any()

def fix_common_broken_characters(df):
    """
    Direct replace known bad mojibake sequences.
    """
    df = df.copy()

    replacements = {
        "â€“": "–",    # en dash
        "â€”": "—",    # em dash
        "â€œ": "“",    # left double quote
        "â€": "”",    # right double quote
        "â€˜": "‘",    # left single quote
        "â€™": "’",    # right single quote
        "â€¦": "…",    # ellipsis
    }

    for bad, good in replacements.items():
        df["data"] = df["data"].str.replace(bad, good, regex=False)

    return df

def fix_mojibake_dataframe(df):
    """
    Apply mojibake fixing to 'data' column.
    """
    df = df.copy()
    df["data"] = df["data"].apply(fix_mojibake_text)
    return df

def load_excel_sheet(file_path, *, sheet_name=0, header_row=0, skip_rows=None, column_names=None):
    """
    Load an Excel sheet into a pandas DataFrame with optional mojibake repair.
    """
    try:
        read_args = {
            "sheet_name": sheet_name,
            "skiprows": skip_rows,
            "engine": "openpyxl",
        }

        if column_names is not None:
            read_args["header"] = None
            read_args["names"] = column_names
        else:
            read_args["header"] = header_row

        df = pd.read_excel(file_path, **read_args)

        # Smart mojibake detection
        if needs_mojibake_fixing(df):
            click.echo("[Info] Mojibake detected. Repairing bad characters...")
            df = fix_common_broken_characters(df)
        else:
            click.echo("[Info] No mojibake detected. No repair needed.")

        return df

    except Exception as e:
        click.echo(f"[Error] Could not load Excel file: {e}")
        return pd.DataFrame()
    
def standardize_string_columns(df, columns):
    """
    Ensure selected columns are converted to strings and stripped of leading/trailing spaces.

    Parameters:
    - df (pd.DataFrame): The DataFrame to clean.
    - columns (list[str]): List of column names to process.

    Returns:
    - pd.DataFrame: Updated DataFrame.
    """
    df = df.copy()

    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df

    
def load_csv_file(file_path, *, header_row=None, skip_rows=None, column_names=None):
    """
    Load a CSV UTF-8 file into a pandas DataFrame.
    Trims and cleans all records.
    Always forces one clean string column after loading.
    """
    try:
        read_args = {
            "encoding": "utf-8",
            "skiprows": skip_rows,
            "header": header_row,
        }

        # Load whatever is there — do not pass 'names' yet
        df = pd.read_csv(file_path, **read_args)

        # Collapse all columns into a single 'data' column
        df = df.astype(str)  # Convert everything to string
        #df["data"] = df.apply(lambda row: " ".join(row.values), axis=1)
        df["data"] = df.apply(lambda row: " ".join(val for val in row.values if str(val).lower() != "nan"), axis=1)


        # Keep only the 'data' column
        df = df[["data"]]

        # Always strip leading/trailing whitespace
        df["data"] = df["data"].str.strip()
        
        # Smart mojibake detection
        if needs_mojibake_fixing(df):
            click.echo("[Info] Mojibake detected. Repairing bad characters...")
            df = fix_common_broken_characters(df)
        else:
            click.echo("[Info] No mojibake detected. No repair needed.")
        
        click.echo(f"[Info] Loaded {len(df)} rows from CSV: {file_path}")
        
        return df

    except Exception as e:
        click.echo(f"[Error] Could not load CSV file: {e}")
        return pd.DataFrame()


def extract_and_fill_year_and_chair_column(df):
    """
    Identify header rows that begin with a 4-digit year and contain 'chair',
    move them to a 'year_and_chair' column, and propagate the value downward.
    Removes the original header rows from the data.

    Parameters:
    - df (pd.DataFrame): DataFrame with a single 'data' column.

    Returns:
    - pd.DataFrame: Cleaned DataFrame with 'year_and_chair' column.
    """
    df = df.copy()

    if "data" in df.columns:
        df["data"] = df["data"].astype(str).str.strip()

    # Detect header rows
    pattern = r'^\s*\d{4}.*chair'
    is_header = df["data"].str.contains(pattern, case=False, na=False)

    # Create 'year_and_chair' only where header matches
    df["year_and_chair"] = df["data"].where(is_header)

    # Forward-fill the last valid header
    df["year_and_chair"] = df["year_and_chair"].ffill()

    # Keep only non-header rows
    df_clean = df[~is_header].copy().reset_index(drop=True)

    # Very important: clean 'data' column again after filtering
    if "data" in df_clean.columns:
        df_clean["data"] = df_clean["data"].astype(str).str.strip()

    # And also clean 'year_and_chair' for safety
    if "year_and_chair" in df_clean.columns:
        df_clean["year_and_chair"] = df_clean["year_and_chair"].astype(str).str.strip()

    return df_clean

def split_year_and_chair_columns(df):
    """
    Given a DataFrame with a 'year_and_chair' column, extract 'year' and 'chair' parts.
    Handles both 'Chair,' and 'Co-chair(s),' cases.

    Parameters:
    - df (pd.DataFrame): DataFrame with 'year_and_chair' column.

    Returns:
    - pd.DataFrame: Updated DataFrame with 'year' and 'chair' columns.
    """

    # Force year_and_chair to strings first
    if "year_and_chair" in df.columns:
        df["year_and_chair"] = df["year_and_chair"].astype(str).str.strip()


    # Extract year as first 4-digit number
    df["year"] = df["year_and_chair"].str.extract(r'(\d{4})')

    # Extract everything after 'Chair,' or 'Co-chair,' or 'Co-chairs,'
    df["chair"] = (
        df["year_and_chair"]
        .str.extract(r'(?:Co-)?chairs?,\s*(.*)', flags=re.IGNORECASE)[0]
        .str.strip()
    )

    return df



def split_address_and_host(df):
    """
    Split the 'data' column into 'address' and 'host_name'.
    If no dash separator is found but a comma is present,
    replaces the first comma with a dash to enable splitting.

    Parameters:
    - df (pd.DataFrame): DataFrame with a 'data' column.

    Returns:
    - pd.DataFrame: With 'address' and 'host_name' columns added.
    """
    dash_pattern = re.compile(r'[-–—]{1,2}')

    def smart_split(text):
        # If no dash but there is a comma, replace the first comma with a dash
        if not dash_pattern.search(text) and ',' in text:
            text = text.replace(',', ' –', 1)  # Replace only the first comma

        # Now proceed to find dashes normally
        matches = list(dash_pattern.finditer(text))
        if matches:
            last = matches[-1]
            address = text[:last.start()].strip()
            host = text[last.end():].strip()
            return pd.Series([address, host])
        else:
            return pd.Series([None, text.strip()])

    df = df.copy()
    df[["address", "host_name"]] = df["data"].apply(smart_split)
    return df


def split_address_parts(df):
    """
    Splits the 'address' column into 'street_number', 'street_name', and 'street_type'.
    Handles hyphenated numbers and street types with or without a trailing period.

    Parameters:
    - df (pd.DataFrame): Must contain 'address' column.

    Returns:
    - pd.DataFrame: With 'street_number', 'street_name', and 'street_type' columns.
    """
    # Updated pattern to allow:
    #   - Hyphenated or alphanumeric street numbers
    #   - Street types with optional periods
    street_type_pattern = r'(Ave\.?|St\.?|Blvd\.?|Dr\.?|Ct\.?|Rd\.?|Ln\.?|Way\.?|Cir\.?|Terr\.?|Pl\.?)'
    pattern = rf'^\s*(\d+(?:-\w+)?)\s+(.*?)\s+{street_type_pattern}\s*$'

    # Extract components
    extracted = df["address"].str.extract(pattern)
    extracted.columns = ["street_number", "street_name", "street_type"]

    df = df.copy()
    df[["street_number", "street_name", "street_type"]] = extracted

    return df

def move_text_to_previous_row(df, match_text):
    """
    Finds rows where 'data' starts with match_text,
    removes match_text from that row,
    and appends it to the end of the previous row's 'data'.

    Parameters:
    - df (pd.DataFrame): Must contain 'data' column.
    - match_text (str): Text to match at the beginning of 'data'.

    Returns:
    - pd.DataFrame: Updated DataFrame.
    """
    df = df.copy()
    indices_to_drop = []

    for idx in df.index:
        cell = df.at[idx, "data"]
        if isinstance(cell, str) and cell.startswith(match_text):
            # Remove the match_text from the current line
            new_text = cell[len(match_text):].strip()
            df.at[idx, "data"] = new_text

            if idx > 0:
                # Append match_text to the previous line
                df.at[idx - 1, "data"] = df.at[idx - 1, "data"].strip() + " " + match_text
            else:
                # Edge case: if it's the first row, just leave it alone
                pass

            # Mark this row for deletion
            indices_to_drop.append(idx)

    # Drop all rows that had only match_text
    df = df.drop(index=indices_to_drop).reset_index(drop=True)
    
    return df


def perform_column_cleaning( df ):
    """
    Cleans a specific column by applying street type corrections.
    
    Parameters:
    - df (pd.DataFrame): The DataFrame to clean.
    
    Returns:
    - pd.DataFrame: Updated DataFrame.
    """

    street_corrections = {
        r"\bAve(?!\.)\b": "Ave.",
        r"\bSt(?!\.)\b": "St.",
        r"\bBlvd(?!\.)\b": "Blvd.",
        r"\bDr(?!\.)\b": "Dr.",
        r"\bCt(?!\.)\b": "Ct.",
        r"\bRd(?!\.)\b": "Rd.",
        r"\bLn(?!\.)\b": "Ln.",
        r"\bWay(?!\.)\b": "Way.",
        r"\bCir(?!\.)\b": "Cir.",
        r"\bTerr(?!\.)\b": "Terr.",
        r"\bPl(?!\.)\b": "Pl.",
        r"\bCircle(?!\.)\b": "Cir.",        # <- Corrected
        r"\bAvenue(?!\.)\b": "Ave.",        # <- Corrected
        r"\bStreet(?!\.)\b": "St.",         # <- Corrected
        # Special fixes
        r"\bN\. Davis\b(?!\sAve\.?)": "N. Davis Ave.",
        r"\bN\. Allen\b(?!\sAve\.?)": "N. Allen Ave.",
        r"\bWest Grace\b(?!\sSt\.?)": "W. Grace St.",
        r"\bN(?!\.)\bHarrison\b(?!\sSt\.?)" : "Harrison St.",
        r"\bNorth Rowland\b(?!\sSt\.?)": "N. Rowland St.",
        r"\bWest Franklin\b(?!\sSt\.?)": "W. Franklin St.",
        # Full word directions
        r"\bNorth\b": "N.",
        r"\bSouth\b": "S.",
        r"\bEast\b": "E.",
        #r"\bWest\b": "W.",        
        # New directional fixes
        r"\b([NSEW])\b\s+(?=[A-Z])": r"\1. ",        
        # Fractional / unit fixes
        r"\b(\d+)\s+1/2\b": r"\1-2",
        r"\b(\d+)\s+#(\d+)\b": r"\1-\2",
        r"½": "-2",
        r"St\. John.*s United Church of Christ": "507 N. Lombardy St. - St. John’s United Church of Christ",
    

    }

    df = df.copy()


    for pattern, replacement in street_corrections.items():
        df["data"] = df["data"].str.replace(pattern, replacement, regex=True)


    ## More cleaning using local routines

    df = move_text_to_previous_row(df, match_text="Charlotte Minor")

    return df
