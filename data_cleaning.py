import pandas as pd

def clean_data(file_path="netflix_titles.csv"):
    """Loads and cleans the Netflix dataset for better recommendations."""
    df = pd.read_csv(file_path)

    # ✅ Fill missing values for string columns
    str_cols = ["title", "listed_in", "description", "director", "cast"]
    for col in str_cols:
        df[col] = df[col].fillna("").str.strip()

    # ✅ Normalize genres (ensure no empty genres)
    df["genre_list"] = df["listed_in"].apply(lambda x: x.split(", ") if x else ["Unknown"])

    # ✅ Extract numeric duration values
    df["duration_minutes"] = pd.to_numeric(df["duration"].str.extract(r"(\d+)")[0], errors="coerce").fillna(0)

    # ✅ Identify TV Shows
    df["is_tv_show"] = df["duration"].str.contains("Season", na=False).astype(int)

    # ✅ Convert date_added to datetime (fix warning)
    df.loc[:, "date_added"] = pd.to_datetime(df["date_added"], errors="coerce").fillna(pd.Timestamp("1900-01-01"))

    # ✅ Preprocess text fields for similarity matching
    df["clean_genre"] = df["listed_in"].str.lower().str.replace(",", " ", regex=True).str.replace("&", "and", regex=True)
    df["clean_description"] = df["description"].str.lower()
    df["clean_director"] = df["director"].str.lower().replace("unknown director", "", regex=True)
    df["clean_cast"] = df["cast"].str.lower().replace("unknown cast", "", regex=True)

    return df
