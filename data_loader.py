# data_loader.py
import numpy as np
import pandas as pd


class DataLoader:
    REQUIRED_COLUMNS = ("datetime", "price", "quantity")

    def __init__(self, file_path, ticker_symbol=None, max_price_jump_pct=0.25):
        self.file_path = file_path
        self.ticker_symbol = ticker_symbol.upper() if ticker_symbol else None
        self.max_price_jump_pct = max_price_jump_pct

    def _validate_columns(self, df):
        df.columns = [col.strip() for col in df.columns]
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def _normalize_types(self, df):
        df = df.copy()
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")

        if "tickersymbol" in df.columns:
            df["tickersymbol"] = df["tickersymbol"].astype(str).str.strip().str.upper()
            if self.ticker_symbol:
                df = df[df["tickersymbol"] == self.ticker_symbol]

        return df

    def _drop_invalid_rows(self, df):
        before = len(df)
        df = df.dropna(subset=["datetime", "price", "quantity"])
        df = df[np.isfinite(df["price"]) & np.isfinite(df["quantity"])]
        df = df[(df["price"] > 0) & (df["quantity"] > 0)]
        removed = before - len(df)
        if removed:
            print(f"    - Removed invalid rows: {removed:,}")
        return df

    def _aggregate_duplicate_timestamps(self, df):
        duplicate_count = df.duplicated(subset=["datetime"]).sum()
        if duplicate_count == 0:
            return df

        print(f"    - Aggregated duplicate timestamps: {duplicate_count:,}")
        df = df.copy()
        df["_price_x_quantity"] = df["price"] * df["quantity"]

        group_cols = ["datetime"]
        if "tickersymbol" in df.columns:
            group_cols.append("tickersymbol")

        df = (
            df.groupby(group_cols, as_index=False, sort=True)
            .agg({"_price_x_quantity": "sum", "quantity": "sum"})
        )
        df["price"] = df["_price_x_quantity"] / df["quantity"]
        return df.drop(columns=["_price_x_quantity"])

    def _drop_suspicious_price_jumps(self, df):
        if not self.max_price_jump_pct or self.max_price_jump_pct <= 0 or len(df) < 3:
            return df

        price_jump = df["price"].pct_change().abs()
        keep_mask = price_jump.isna() | (price_jump <= self.max_price_jump_pct)
        removed = len(df) - int(keep_mask.sum())
        if removed:
            print(
                f"    - Removed suspicious price jumps "
                f"(>{self.max_price_jump_pct:.0%}): {removed:,}"
            )
        return df[keep_mask]

    def load_and_clean(self):
        print(f"[*] Input Data from: {self.file_path} ...")
        df = pd.read_csv(self.file_path)
        raw_count = len(df)

        self._validate_columns(df)
        df = self._normalize_types(df)
        df = self._drop_invalid_rows(df)
        df = self._aggregate_duplicate_timestamps(df)
        df = df.sort_values(by="datetime", ascending=True).reset_index(drop=True)
        df = self._drop_suspicious_price_jumps(df).reset_index(drop=True)

        if df.empty:
            raise ValueError("No valid market data rows after cleaning.")

        df["Timestamp"] = df["datetime"].astype("datetime64[ns]").astype("int64")

        print(f"[+] Clean data: {len(df):,}/{raw_count:,} ticks ready.")

        prices_np = np.ascontiguousarray(df["price"].to_numpy(), dtype=np.float64)
        volumes_np = np.ascontiguousarray(df["quantity"].to_numpy(), dtype=np.float64)
        timestamps_np = np.ascontiguousarray(df["Timestamp"].to_numpy(), dtype=np.int64)

        return prices_np, volumes_np, timestamps_np
