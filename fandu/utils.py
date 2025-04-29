"""
Utilities for Fandu
"""

import os
import re
import click
import pandas as pd
from rapidfuzz import fuzz, process


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

def load_excel_sheet(file_path, *, sheet_name=0, header_row=0, skip_rows=None, column_names=None, columns=None):
    """
    Load an Excel sheet into a pandas DataFrame with optional mojibake repair.
    
    Parameters:
    - file_path: Path to the Excel file.
    - sheet_name: Sheet index or name (default: 0).
    - header_row: Row to use as header (ignored if column_names is provided).
    - skip_rows: List of rows to skip.
    - column_names: If provided, overrides header and uses these names.
    - columns: Restrict to specific columns (e.g., [0, 2, 4] or ['Name', 'Address'])
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

        if columns is not None:
            read_args["usecols"] = columns

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

def resort_by_year_and_chair_block_order(df):
    """
    Resort a DataFrame by 'year_and_chair' groups in chronological order,
    while preserving the relative order of rows within each group.

    Returns:
    - A sorted DataFrame
    """
    df = df.copy()
    
    # Create a temporary column that represents the original row order
    df["_original_index"] = range(len(df))
    
    # Extract the 4-digit year prefix for sorting
    df["_year"] = df["year_and_chair"].str.extract(r'^(\d{4})').astype(float)
    
    # Sort by year, then by original row order within the block
    df_sorted = df.sort_values(by=["_year", "_original_index"]).drop(columns=["_year", "_original_index"])
    
    return df_sorted.reset_index(drop=True)


def extract_and_fill_year_and_chair_column(df):
    """
    Identify header rows (4-digit year + 'chair') and detect Tour A / Tour B markers.
    - Tour A markers are removed (Tour A is default).
    - Tour B markers switch tour to B until next year header.
    - Year headers reset tour back to A.
    - Notes in square brackets are extracted from the year/chair row and applied only to rows in that group.
    - If no data rows are found for a year_and_chair group, insert a placeholder row with just that year_and_chair and note.
    
    Returns:
    - DataFrame with columns: 'data', 'year_and_chair', 'tour', 'notes'
    """
    df = df.copy()
    df["data"] = df["data"].astype(str).str.strip()

    # Identify control rows
    year_chair_pattern = r'^\s*\d{4}.*chair'
    is_year_chair_header = df["data"].str.contains(year_chair_pattern, case=False, na=False)
    is_tour_a_marker = df["data"].str.contains(r'\bTour A\b', case=False, na=False)
    is_tour_b_marker = df["data"].str.contains(r'\bTour B\b', case=False, na=False)

    # Extract notes and remove them from data
    df["extracted_note"] = df["data"].where(is_year_chair_header).str.extract(r'\[([^\]]+)\]', expand=False)
    df.loc[is_year_chair_header, "data"] = df.loc[is_year_chair_header, "data"].str.replace(r'\s*\[[^\]]+\]', '', regex=True)

    # Set year_and_chair and forward fill
    df["year_and_chair"] = df["data"].where(is_year_chair_header)
    df["year_and_chair"] = df["year_and_chair"].ffill()

    # Set notes per group
    df["notes"] = ""
    current_note = ""
    last_yac = None

    for idx, row in df.iterrows():
        if is_year_chair_header.loc[idx]:
            current_note = row["extracted_note"] if pd.notna(row["extracted_note"]) else ""
            last_yac = row["year_and_chair"]
        elif row["year_and_chair"] == last_yac:
            df.at[idx, "notes"] = current_note

    # Set tour logic
    df["tour"] = "A"
    current_tour = "A"

    for idx, row in df.iterrows():
        if is_year_chair_header.loc[idx]:
            current_tour = "A"
        elif is_tour_b_marker.loc[idx]:
            current_tour = "B"
        elif is_tour_a_marker.loc[idx]:
            current_tour = "A"
        df.at[idx, "tour"] = current_tour

    # Keep track of data groups
    groups_with_data = set(df.loc[~(is_year_chair_header | is_tour_a_marker | is_tour_b_marker), "year_and_chair"])

    # Insert filler rows for missing groups
    fillers = []
    for idx, row in df[is_year_chair_header].iterrows():
        yac = row["year_and_chair"]
        if yac not in groups_with_data:
            fillers.append({
                "data": "",
                "year_and_chair": yac,
                "tour": "A",
                "notes": row["extracted_note"] if pd.notna(row["extracted_note"]) else ""
            })

    # Remove control rows and reassemble
    df_clean = df[~(is_year_chair_header | is_tour_a_marker | is_tour_b_marker)].copy()
    df_clean = pd.concat([df_clean, pd.DataFrame(fillers)], ignore_index=True)

    for col in ["data", "year_and_chair", "tour", "notes"]:
        df_clean[col] = df_clean[col].astype(str).str.strip()

    df_clean = resort_by_year_and_chair_block_order( df_clean )
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


def extract_chair_names(chair_entry):
    """
    Extracts:
    - chair1, chair2: full parsed names
    - chair1_first, chair1_last: parsed components of chair1
    - chair2_first, chair2_last: parsed components of chair2
    """

    def get_first_and_last_name(name):
        """
        Extracts the first and last name from a full name string.
        Suffixes like 'Jr.', 'Sr.', etc. are included in the first name.
        """
        if not name or not isinstance(name, str):
            return "", ""

        name = name.strip().replace(",", "")
        parts = name.split()

        if not parts:
            return "", ""

        suffixes = {"Jr.", "Sr.", "II", "III", "IV", "Jr", "Sr"}

        if parts[-1] in suffixes:
            last_name = parts[-2] if len(parts) >= 2 else parts[-1]
            first_name = " ".join(parts[:-2] + [parts[-1]])
        else:
            last_name = parts[-1]
            first_name = " ".join(parts[:-1])

        return first_name.strip(), last_name.strip()

    if pd.isna(chair_entry) or not isinstance(chair_entry, str):
        return "", "", "", "", "", ""

    original = chair_entry.strip()

    # Remove notes unless they are a single name like (Anne)
    cleaned = re.sub(r'\(([^)]+)\)', lambda m: f"({m.group(1)})" if len(m.group(1).split()) == 1 else "", original)

    # Special case: Mr. & Mrs. Bill (Anne) Patten
    m = re.match(r'Mr\.\s*&\s*Mrs\.\s+([\w\-\.]+)\s+\(([\w\-]+)\)\s+([\w\-]+)', cleaned)
    if m:
        husband_first = m.group(1).strip()
        wife_first = m.group(2).strip()
        last = m.group(3).strip()
        chair1 = f"{wife_first} {last}"
        chair2 = f"{husband_first} {last}"
        chair1_first, chair1_last = get_first_and_last_name(chair1)
        chair2_first, chair2_last = get_first_and_last_name(chair2)
        return chair1, chair1_first, chair1_last, chair2, chair2_first, chair2_last

    # Special case: Priscilla & Tom George
    m = re.match(r'([\w\-]+)\s*&\s*([\w\-]+)\s+([\w\-]+)$', cleaned)
    if m:
        first1 = m.group(1).strip()
        first2 = m.group(2).strip()
        last = m.group(3).strip()
        chair1 = f"{first1} {last}"
        chair2 = f"{first2} {last}"
        chair1_first, chair1_last = get_first_and_last_name(chair1)
        chair2_first, chair2_last = get_first_and_last_name(chair2)
        return chair1, chair1_first, chair1_last, chair2, chair2_first, chair2_last

    # General split
    parts = re.split(r'\s*&\s*|\s+and\s+', cleaned, maxsplit=1)
    result = []

    for part in parts:
        part = part.strip()

        # Case: embedded name in parentheses
        m = re.search(r'\(([^)]+)\)\s+([\w\-\']+)$', part)
        if m:
            first = m.group(1).strip()
            last = m.group(2).strip()
            result.append(f"{first} {last}")
            continue

        # Case: honorific or suffix present
        m = re.match(r'(Mr\.|Mrs\.|Ms\.|Miss)?\s*(.+)', part)
        if m:
            name = m.group(2).strip()
            if re.match(r'[A-Z]\.[A-Z]\.', name) or re.search(r'\b(Jr\.|Sr\.|II|III|IV)\b', original):
                chair1_first, chair1_last = get_first_and_last_name(original)
                return original, chair1_first, chair1_last, "", "", ""
            result.append(name)
            continue

        # Fallback
        result.append(part)

    # Pad to two names
    while len(result) < 2:
        result.append("")

    chair1 = result[0]
    chair2 = result[1]
    chair1_first, chair1_last = get_first_and_last_name(chair1)
    chair2_first, chair2_last = get_first_and_last_name(chair2)

    return chair1, chair1_first, chair1_last, chair2, chair2_first, chair2_last

def split_and_add_chairs( df ):
    """
    Pull out the chair names to new column.
    """
    df = df.copy()
    df[['chair1', 'chair1_first_name', 'chair1_last_name', \
        'chair2', 'chair2_first_name', 'chair2_last_name']] = df['chair'].apply(lambda x: pd.Series(extract_chair_names(x)))
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
    street_type_pattern = r'(Ave\.?|St\.?|Blvd\.?|Dr\.?|Ct\.?|Rd\.?|Ln\.?|Way\.?|Cir\.?|Terr\.?|Pl\.?|Alley\.?|Al\.?)'

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
        # "Strawberry": "N. Strawberry",
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


def build_clean_address( df ):
    df = df.copy()
    df["clean_address"] = df["street_number"] + " " + df["street_name"] + " " + df["street_type"]
    df["clean_address"] = df["clean_address"].fillna("")
    return df


def normalize_address(address):
    """
    Lowercase, strip, and replace common punctuation and abbreviations.
    """

    if not isinstance(address, str):
        address = str(address) if pd.notna(address) else ""

    return (address.lower()
                  .replace('.', '')
                  .replace(',', '')
                  .replace('rear', '')  # Optional: remove trailing tags
                  .replace('  ', ' ')
                  .strip())


def match_addresses(master_df, unmatched_df, threshold=90):
    # Normalize address columns
    master_df['normalized'] = master_df['AddressLabel'].apply(normalize_address)
    unmatched_df['normalized'] = unmatched_df['clean_address'].apply(normalize_address)

    # Map normalized master address to ID
    master_dict = dict(zip(master_df['normalized'], master_df['AddressId']))

    matched_rows = []
    unmatched_rows = []

    for i, row in unmatched_df.iterrows():
        unmatched_addr = row['normalized']
        original_addr = row['clean_address']
        match, score, _ = process.extractOne(unmatched_addr, master_dict.keys(), scorer=fuzz.token_sort_ratio)

        if score >= threshold:
            matched_rows.append({
                'unmatched_address': original_addr,
                'matched_address': match,
                'matched_id': master_dict[match],
                'score': score
            })
        else:
            unmatched_rows.append({
                'unmatched_address': original_addr,
                'matched_address': match,
                'matched_id': master_dict[match],
                'score': score
            })

    matched_df = pd.DataFrame(matched_rows)
    unmatched_df = pd.DataFrame(unmatched_rows)

    return matched_df, unmatched_df

