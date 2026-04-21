from fastapi import FastAPI
import pandas as pd

app = FastAPI()

CSV_PATH = "tick_trade_mock.csv"

@app.get("/api/footprint/day")
def get_day(code: str, date: str):
    df = pd.read_csv(CSV_PATH)

    df["DealTime"] = pd.to_datetime(
        date + " " + df["DealTime"],
        format="%Y%m%d %H:%M:%S.%f"
    )
    df["minute"] = df["DealTime"].dt.floor("1min")

    minutes = []

    for minute, g in df.groupby("minute"):
        g = g.sort_values("DealTime")

        kline = {
            "open": float(g.iloc[0]["Price"]),
            "high": float(g["Price"].max()),
            "low": float(g["Price"].min()),
            "close": float(g.iloc[-1]["Price"]),
            "volume": int(g["Volume"].sum())
        }

        rows = (
            g.groupby("Price")
            .apply(lambda x: {
                "buy": int(x.loc[x["Side"] == 1, "Volume"].sum()),
                "sell": int(x.loc[x["Side"] == -1, "Volume"].sum())
            })
            .reset_index()
        )

        footprint_rows = []
        minute_delta = 0

        for _, r in rows.iterrows():
            buy = r[0]["buy"]
            sell = r[0]["sell"]
            delta = buy - sell
            minute_delta += delta

            footprint_rows.append({
                "price": float(r["Price"]),
                "buy": buy,
                "sell": sell,
                "delta": delta
            })

        footprint_rows.sort(key=lambda x: -x["price"])

        minutes.append({
            "minute": minute.strftime("%H:%M"),
            "kline": kline,
            "minute_delta": minute_delta,
            "rows": footprint_rows
        })

    return {"minutes": minutes}