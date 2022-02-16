import pandas as pd

from enthic.config import Config
from enthic.ontology import read_account
from enthic.scraping.database_requests_utils import ENGINE


def fetch_raw_indicators():
    ontology = read_account()

    df = (
        pd.read_sql("SELECT * FROM bundle", ENGINE)
        .merge(
            ontology[["bundle", "accountability", "label"]],
            on=["bundle", "accountability"],
        )
        .pivot_table(
            index=["siren", "declaration", "accountability"],
            columns=["label"],
            values="amount",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )
    return df


def main():
    df = fetch_raw_indicators()
    df.to_parquet(Config.DATADIR / "enthic_features.parquet")


if __name__ == "__main__":
    main()
