import pandas as pd



class Helper:
    def __init__(self) -> None:
        pass

    def get_start_end_date(self, days=156):
        today = pd.Timestamp.today()
        today_str = today.strftime('%Y-%m-%d')
        # 180 ago
        start_date = today - pd.DateOffset(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        return start_date_str, today_str   