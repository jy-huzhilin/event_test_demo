from datetime import datetime
from typing import Dict

import pandas as pd


class event_future_1min_demo:
    """基于分钟线的最小事件驱动 demo。"""

    input_name = "cbond.future_hf_1min"
    output_name = "demo__future_minute_spread__1m"

    def _build_latest_snapshot(self, df: pd.DataFrame, current_time: datetime) -> pd.DataFrame:
        if df.empty:
            raise RuntimeError("cbond.future_hf_1min 输入为空，无法执行 demo")

        required_columns = {"time", "ths_code", "open", "close"}
        missing = required_columns - set(df.columns)
        if missing:
            raise RuntimeError(f"分钟线输入缺少必要字段: {sorted(missing)}")

        working = df.copy()
        working["time"] = pd.to_datetime(working["time"])
        working["open"] = pd.to_numeric(working["open"], errors="coerce")
        working["close"] = pd.to_numeric(working["close"], errors="coerce")
        current_ts = pd.Timestamp(current_time)

        if "create_time" in working.columns:
            working = working.sort_values(by="create_time", ascending=False)
            working = working.drop_duplicates(subset=["time", "ths_code"], keep="first")

        current_df = working[working["time"] == current_ts].copy()
        if current_df.empty:
            raise RuntimeError(f"cbond.future_hf_1min 尚未更新到 {current_ts.strftime('%Y-%m-%d %H:%M:%S')}")
        if current_df[["open", "close"]].isna().any().any():
            raise RuntimeError("cbond.future_hf_1min 的 open/close 含有非数值内容")

        current_df["value"] = current_df["close"] - current_df["open"]
        current_df = current_df.rename(columns={"ths_code": "symbol"})
        current_df["time"] = current_ts.strftime("%Y-%m-%d %H:%M:%S")
        return current_df[["time", "symbol", "value"]].reset_index(drop=True)

    def compute(self, input: Dict[str, pd.DataFrame], current_time: datetime) -> Dict[str, pd.DataFrame]:
        minute_df = input[self.input_name]
        result_df = self._build_latest_snapshot(minute_df, current_time)
        return {self.output_name: result_df}
