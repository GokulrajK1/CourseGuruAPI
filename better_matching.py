from database import ProfessorsDB
import webbrowser
import pandas as pd
from utils import print_separator, print_separators_bounded, get_integer_input
import asyncio
import aiohttp
from rmp_queries import RMPQuery

def match_csp_and_rmp_manually(start_index : int = 1, missing_rmp_prof_ids_file_path : str = "missing_rmp_prof_ids.txt"):
    csp_df = ProfessorsDB.get_data_table_as_df(ProfessorsDB.CSP_DATA_TABLE_NAME)
    rmp_df = ProfessorsDB.get_data_table_as_df(ProfessorsDB.PROFESSOR_TABLE_NAME)
    filtered_csp_df = csp_df[csp_df["first_name"].isna() & csp_df["id"].isna() & ~csp_df["already_matched"]].reset_index(drop=True)
    run_manual_matching(filtered_csp_df, csp_df, rmp_df, start_index, missing_rmp_prof_ids_file_path)
    filtered_csp_df = csp_df[~csp_df["first_name"].isna() & csp_df["id"].isna() & ~csp_df["already_matched"] & ~csp_df["last_name"].isna()].reset_index(drop=True)
    run_manual_matching(filtered_csp_df, csp_df, rmp_df, start_index, missing_rmp_prof_ids_file_path="second_missing_rmp_profs_ids.txt")

def run_manual_matching(filtered_csp_df : pd.DataFrame, csp_df : pd.DataFrame, rmp_df : pd.DataFrame, start_index : int, missing_rmp_prof_ids_file_path : str):
    if start_index < 1: raise ValueError("start_index must be greater than 1")
    
    # if declare_previous_indicies_as_matched:
    #     csp_df["already_matched"] = (~csp_df["id"].isna())
    #     full_mask = csp_df["first_name"].isna() & csp_df["id"].isna()
    #     target_indices = csp_df[full_mask].iloc[:start_index - 1].index
    #     csp_df.loc[target_indices, "already_matched"] = 1

    for _, row in filtered_csp_df.iterrows():
        
        info = f"CSP Professor Data: {row["scraped_name"]} | {row["course_title"]} | {row["course_code"]}"
        print_separators_bounded(string=info)

        matches = get_matches(row, rmp_df)

        if matches.empty:
            print("No Matching RMP Profiles Found!")
            _ = input("Hit Enter To Launch Browser Queries...")
            make_web_searches_for_more_rmp_info(row, csp_df, rmp_df, missing_rmp_prof_ids_file_path)
        else:
            print(f"Matching RMP Profiles\n{matches}")
            print_separator()
            number_of_matches = len(matches)
            acceptable_inputs = list(range(number_of_matches + 1))
            prompt = f"Select the index (1 through {number_of_matches}) of the matching professor or enter '0' launch browser queries or -1 to safely exit!\n"
            selected_index = get_integer_input(prompt, acceptable_inputs)
            if selected_index == 0:
                print("Launching Browser Queries")
                make_web_searches_for_more_rmp_info(row, csp_df, rmp_df, missing_rmp_prof_ids_file_path)
            else:
                selected_id = matches.iloc[selected_index - 1]['id']
                csp_df.loc[csp_df['scraped_name'] == row['scraped_name'], 'id'] = selected_id
                print("Updated!")
                print(csp_df[csp_df["id"] == selected_id])
                print_separator()

        csp_df.loc[csp_df['scraped_name'] == row['scraped_name'], 'already_matched'] = 1
        ProfessorsDB.write_data_table_as_df(ProfessorsDB.CSP_DATA_TABLE_NAME, csp_df)

    with open(missing_rmp_prof_ids_file_path, "r") as file:
        rmp_professor_ids = [line.strip() for line in file.readlines()] # get rid of the \n

    existing_rmp_professor_ids = rmp_df["id"]
    missing_rmp_professor_ids = [id for id in rmp_professor_ids if id not in existing_rmp_professor_ids.values]

    professor_info_df, ratings_info_df = fetch_rmp_professor_data_from_ids(missing_rmp_professor_ids)

    if professor_info_df == None:
        return

    ProfessorsDB.write_data_table_as_df(ProfessorsDB.PROFESSOR_TABLE_NAME, professor_info_df, append=True)
    ProfessorsDB.write_data_table_as_df(ProfessorsDB.RATINGS_TABLE_NAME, ratings_info_df, append=True)

