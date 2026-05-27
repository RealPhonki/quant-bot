# standard
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import json

# third party
import yfinance as yf
import pandas_ta as ta
import pandas as pd

# TODO: Implement batch updates
# TODO: Add documentation
# TODO: Remove magic numbers

class StockClient:
    VALID_INDICATORS = ["aberration", "accbands", "ad", "adosc", "adx", "alligator", "alma", "alphatrend", "amat", "ao", "aobv", "apo", "aroon", "atr", "atrts", "bbands", "bias", "bop", "brar", "cci", "cdl_pattern", "cdl_z", "cfo", "cg", "chandelier_exit", "chop", "cksp", "cmf", "cmo", "coppock", "crsi", "cti", "decay", "decreasing", "dema", "dm", "donchian", "dpo", "ebsw", "efi", "ema", "entropy", "eom", "er", "eri", "exhc", "fisher", "fwma", "ha", "hilo", "hl2", "hlc3", "hma", "ht_trendline", "hwc", "hwma", "ichimoku", "increasing", "inertia", "jma", "kama", "kc", "kdj", "kst", "kurtosis", "kvo", "linreg", "log_return", "long_run", "macd", "mad", "mama", "massi", "mcgd", "median", "mfi", "midpoint", "midprice", "mom", "natr", "nvi", "obv", "ohlc4", "pdist", "percent_return", "pgo", "pivots", "ppo", "psar", "psl", "pvi", "pvo", "pvol", "pvr", "pvt", "pwma", "qqe", "qstick", "quantile", "reflex", "rma", "roc", "rsi", "rsx", "rvgi", "rvi", "rwi", "short_run", "sinwma", "skew", "slope", "sma", "smc", "smi", "smma", "squeeze", "squeeze_pro", "ssf", "ssf3", "stc", "stdev", "stoch", "stochf", "stochrsi", "supertrend", "swma", "t3", "tema", "thermo", "tmo", "tos_stdevall", "trendflex", "trima", "trix", "true_range", "tsi", "tsignals", "tsv", "ui", "uo", "variance", "vhf", "vhm", "vidya", "vortex", "vwap", "vwma", "wcp", "willr", "wma", "xsignals", "zigzag", "zlma", "zscore"]

    """ Expected format for update_history.json
    {
        "TICKER": {
            "last_updated": "%Y-%m-%d"
        }
    }
    """

    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents = True, exist_ok = True)

        self.update_history = self.read_update_history()

    def read_update_history(self) -> None:
        path = self.data_dir.joinpath("update_history.json")
        if path.exists():
            with open(path, "r") as file:
                return json.load(file)
        else:
            path.write_text("{}")
            return {}
        
    def write_update_history(self) -> None:
        with open(self.data_dir.joinpath("update_history.json"), "w") as file:
            json.dump(self.update_history, file)

    def fetch(self, ticker: str) -> pd.DataFrame:
        ticker = ticker.upper()
        path = self.data_dir.joinpath(f"{ticker}.csv")

        if path.exists():
            df = self.from_cache(path, ticker)

        else:
            df = self.download(path, ticker)

        df = self.add_indicators(df)
        df = self.clean(df, ticker)

        return df

    def add_indicators(self, dataframe: pd.DataFrame, indicators: list[Dict[str, Any]] = None) -> pd.DataFrame:
        df = dataframe.copy()

        # convert from multi-index (features from newer versionso yfinance)
        df.columns = df.columns.get_level_values(0)

        if indicators is None:
            indicators = [
                dict(name="sma", length=20),
                dict(name="sma", length=50),
                dict(name="sma", length=200),
                dict(name="ema", length=9),
                dict(name="rsi", length=14),
                dict(name="adx", length=14),
                dict(name="stoch", k=14, d=3)
            ]

        for indicator in indicators:
            indicator = indicator.copy()
            name = indicator.pop("name")

            if name not in self.VALID_INDICATORS:
                raise KeyError(f"Illegal indicator '{name}'. Valid indicators are: " + ", ".join(self.VALID_INDICATORS))
            
            getattr(df.ta, name)(**indicator, append=True)
        
        return df

    def clean(self, dataframe: pd.DataFrame, ticker: str) -> pd.DataFrame:
        df = dataframe.copy()
        df = df.apply(pd.to_numeric)
        df.index = pd.to_datetime(df.index)
        df.dropna(inplace = True)

        if len(df) == 0:
            raise ValueError(f"No data remaining after cleaning {ticker}")

        return df
    
    def from_cache(self, path: Path, ticker: str) -> pd.DataFrame:
        df = pd.read_csv(path, index_col = 0, parse_dates = True, header=[0, 1], date_format = "%Y-%m-%d")

        # check if the entry exists
        if ticker not in self.update_history:
            df = self.download(path, ticker)
            return df

        # check if the data needs to be updated
        last_updated = datetime.strptime(self.update_history[ticker]["last_updated"], "%Y-%m-%d")
        if last_updated.date() < datetime.today().date():
            df = self.download(path, ticker)
            return df
        
        print(f"Fetched '{ticker}' from cache")
        return df
    
    def download(self, path: Path, ticker: str) -> pd.DataFrame:
        today = datetime.today().strftime("%Y-%m-%d")
        df = yf.download(ticker, period = "max", end = today)
        df.to_csv(path)

        self.update_history[ticker] = {}
        self.update_history[ticker]["last_updated"] = today
        self.write_update_history()

        print(f"Downloaded '{ticker}'")

        return df