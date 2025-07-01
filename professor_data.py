import requests
import asyncio
import aiohttp
import pandas as pd
import numpy as np
import sqlite3
from name import Name
from database import ProfessorsDB

"""
This script will fetch and update the database professors.db 
This will fetch all professors from CSP and all the professors from RMP as well as their ratings 
This should be the FIRST script you run to update professor.db 

Instructions BEFORE running:

1) Log into Rutgers Course Scheudle Planner and search for courses of any subject 
2) Use Inspect Element and navigate to the Network tab and find the JSON request
3) Find the JSESSSION_ID and sims-csp values in the headers tab
4) Update CURRENT_JSESSION_ID and CURRENT_SIMS_CSP with the new values  
5) Update SEMESTER to the previous semester DO NOT use the current one as it may be missing professors 
"""

CURRENT_JSESSION_ID = "9D27C3C1D7E085485B8E8A615C369296.jvm1-tc8"
CURRENT_SIMS_CSP = "1173101996.20480.0000"

SEMESTER = "12025"
COOKIES = {"JSESSIONID" : CURRENT_JSESSION_ID, "sims-csp": CURRENT_SIMS_CSP}

def fetch_scraped_csp_data():

    course_sections = fetch_course_sections()
    names_data = []

    for courseOfferings in course_sections:
        courses = courseOfferings["courseOfferings"]

        for course in courses:
            sections = course.get("sections")
            parse_csp_data_from_sections(sections, names_data, course)

    insert_csp_data_to_db(names_data)
    remove_duplicates_in_csp_db()

    print("Finished Fetching CSP Data!")

def remove_duplicates_in_csp_db():
    conn = sqlite3.connect(ProfessorsDB.NAME)
    df = pd.read_sql_query(f"SELECT * FROM {ProfessorsDB.CSP_DATA_TABLE_NAME}", conn)
    df_deduped = df.drop_duplicates(subset=["scraped_name", "first_name", "middle_name"])
    df_deduped.reset_index(drop=True, inplace=True)
    df_deduped.to_sql(ProfessorsDB.CSP_DATA_TABLE_NAME, conn, if_exists="replace", index=False)
    conn.close() 

