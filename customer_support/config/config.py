import os
import shutil
import sqlite3
import pandas as pd
import requests

from keys_secrets.keys import key_tavily, key_openai

class SingletonMeta(type):
    """
    A Singleton metaclass that creates only one instance of the class.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Config(metaclass=SingletonMeta):
    def __init__(self):
        self.backup_file = "travel2.backup.sqlite"
        self.db = self.prepare_sqlite_db()
        self.set_tavily_key("TAVILY_API_KEY")
        self.set_openai_key("OPENAI_API_KEY")


    def get_db(self):
        return self.db
    
    def get_backup_file(self):
        return self.backup_file
        

    def set_tavily_key(self, var: str):
        if not os.environ.get(var):
            os.environ["TAVILY_API_KEY"] = key_tavily

    def set_openai_key(self, var: str):
        if not os.environ.get(var):
            os.environ["OPENAI_API_KEY"] = key_openai


    def prepare_sqlite_db(self):
        db_url = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/travel2.sqlite"
    
        local_file = "travel2.sqlite"
        # The backup lets us restart for each tutorial section
        overwrite = False
        if overwrite or not os.path.exists(local_file):
            response = requests.get(db_url)
            response.raise_for_status()  # Ensure the request was successful
            with open(local_file, "wb") as f:
                f.write(response.content)
            # Backup - we will use this to "reset" our DB in each section
            shutil.copy(local_file, self.backup_file)
        # Convert the flights to present time for our tutorial
        conn = sqlite3.connect(local_file)

        tables = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table';", conn
        ).name.tolist()
        tdf = {}
        for t in tables:
            tdf[t] = pd.read_sql(f"SELECT * from {t}", conn)

        example_time = pd.to_datetime(
            tdf["flights"]["actual_departure"].replace("\\N", pd.NaT)
        ).max()
        current_time = pd.to_datetime("now").tz_localize(example_time.tz)
        time_diff = current_time - example_time

        tdf["bookings"]["book_date"] = (
            pd.to_datetime(tdf["bookings"]["book_date"].replace("\\N", pd.NaT), utc=True)
            + time_diff
        )

        datetime_columns = [
            "scheduled_departure",
            "scheduled_arrival",
            "actual_departure",
            "actual_arrival",
        ]
        for column in datetime_columns:
            tdf["flights"][column] = (
                pd.to_datetime(tdf["flights"][column].replace("\\N", pd.NaT)) + time_diff
            )

        for table_name, df in tdf.items():
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        del df
        del tdf
        conn.commit()
        conn.close()

        return local_file
