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
    Identify header rows (4-digit year + 'chair') and detect Tour A / Tour B markers.
    - Tour A markers are removed (Tour A is default).
    - Tour B markers switch tour to B until next year header.
    - Year headers reset tour back to A.

    Returns:
    - DataFrame with 'year_and_chair' and 'tour' columns.
    """
    df = df.copy()

    # Clean 'data' column
    if "data" in df.columns:
        df["data"] = df["data"].astype(str).str.strip()

    # Detect year/chair header rows
    year_chair_pattern = r'^\s*\d{4}.*chair'
    is_year_chair_header = df["data"].str.contains(year_chair_pattern, case=False, na=False)

    # Detect Tour markers
    is_tour_a_marker = df["data"].str.contains(r'\bTour A\b', case=False, na=False)
    is_tour_b_marker = df["data"].str.contains(r'\bTour B\b', case=False, na=False)

    # Create year_and_chair column
    df["year_and_chair"] = df["data"].where(is_year_chair_header)
    df["year_and_chair"] = df["year_and_chair"].ffill()

    # Initialize tour: default A
    df["tour"] = "A"

    # Step through rows carefully
    current_tour = "A"

    for idx, row in df.iterrows():
        if is_year_chair_header.loc[idx]:
            current_tour = "A"  # reset to Tour A on new year
        elif is_tour_b_marker.loc[idx]:
            current_tour = "B"  # switch to Tour B
        elif is_tour_a_marker.loc[idx]:
            current_tour = "A"  # Tour A marker reaffirms A (no effect really)

        df.at[idx, "tour"] = current_tour

    # Remove all control rows (year headers, Tour A, Tour B)
    remove_headers = is_year_chair_header | is_tour_a_marker | is_tour_b_marker
    df_clean = df[~remove_headers].copy().reset_index(drop=True)

    # Final cleanup
    for col in ["data", "year_and_chair", "tour"]:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()

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
    Splits the 'data' column into 'address', 'unit_number', 'place_name', and 'host_name'.
    Handles unit numbers even without comma before '#', extracts place names, and splits address vs host safely.
    """
    df = df.copy()

    dash_pattern = re.compile(r'[-–—]{1,2}')
    place_pattern = re.compile(r'\[(.*?)\]')
    unit_pattern = re.compile(r'\s*#(\w+)')

    def smart_split(text):
        original_text = text  # Save for debugging if needed

        # 1. Extract place_name if present
        place_match = place_pattern.search(text)
        place_name = place_match.group(1).strip() if place_match else None

        if place_match:
            text = text.replace(place_match.group(0), "").strip()

        # 2. Extract unit_number even if no comma
        unit_match = unit_pattern.search(text)
        unit_number = unit_match.group(1).strip() if unit_match else None

        if unit_match:
            # Remove the matched unit pattern (with optional preceding whitespace/comma)
            text = unit_pattern.sub('', text, count=1).strip()

        # 3. Fix if no dash but comma exists (rare case)
        if not dash_pattern.search(text) and ',' in text:
            text = text.replace(',', ' –', 1)

        # 4. Split on FIRST dash
        matches = list(dash_pattern.finditer(text))
        if matches:
            first = matches[0]
            address = text[:first.start()].strip()
            host = text[first.end():].strip()
        else:
            address = text.strip()
            host = None

        # 5. Special case: if no host but place_name exists
        if not host and place_name:
            host = place_name

        return pd.Series([address, unit_number, place_name, host])

    df[["address", "unit_number", "place_name", "host_name"]] = df["data"].apply(smart_split)

    return df

def split_address_parts(df):
    """
    Splits the 'address' column into 'street_number', 'street_name', and 'street_type'.
    Handles hyphenated numbers and street types with or without trailing period.

    Parameters:
    - df (pd.DataFrame): Must contain 'address' column.

    Returns:
    - pd.DataFrame: With 'street_number', 'street_name', and 'street_type' columns.
    """
    df = df.copy()

    # Pattern to match number, name, and type
    street_type_pattern = r'(Ave\.?|St\.?|Blvd\.?|Dr\.?|Ct\.?|Rd\.?|Ln\.?|Way\.?|Cir\.?|Terr\.?|Pl\.?|Alley\.?)'

#    street_type_pattern = r'(Ave\.?|St\.?|Blvd\.?|Dr\.?|Ct\.?|Rd\.?|Ln\.?|Way\.?|Cir\.?|Terr\.?|Pl\.?)'
    pattern = rf'^\s*(\d+(?:-\w+)?)\s+(.*?)\s+{street_type_pattern}\s*$'

    extracted = df["address"].str.extract(pattern)
    extracted.columns = ["street_number", "street_name", "street_type"]

    df[["street_number", "street_name", "street_type"]] = extracted

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
    }

    df = df.copy()


    for pattern, replacement in street_corrections.items():
        df["data"] = df["data"].str.replace(pattern, replacement, regex=True)


    return df


def recode_street_names(df):
    """
    Recode specific street_name values to standard form.
    
    Parameters:
    - df (pd.DataFrame): DataFrame containing 'street_name' column.

    Returns:
    - pd.DataFrame: Updated DataFrame with corrected 'street_name' values.
    """
    df = df.copy()

    # Define your custom street name mappings here
    street_recode_map = {
        "West Franklin": "W. Franklin",
        "Harvie" : "N. Harvie",
        "Franklin": "W. Franklin",
        "Strawberry": "N. Strawberry",
        "Broad": "W. Broad",
        "Main": "W. Main",
        "Addison": "S. Addison",
        "West Grace" : "W. Grace",
        "Plum" : "N. Plum",
        "Shields" : "N. Shields",
        "Stafford" : "N. Stafford",
        "Meadow" : "N. Meadow",
        "Rowland" : "N. Rowland",
        "Morris": "N. Morris",
        "Linden" : "N. Linden",
        "Harrison" : "N. Harrison",
        "Lombardy" : "N. Lombardy",
        # Add more as needed...
    }

    # Apply the recoding
    df["street_name"] = df["street_name"].replace(street_recode_map)

    return df