def get_matches(row : pd.Series, rmp_df : pd.DataFrame):
    first_part_of_name, second_part_of_name = "#", "#"
    last_name : str = row["last_name"]
    if "-" in last_name:
        first_part_of_name, _, second_part_of_name = last_name.partition("-")
    elif " " in last_name:
        first_part_of_name, _, second_part_of_name = last_name.partition(" ")
    else:
        first_part_of_name = last_name

    mask = (
        rmp_df["last_name"].fillna("").str.contains(first_part_of_name, case=False) |
        rmp_df["first_name"].fillna("").str.contains(first_part_of_name, case=False) |
        rmp_df["last_name"].fillna("").str.contains(second_part_of_name, case=False) |
        rmp_df["first_name"].fillna("").str.contains(second_part_of_name, case=False)
    )

    matches = rmp_df[mask].copy().reset_index(drop=True)
    matches.index += 1
    matches.drop(columns=["avg_rating","avg_difficulty","would_take_again_percent"], inplace=True)

    return matches

def make_web_searches_for_more_rmp_info(row : pd.Series, csp_df : pd.DataFrame, rmp_df : pd.DataFrame, missing_rmp_prof_ids_file_path : str):
    search_terms = [
        f"{row["scraped_name"]} rate my professor rutgers",
        f"{row["scraped_name"]} rutgers professor",
        f"{row["course_code"]} rutgers",
        f"{row["scraped_name"]} {row["course_code"]} rutgers"
    ]

    for term in search_terms[::-1]:
        query = f"https://www.google.com/search?q={term.replace(' ', '+')}"
        webbrowser.open_new_tab(query)

    found_id = input("RMP ID Found? Just hit enter if not found or enter 'quit' to safey end execution: ").rstrip()
    if found_id == "quit":
        raise ValueError("Intentional Break Out of Execution")
    elif found_id != "":
        csp_df.loc[csp_df['scraped_name'] == row['scraped_name'], 'id'] = found_id
        print("Updated!")
        print(csp_df[csp_df["id"] == found_id])
        count_id = len(rmp_df[rmp_df["id"] == found_id])
        if count_id == 0:
            
            with open(missing_rmp_prof_ids_file_path, "a") as file:
                file.write(f"{found_id}\n")
            print(f"RMP ID was not in the Database added it the '{missing_rmp_prof_ids_file_path}' file")
        elif count_id > 1:
            raise ValueError("Something horrible has happened")
        else:
            print("RMP ID Already Found In Database. CSP and RMP Sucessfully Connected!")
        

    else:
        print("No Update made because no RMP ID was found")

def fetch_rmp_professor_data_from_ids(rmp_professor_ids : list[str]) -> tuple[pd.DataFrame]:

    if rmp_professor_ids == []:
        return None, None

    results = asyncio.run(fetch_async_ratings(rmp_professor_ids))

    professor_data_list = []
    ratings_data_list = []

    for id, result in zip(rmp_professor_ids, results):
        empty_professor_data = {"firstName" : None, "lastName" : None, "id" : id, "department" : None, 
                            "avgRating": None, "avgDifficulty" : None, 
                            "wouldTakeAgainPercent" : None, "ratings" : {}}
        
        professor_data = result.get("data", {}).get("node", empty_professor_data)
        ratings = professor_data.pop("ratings").get("edges", [])
        professor_data_list.append(professor_data)

        if ratings == []:
            continue

        for rating in ratings:
            rating_info = rating.get("node", {})
            rating_info.update({"id" : id})
            ratings_data_list.append(rating_info)

    professor_info_df = pd.DataFrame(professor_data_list)
    professor_info_df = professor_info_df[["firstName", "lastName", "id", "department", "avgRating", "avgDifficulty", "wouldTakeAgainPercent"]]
    professor_info_df.columns = ["first_name", "last_name", "id", "department", "avg_rating", "avg_difficulty", "would_take_again_percent"]

    ratings_info_df = pd.DataFrame(ratings_data_list)
    ratings_info_df = ratings_info_df[["id", "class", "comment", "grade", "attendanceMandatory", "textbookUse", "ratingTags"]]
    ratings_info_df.columns = ["id", "class", "comment", "grade", "attendence_mandatory", "textbook_use", "rating_tags"]

    return professor_info_df, ratings_info_df

def get_rmp_tasks(session : aiohttp.ClientSession, rmp_professor_ids : list[str], number_of_ratings : int = 100):
    tasks = [session.post(RMPQuery.url,  json={"query" : RMPQuery.fetch_all_professor_info_query_with_id, 
            "variables": {"id" : id, "count" : number_of_ratings}}, 
            headers=RMPQuery.headers) for id in rmp_professor_ids]
    return tasks 
    
async def fetch_async_ratings(rmp_professor_ids) -> list:
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = get_rmp_tasks(session, rmp_professor_ids)
        responses = await asyncio.gather(*tasks)
        for response in responses:
            results.append(await response.json())

    return results

if __name__ == "__main__":
    match_csp_and_rmp_manually(start_index=280)
    