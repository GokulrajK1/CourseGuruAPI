import sqlite3
import pandas as pd

class ProfessorsDB:
    NAME = "professors.db"
    CSP_DATA_TABLE_NAME = "csp_data"
    PROFESSOR_TABLE_NAME = "rmp_professors"
    RATINGS_TABLE_NAME = "rmp_ratings"

    @staticmethod
    def get_csp_data_table_as_df() -> pd.DataFrame:
        conn = sqlite3.connect(ProfessorsDB.NAME)
        csp_df = pd.read_sql_query(f"SELECT * from {ProfessorsDB.CSP_DATA_TABLE_NAME}", conn)
        conn.close()
        return csp_df
    
    @staticmethod
    def get_rmp_data_table_as_df() -> pd.DataFrame:
        conn = sqlite3.connect(ProfessorsDB.NAME)
        rmp_df = pd.read_sql_query(f"SELECT * from {ProfessorsDB.PROFESSOR_TABLE_NAME}", conn)
        conn.close()
        return rmp_df
    
    @staticmethod
    def write_csp_df_into_csp_data_table(csp_df : pd.DataFrame):
        conn = sqlite3.connect(ProfessorsDB.NAME)
        csp_df.to_sql(f"{ProfessorsDB.CSP_DATA_TABLE_NAME}", conn, index=False, if_exists='replace')
        conn.commit()
        conn.close()
        


