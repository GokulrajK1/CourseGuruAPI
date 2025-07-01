from database import ProfessorsDB
import webbrowser
import pandas as pd
from utils import print_separator, print_separators_bounded, get_integer_input

# Add support for adding the rmp ids to a text file for the ones that aren't in rmp db 

def make_web_searches_for_more_rmp_info(row : pd.Series, csp_df : pd.DataFrame, rmp_df : pd.DataFrame):
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
            missing_rmp_prof_ids_file_path = "missing_rmp_prof_ids.txt"
            with open(missing_rmp_prof_ids_file_path, "a") as file:
                file.write(f"{found_id}\n")
            print(f"RMP ID was not in the Database added it the '{missing_rmp_prof_ids_file_path}' file")
        elif count_id > 1:
            raise ValueError("Something horrible has happened")
        else:
            print("RMP ID Already Found In Database. CSP and RMP Sucessfully Connected!")
        

    else:
        print("No Update made because no RMP ID was found")

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
    

def match_professors_with_null_first_name(start_index : int = 1, declare_previous_indicies_as_matched : bool = False):
    if start_index < 1: raise ValueError("start_index must be greater than 1")
    csp_df = ProfessorsDB.get_csp_data_table_as_df()
    rmp_df = ProfessorsDB.get_rmp_data_table_as_df()

    if declare_previous_indicies_as_matched:
        csp_df["already_matched"] = (~csp_df["id"].isna())
        full_mask = csp_df["first_name"].isna() & csp_df["id"].isna()
        target_indices = csp_df[full_mask].iloc[:start_index - 1].index
        csp_df.loc[target_indices, "already_matched"] = 1

    filtered_csp_df = csp_df[csp_df["first_name"].isna() & csp_df["id"].isna() & ~csp_df["already_matched"]].reset_index(drop=True)

    for _, row in filtered_csp_df.iterrows():
        
        info = f"CSP Professor Data: {row["scraped_name"]} | {row["course_title"]} | {row["course_code"]}"
        print_separators_bounded(string=info)

        matches = get_matches(row, rmp_df)

        if matches.empty:
            print("No Matching RMP Profiles Found!")
            _ = input("Hit Enter To Launch Browser Queries...")
            make_web_searches_for_more_rmp_info(row, csp_df, rmp_df)
        else:
            print(f"Matching RMP Profiles\n{matches}")
            print_separator()
            number_of_matches = len(matches)
            acceptable_inputs = list(range(number_of_matches + 1))
            prompt = f"Select the index (1 through {number_of_matches}) of the matching professor or enter '0' launch browser queries or -1 to safely exit!\n"
            selected_index = get_integer_input(prompt, acceptable_inputs)
            if selected_index == 0:
                print("Launching Browser Queries")
                make_web_searches_for_more_rmp_info(row, csp_df, rmp_df)
            else:
                selected_id = matches.iloc[selected_index - 1]['id']
                csp_df.loc[csp_df['scraped_name'] == row['scraped_name'], 'id'] = selected_id
                print("Updated!")
                print(csp_df[csp_df["id"] == selected_id])
                print_separator()

        csp_df.loc[csp_df['scraped_name'] == row['scraped_name'], 'already_matched'] = 1
        ProfessorsDB.write_csp_df_into_csp_data_table(csp_df)

if __name__ == "__main__":
    match_professors_with_null_first_name(start_index=280, declare_previous_indicies_as_matched=False)