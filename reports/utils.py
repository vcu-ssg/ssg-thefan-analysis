"""

"""

import pandas as pd
from pathlib import Path




class ExcelAnalyzer:
    def __init__(self, file_path, sheet_name=0):
        """Initialize with an Excel file and load it into a Pandas DataFrame."""
        self.file_path = file_path
        engine = "openpyxl"
        if Path(file_path).suffix.lower()==".xls":
            engine = "xlrd"

        self.df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine)

        # Clean up the column names to avoid leading/trailing spaces
        self.df.columns = self.df.columns.str.strip()

        # Fill missing values in "Member bundle ID or email"
        self.fill_member_bundle_column()

    def fill_member_bundle_column(self):
        """Fill missing values in 'Member bundle ID or email' with 'Email' or 'User ID'."""
        if "Member bundle ID or email" in self.df.columns:
            self.df["Member bundle ID or email"] = self.df["Member bundle ID or email"].fillna(self.df["Email"])
            self.df["Member bundle ID or email"] = self.df["Member bundle ID or email"].fillna(self.df["User ID"])

    @property
    def num_records(self):
        """Returns the total number of records (rows) in the DataFrame."""
        return len(self.df)

    @property
    def num_unique_user_ids(self):
        """Returns the number of unique values in the 'User ID' column."""
        return self.df["User ID"].nunique()

    @property
    def num_unique_nonblank_emails(self):
        """Returns the number of unique, non-blank emails in the 'Email' column."""
        return self.df["Email"].dropna().nunique()

    @property
    def num_unique_nonblank_usernames(self):
        """Returns the number of unique, non-blank values in the 'Username' column."""
        return self.df["Username"].dropna().nunique()

    @property
    def num_unique_nonblank_member_bundles(self):
        """Returns the number of unique, non-blank values in the 'Member bundle ID or email' column."""
        return self.df["Member bundle ID or email"].dropna().nunique()

    def count_membership_by_level(self):
        """Returns a dictionary of counts of 'User ID' where 'Membership enabled' is 'yes', grouped by 'Membership level'."""
        if not {"User ID", "Membership enabled", "Membership level"}.issubset(self.df.columns):
            raise ValueError("Required columns ('User ID', 'Membership enabled', 'Membership level') are missing.")

        filtered_df = self.df[self.df["Membership enabled"].str.lower() == "yes"]
        grouped_counts = filtered_df.groupby("Membership level")["User ID"].nunique()
        
        return grouped_counts
        #return grouped_counts.to_dict()  # Convert to dictionary for easy access

    def count_bundles_by_level(self):
        """Returns a dictionary of counts of 'User ID' where 'Membership enabled' is 'yes', grouped by 'Membership level'."""
        if not {"User ID", "Membership enabled", "Membership level"}.issubset(self.df.columns):
            raise ValueError("Required columns ('User ID', 'Membership enabled', 'Membership level') are missing.")

        filtered_df = self.df[self.df["Membership enabled"].str.lower() == "yes"]
        grouped_counts = filtered_df.groupby("Membership level")["Member bundle ID or email"].nunique()
        
        return grouped_counts
        #return grouped_counts.to_dict()  # Convert to dictionary for easy access

    def get_users_with_duplicate_emails(self):
        """Returns a DataFrame with 'User ID', 'Username', 'First name', 'Last name', and 'Email' 
        for all rows where 'Email' appears more than once in the dataset.
        """
        required_columns = {"User ID", "Username", "First name", "Last name", "Email"}
        if not required_columns.issubset(self.df.columns):
            raise ValueError(f"Missing required columns: {required_columns - set(self.df.columns)}")

        # Find duplicate emails (excluding NaN values)
        duplicate_emails = self.df["Email"].value_counts()
        duplicate_emails = duplicate_emails[duplicate_emails > 1].index  # Get emails that appear more than once

        # Filter the DataFrame to include only rows with duplicate emails
        duplicate_users_df = self.df[self.df["Email"].isin(duplicate_emails)][["User ID", "Username", "First name", "Last name", "Email"]]

        return duplicate_users_df

    def get_users_with_duplicate_names(self):
        """Returns a DataFrame with 'User ID', 'Username', 'First name', 'Last name', 'Email', and 'Membership enabled' 
        for all rows where the combination of 'First name' and 'Last name' appears more than once.
        """
        required_columns = {"User ID", "Username", "First name", "Last name", "Email", "Membership enabled"}
        if not required_columns.issubset(self.df.columns):
            raise ValueError(f"Missing required columns: {required_columns - set(self.df.columns)}")

        # Create a combined column of "First name" and "Last name"
        name_counts = self.df.groupby(["First name", "Last name"]).size()

        # Find names that appear more than once
        duplicate_names = name_counts[name_counts > 1].index  # Get tuples of (First name, Last name)

        # Filter the DataFrame for rows with duplicate names
        duplicate_users_df = self.df[self.df.set_index(["First name", "Last name"]).index.isin(duplicate_names)]
        
        # Select relevant columns
        return duplicate_users_df[["User ID", "Username", "First name", "Last name", "Email", "Membership enabled"]]


    def summary(self):
        """Prints a summary of the key metrics."""
        print(f"Excel File: {self.file_path}")
        print(f"Number of records: {self.num_records}")
        print(f"Number of unique User IDs: {self.num_unique_user_ids}")
        print(f"Number of unique, non-blank emails: {self.num_unique_nonblank_emails}")
        print(f"Number of unique, non-blank Usernames: {self.num_unique_nonblank_usernames}")
        print(f"Number of unique, non-blank Member bundle ID or emails: {self.num_unique_nonblank_member_bundles}")

