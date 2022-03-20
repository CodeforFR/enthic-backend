import dask.dataframe as dd
from dask.distributed import Client

from enthic.config import Config
from enthic.ontology import read_account
from enthic.scraping.database_requests_utils import ENGINE


def fetch_raw_indicators():
    ontology = read_account()

    codes_to_labels = {
        d["label_code"]: d["label"]
        for d in ontology[["label", "label_code"]]
        .drop_duplicates()
        .to_dict(orient="records")
    }

    complete_raw = (
        (
            dd.read_sql_table(
                "bundle", str(ENGINE.url), index_col="siren", bytes_per_chunk="256 MiB"
            )
            .reset_index()
            .assign(
                reference=lambda df: (df["declaration"] + df["siren"] * 1e4).astype(int)
            )
            .merge(
                ontology[["bundle", "accountability", "label_code"]],
                on=["bundle", "accountability"],
            )
            .categorize(columns=["label_code"])
        )
        .pivot_table(
            index="reference",
            columns="label_code",
            values="amount",
            aggfunc="sum",
        )
        .reset_index()
    )

    return complete_raw.rename(
        columns={c: codes_to_labels.get(c, c) for c in complete_raw.columns}
    )


def main():
    df = fetch_raw_indicators()
    print(Config.DATADIR)
    df.to_parquet(Config.DATADIR / "enthic_raw_fields.parquet")

    # Final step of pipeline that transform final dataset into standard parquet file.
    dd.read_parquet(Config.DATADIR / "enthic_raw_fields.parquet").compute().to_parquet(
        Config.DATADIR / "enthic_features.parquet"
    )


if __name__ == "__main__":
    Client()
    main()
