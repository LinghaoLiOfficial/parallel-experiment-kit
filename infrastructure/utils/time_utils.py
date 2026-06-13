from datetime import datetime


class TimeParser:
    @classmethod
    def get_current_time(cls):
        return datetime.now()

    @classmethod
    def calculate_duration(cls, total_seconds) -> str:
        days = total_seconds // (24 * 3600)
        hours = (total_seconds % (24 * 3600)) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{days}天{hours}小时{minutes}分{seconds}秒"

    @classmethod
    def calculate_duration_for_seconds(cls, start_time) -> int:
        return int((datetime.now() - start_time).total_seconds())