def insert_csp_data_to_db(names_data):
    conn = sqlite3.connect(ProfessorsDB.NAME)
    cursor = conn.cursor()

    cursor.execute(f"DROP TABLE IF EXISTS {ProfessorsDB.CSP_DATA_TABLE_NAME}")

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {ProfessorsDB.CSP_DATA_TABLE_NAME} (
            scraped_name TEXT,
            first_name TEXT,
            middle_name TEXT,
            last_name TEXT,
            course_code TEXT,
            course_title TEXT
        )
    ''')

    query = f""" 
        INSERT INTO {ProfessorsDB.CSP_DATA_TABLE_NAME} (
            scraped_name, 
            first_name, 
            middle_name, 
            last_name,
            course_code,
            course_title
        ) VALUES (?, ?, ?, ?, ?, ?)
    """

    cursor.executemany(query, names_data)

    conn.commit()
    conn.close()


def parse_csp_data_from_sections(sections : list, names_data : list, course : dict):
    unit = course.get("offeringUnit", {}).get("code")
    subject = course.get("course", {}).get("subject")
    number = course.get("course", {}).get("number")
    title = course.get("fullTitle", "").strip()
    course_code = f"{unit}:{subject}:{number}"
   
    for section in sections:
        scraped_professor_list = section.get("instructors", []) + [{}]
        for scraped_professor_dict in scraped_professor_list:
            scraped_professor = scraped_professor_dict.get("name")
            if not scraped_professor:
                continue
            name = Name.from_scraped_name(scraped_professor)
            names_components_tuple = name.get_components()
            tuple_to_be_inserted = (scraped_professor, ) + names_components_tuple + (course_code, title)
            names_data.append(tuple_to_be_inserted)


def fetch_course_sections():
    url = f"https://sims.rutgers.edu/csp/getSubjects.json?semester={SEMESTER}&campus=NB&levelOfStudy=U"
    response = requests.post(url, cookies=COOKIES)
    subject_codes = response.json()["subjects"]
    results = asyncio.run(fetch_async_sections(subject_codes))
    return results
    
def get_csp_tasks(session : aiohttp.ClientSession, subject_codes : list):
    url = f"https://sims.rutgers.edu/csp/sectionsLookup.json?semester={SEMESTER}&campus=NB&levelOfStudy=U&subject="
    tasks = []
    for subject_code in subject_codes:
        new_url = url + subject_code["code"]
        tasks.append(session.post(url=new_url, cookies=COOKIES))

    return tasks

async def fetch_async_sections(subject_codes : list):
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = get_csp_tasks(session, subject_codes)
        responses = await asyncio.gather(*tasks)
        for response in responses:
            results.append(await response.json())

    return results

URL = "https://www.ratemyprofessors.com/graphql"

HEADERS = {
        "Content-Type": "application/json",
        "Authorization": "Basic dGVzdDp0ZXN0",
        "Origin": "https://www.ratemyprofessors.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

RUTGERS_SCHOOL_ID = "U2Nob29sLTgyNQ=="

FETCH_ALL_PROFESSORS_INFO_QUERY = """
query SimpleTeacherQuery($query: TeacherSearchQuery!, $cursor: String!) {
    search: newSearch {
        teachers(query: $query, first: 1000, after: $cursor) {
            edges {
                node {
                id
                firstName
                lastName
                department
                avgRating
                wouldTakeAgainPercent
                avgDifficulty
                }
            }
            pageInfo {
                hasNextPage
                endCursor
            }
            resultCount
        }
    }
}"""

RATINGS_QUERY = """
        query TeacherRatingsPageQuery($id: ID!, $count: Int!) {
            node(id: $id) {
                __typename
                ... on Teacher {
                    ratings(first: $count) {
                        edges {
                            node {
                                comment
                                attendanceMandatory
                                grade
                                class
                                textbookUse
                                ratingTags
                            }
                        }
                    }
                }
            }
        }
    """

ID_QUERY =  """
        query NewSearchTeachersQuery($query: TeacherSearchQuery!, $count: Int) {
            newSearch {
                teachers(query: $query, first: $count) {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        }
    """

FULL_QUERY = """
        query TeacherRatingsPageQuery($id: ID!, $count: Int!) {
            node(id: $id) {
                __typename
                ... on Teacher {
                    firstName
                    lastName
                    department
                    courseCodes {
                        courseName
                    }
                    avgRating
                    numRatings
                    wouldTakeAgainPercent
                    avgDifficulty
                    ratings(first: $count) {
                        edges {
                            node {
                                comment
                                date 
                                helpfulRating
                                clarityRating
                                difficultyRating
                                attendanceMandatory
                                wouldTakeAgain
                                grade
                                class
                                ratingTags
                            }
                        }
                    }
                }
            }
        }
    """

def fetch_and_store_rmp_data():
    fetch_all_professors_names_and_ids()
    fetch_all_ratings()
    print("Finished fetching RMP data!")

def fetch_all_professors_names_and_ids() -> pd.DataFrame:
    cursor = ""
    hasNextPage = True
    professor_info_list = []
    while hasNextPage:
        query = FETCH_ALL_PROFESSORS_INFO_QUERY
        variables = {"query": {"text": "", "schoolID": RUTGERS_SCHOOL_ID}, "cursor": cursor}
        response = requests.post(URL, json = {"query" : query, "variables" : variables}, headers=HEADERS)

        if response.status_code != 200:
            return None
        data = response.json()

        professors = data.get("data", {}).get("search", {}).get("teachers", {}).get("edges", [])
        for professor in professors:
            professor_info_list.append(professor.get("node", {}))

        cursor = data.get("data", {}).get("search", {}).get("teachers", {}).get("pageInfo", {}).get("endCursor")
        hasNextPage = data.get("data", {}).get("search", {}).get("teachers", {}).get("pageInfo", {}).get("hasNextPage")

    professor_info_df = pd.DataFrame(professor_info_list)
    professor_info_df = professor_info_df[["firstName", "lastName", "id", "department", "avgRating", "avgDifficulty", "wouldTakeAgainPercent"]]
    professor_info_df.columns = ["first_name", "last_name", "id", "department", "avg_rating", "avg_difficulty", "would_take_again_percent"]
    
    conn = sqlite3.connect(ProfessorsDB.NAME)

    professor_info_df.to_sql(f"{ProfessorsDB.PROFESSOR_TABLE_NAME}", conn, index=False, if_exists='replace')

    conn.commit()

    conn.close()

def fetch_all_ratings():
    conn = sqlite3.connect(ProfessorsDB.NAME)
    professor_df = pd.read_sql_query(f"SELECT * from {ProfessorsDB.PROFESSOR_TABLE_NAME}", conn)

    ids = professor_df["id"].tolist()
    results = asyncio.run(fetch_async_ratings(ids))

    ratings_info_list = []
    for i, result in enumerate(results):
        professor_id = ids[i]
        if result["data"]["node"] == None:
            ratings_info_list.append({
                "id" : professor_id, 
                "class" : None,
                "comment" : None,
                "grade" : None,
                "attendenceMandatory": None,
                "textbookUse" : None,
                "ratingTags" : None})
        else:
            ratings = result.get("data", {}).get("node", {}).get("ratings", {}).get("edges", [])
            for rating in ratings:
                rating_info : dict = rating.get("node", {})
                rating_info.update({"id" : professor_id})
                ratings_info_list.append(rating_info)
    
    ratings_info_df = pd.DataFrame(ratings_info_list)
    ratings_info_df = ratings_info_df[["id", "class", "comment", "grade", "attendenceMandatory", "textbookUse", "ratingTags"]]
    ratings_info_df.columns = ["id", "class", "comment", "grade", "attendence_mandatory", "textbook_use", "rating_tags"]

    ratings_info_df.fillna({"textbook_use" : -1}, inplace=True)
    ratings_info_df["textbook_use"] = ratings_info_df["textbook_use"].apply(lambda x: 0 if x < 3 else 1)
    ratings_info_df.replace("", np.nan, inplace=True)
    ratings_info_df.to_sql(f"{ProfessorsDB.RATINGS_TABLE_NAME}", conn, index=False, if_exists='replace')

    conn.commit()
    conn.close()

def get_rmp_tasks(session : aiohttp.ClientSession, professor_ids):
    NUMBER_OF_RATINGS = 100

    tasks = [session.post(URL,  json={"query" : RATINGS_QUERY, 
            "variables": {"id" : professor_id, "count" : NUMBER_OF_RATINGS}}, 
            headers=HEADERS) for professor_id in professor_ids]
    return tasks 
    
async def fetch_async_ratings(ids):
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = get_rmp_tasks(session, ids)
        responses = await asyncio.gather(*tasks)
        for response in responses:
            results.append(await response.json())

    return results

if __name__ == "__main__":
    fetch_scraped_csp_data()
    fetch_and_store_rmp_data()
