"""
"""

import pandas as pd

class HHTAnalysis:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
    
    @property
    def geocoded(self):
        return self.df[self.df['latitude'].notna() & self.df['longitude'].notna()]

    @property
    def years(self):
        return [int(y) for y in sorted(self.df['year'].dropna().unique())]
    
    @property
    def missing_years(self):
        years_present = set(self.yearly_summary["year"])
        full_range = set(range(min(years_present), max(years_present) + 1))
        return sorted(full_range - years_present)

    @property
    def annotated_years(self):
        df = self.df
        # Filter to rows where 'notes' is not null/empty
        filtered = df[df["notes"].notna() & (df["notes"].str.strip() != "")]
        
        # Group by year and collapse the notes (you can change join separator if needed)
        result = (
            filtered
            .groupby("year", as_index=False)
            .agg({"notes": lambda x: " | ".join(x.dropna().unique())})
        )

        return result.reset_index(drop=True)
        
    @property
    def yearly_summary(self):
        df = self.df

        # Keep only rows with a valid address
        valid = df[df["clean_address"].notna() & (df["clean_address"].str.strip() != "")]

        # Group by year, count addresses, extract informal_chairs and notes
        result = (
            valid
            .groupby("year", as_index=False)
            .agg(
                informal_chairs=("informal_chairs", lambda x: next((v for v in x if pd.notna(v) and str(v).strip() != ""), None)),
                address_count=("clean_address", "count"),
                notes=("notes", lambda x: next((v for v in x if pd.notna(v) and str(v).strip() != ""), ""))
            )
            .sort_values("year")
        )

        return result.reset_index(drop=True)
    
    @property
    def chair_summary(self):
        df = self.df

        # Create long-form DataFrames for chair1 and chair2
        chair1_df = df[["year", "chair1", "chair1_first_name", "chair1_last_name"]].copy()
        chair1_df.columns = ["year", "chair", "chair_first_name", "chair_last_name"]

        chair2_df = df[["year", "chair2", "chair2_first_name", "chair2_last_name"]].copy()
        chair2_df.columns = ["year", "chair", "chair_first_name", "chair_last_name"]

        # Combine the two
        combined = pd.concat([chair1_df, chair2_df], ignore_index=True)

        # Drop empty or null chair names
        combined = combined[combined["chair"].notna() & (combined["chair"].str.strip() != "")]

        # Group by chair name and count unique years
        summary = (
            combined
            .groupby(["chair", "chair_first_name", "chair_last_name"], as_index=False)
            .agg(year_count=("year", lambda x: x.nunique()))
            .sort_values(by=["year_count", "chair_last_name", "chair_first_name"], ascending=[False, True, True])
        )

        return summary.reset_index(drop=True)


    @property
    def street_summary(self):
        df = self.df

        # Create a combined street name
        df["full_street"] = df["street_name"].str.strip() + " " + df["street_type"].str.strip()

        # Group by combined street name and count
        summary = (
            df.groupby("full_street", as_index=False)
            .size()
            .rename(columns={"size": "count"})
            .sort_values("count", ascending=False)
        )

        return summary.reset_index(drop=True)


    @property
    def number_summary(self):
        df = self.df

        # Ensure street_number is numeric and drop nulls
        valid = df[df["street_number"].notna()]
        valid = valid.copy()
        valid["street_number"] = valid["street_number"].astype(int)

        # Calculate block (floor to nearest 100)
        valid["block"] = (valid["street_number"] // 100) * 100
        valid["block_label"] = valid["block"].astype(str) + " block"

        # Group by block label and count
        summary = (
            valid.groupby("block_label", as_index=False)
            .size()
            .rename(columns={"size": "count"})
            .sort_values("count", ascending=False)
        )

        return summary.reset_index(drop=True)

    @property
    def address_summary(self):
        df = self.df

        # Filter out null addresses and ensure all required fields exist
        valid = df[df["clean_address"].notna()].copy()
        valid["place_name"] = valid["place_name"].fillna("")

        # Group by address and place_name, count occurrences
        summary = (
            valid
            .groupby(["address", "place_name", "street_name", "street_number"], as_index=False)
            .size()
            .rename(columns={"size": "count"})
            .sort_values(by=["count", "street_name", "street_number"], ascending=[False, True, True])
        )

        return summary[["address","place_name","count"]].reset_index(drop=True)
    
    @property
    def place_summary(self):
        df = self.df

        # Filter for non-empty place names
        valid = df[df["place_name"].notna() & (df["place_name"].str.strip() != "")].copy()

        summary = (
            valid
            .groupby("place_name", as_index=False)
            .size()
            .rename(columns={"size": "count"})
            .sort_values("count", ascending=False)
        )

        return summary.reset_index(drop=True)