import sqlite3
import pandas as pd

class ProfessorsDB:
    NAME = "professors.db"
    CSP_DATA_TABLE_NAME = "csp_data"
    PROFESSOR_TABLE_NAME = "rmp_professors"
    RATINGS_TABLE_NAME = "rmp_ratings"

    @staticmethod
    def get_data_table_as_df(data_table_name : str) -> pd.DataFrame:
        conn = sqlite3.connect(ProfessorsDB.NAME)
        df = pd.read_sql_query(f"SELECT * from {data_table_name}", conn)
        conn.close()
        return df
    
    @staticmethod
    def write_data_table_as_df(data_table_name : str, df : pd.DataFrame, append : bool = False) -> pd.DataFrame:
        if append:
            original_df = ProfessorsDB.get_data_table_as_df(data_table_name)
            df = pd.concat([original_df, df], ignore_index=True)

        conn = sqlite3.connect(ProfessorsDB.NAME)
        df.to_sql(f"{data_table_name}", conn, index=False, if_exists='replace')
        conn.commit()
        conn.close()

        return df 
