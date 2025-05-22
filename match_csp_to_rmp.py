import sqlite3
import pandas as pd 
from database import Database

""" 
This script will attempt to match the scraped names from CSP to professor profiles on RMP.
This is so that when we get a request from the user with scraped names we will be able to query the RMP data efficiently
This is a semi-automatic system so the first matching attempt is fully automatic while the remaining require human input 

The First Matching Attempt (Perfect Match / Automatic)
1) For each CSP Professor, it will look for a matching first and last name in RMP 
2) If found it will add the RMP id to the corresponding row in CSP so the two are linked 
3) However sometimes a CSP professor can match perfectly to multiple RMP profiles 
4) This will require manual fixing and the script will perform an early return prompting you fix the duplicates
5) Each time this happens in the script will output the offending CSP professor along with all the RMP profiles it matched
6) Now you must go into the professors.db file and by doing additional research online and based on the RMP profiles find
the correct RMP profile that correctly matches 
7) CSP professors will never have the exact same name (hopefully if there are any missing it's cause of middle names)
8) Remove the remaining profesors that don't match the CSP one
9) If you do this correctly there should be no more duplicate and it should print ALL PERFECT MATCHES ARE FINISHED

The Second Matching Attempt (Partial Match / Semi-automatic)
1) For each CSP Professor, it will look for a RMP profile that with matching last name and that hasn't been matched yet
2) If it finds RMP profiles it will list them out along with the information from CSP
3) Now you can enter a number from 1 through however many RMP profiles it matched with
4) Through some research you can find if it matches any of the profiles 
5) Enter the number of the matching profile or -1 if there is no match 
6) The number of remaining professors can be check manually but in theory should have no match 

"""
    
duplicate_flag = False
count = 0 

def match_csp_scraped_names_to_rmp():
    print("\nFinding Perfect Matches...")

    global duplicate_flag

    conn = sqlite3.connect(Database.NAME)
    csp_df = pd.read_sql_query(f"SELECT * from {Database.CSP_DATA_TABLE_NAME}", conn)
    rmp_professors_df = pd.read_sql_query(f"SELECT * from {Database.PROFESSOR_TABLE_NAME}", conn)

    rmp_professors_df['matched'] = False

    number_of_csp_professors = len(csp_df)

    # First check if there are any perfect matches (CSP First and Last Name == RMP First and Last Name)
    csp_df["id"] = csp_df.apply(check_for_perfect_csp_rmp_match, axis=1, args=(rmp_professors_df,))

    matched_ids = csp_df["id"].dropna().unique()
    rmp_professors_df.loc[rmp_professors_df["id"].isin(matched_ids), "matched"] = True

    if duplicate_flag:
        print("There are duplicates check the output of the previous function. Make sure each CSP maps to only one RMP")
        return
    
    print("All Perfect Matches Have Been Made!")

    number_of_perfect_matches = csp_df[~csp_df["id"].isna()].shape[0]

    print(f"Number of Perfect Matches Made: {number_of_perfect_matches}")
    print(f"Number of Remaining CSP Professors: {number_of_csp_professors - number_of_perfect_matches}\n")
    
    # Second check if there are any partial matches (CSP Last Name == RMP Last Name and No CSP First Name)
    csp_df, rmp_professors_df, number_of_parital_matches = check_for_partial_csp_rmp_match(csp_df, rmp_professors_df)

    print(csp_df[csp_df["id"].isna()].shape)
    print(count)


    
    # conn = sqlite3.connect(Database.NAME)
    # csp_df.to_sql(f"{Database.CSP_DATA_TABLE_NAME}", conn, index=False, if_exists='replace')
    # conn.commit()
    # conn.close()

# First Matching Attempt:  
def check_for_perfect_csp_rmp_match(data, rmp_professors_df):
    global duplicate_flag
    
    scraped_name = data["scraped_name"]
    first = data["first_name"]
    last = data["last_name"]

    if not first and not last:
        return None

    name_match = rmp_professors_df[(rmp_professors_df["first_name"] == first) & (rmp_professors_df["last_name"] == last)]
    
    # Duplicate Perfect Matches  
    if len(name_match) not in [0, 1]:
        duplicate_flag = True
        print("Duplicate Match Found! Fix this Disparity")
        print("Name From CSP")
        print(scraped_name)
        print("All the matching names from RMP. Find the right one!")
        print(name_match)

    if not name_match.empty:
        return name_match.iloc[0]["id"]
    
# Second Matching Attempt
def check_for_partial_csp_rmp_match(csp_df, rmp_professors_df):

    remaining_csp_df = csp_df[csp_df['id'].isna() & csp_df['first_name'].isna()]
    count = 0 

    for i, row in remaining_csp_df.iterrows():
        matches = rmp_professors_df[(rmp_professors_df['last_name'] == row['last_name']) & (rmp_professors_df['matched'] == False)].copy()
        matches.index = range(1, len(matches) + 1)
        if matches.empty:
            continue
        print("CSP Professor Data")
        print(f"{row["scraped_name"]} : {row["course_title"]} : {row["course_code"]}\n")
        print("Matching RMP Profiles")
        print(matches)
        print()
        selection = int(input(f"Enter 1 through {len(matches)} to select the matching one and -1 if no match:\n"))

        if selection == -1:
            continue

        selected_id = matches.iloc[selection - 1]['id']
        csp_df.at[i, 'id'] = selected_id
        rmp_professors_df.loc[rmp_professors_df['id'] == selected_id, 'matched'] = True
        count += 1 

    return csp_df, rmp_professors_df, count 








# def check_for_partial_csp_rmp_match(data, rmp_professors_df):
#     global count
#     scraped_name = data["scraped_name"]
#     first = data["first_name"]
#     middle = data["middle_name"]
#     last = data["last_name"]
#     course_title = data["course_title"]
#     course_code = data["course_code"]
#     id = data["id"]

#     if id:
#         return id 
    
#     if first:
#         return 
    
#     name_match = rmp_professors_df[(rmp_professors_df["last_name"] == last) & (rmp_professors_df["matched"] == False)]
    
#     if len(name_match):
#         print(f"{scraped_name} : {course_title} : {course_code}")
#         print(name_match)
#         print()
#         selection = int(input(f"Enter 1 through {len(name_match)} to select the matching one and -1 if no match: "))
#         print()

#         if selection == -1:
#             return 
#         count += 1 
#         return name_match.iloc[selection - 1]["id"]

if __name__ == "__main__":
    match_csp_scraped_names_to_rmp()