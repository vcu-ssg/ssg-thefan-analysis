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

        return result
        
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

        return result

