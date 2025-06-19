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

def match_csp_scraped_names_to_rmp():
    print("\nFinding Perfect Matches...\n")

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

    print("Finding Partial Matches...\n")

    csp_df = csp_df.replace(r'^\s*$', None, regex=True)
    
    # Second check if there are any partial matches (CSP Last Name == RMP Last Name and No CSP First Name)
    csp_df, rmp_professors_df, number_of_partial_matches = check_for_partial_csp_rmp_match(csp_df, rmp_professors_df)

    print(f"Number of Perfect Matches Made: {number_of_perfect_matches}")
    print(f"Number of Partial Matches Made: {number_of_partial_matches}")
    print(f"Number of Remaining CSP Professors: {number_of_csp_professors - number_of_perfect_matches - number_of_partial_matches}")
    print(f"Total Number of Professors {number_of_csp_professors}")
    
    conn = sqlite3.connect(Database.NAME)
    csp_df.to_sql(f"{Database.CSP_DATA_TABLE_NAME}", conn, index=False, if_exists='replace')
    conn.commit()
    conn.close()

# First Matching Attempt:  
def check_for_perfect_csp_rmp_match(data, rmp_professors_df):
    global duplicate_flag
    
    scraped_name = data["scraped_name"]
    first = data["first_name"]
    last = data["last_name"]
    id = data["id"]

    if id:
        return id

    if not first or not last:
        return None

    name_match = rmp_professors_df[(rmp_professors_df["first_name"].str.lower() == first.lower()) & (rmp_professors_df["last_name"].str.lower() == last.lower())]
    
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

    with open("manual_selections.txt", "r") as file:
        selections = file.readlines()

    outfile = open("manual_selections.txt", "a")
    remaining_csp_df = csp_df[csp_df['id'].isna() & csp_df['first_name'].isna()]
    remaining_csp_df_length = len(remaining_csp_df)

    selection_index = 0 
    count = 0 
    remaining_index = 1

    for _, row in remaining_csp_df.iterrows():
        mask = (rmp_professors_df['last_name'].str.lower() == row['last_name'].lower()) & (rmp_professors_df['matched'] == False)
        matches = rmp_professors_df[mask].copy()
        matches.index = range(1, len(matches) + 1)

        if matches.empty:
            remaining_index += 1 
            continue
        
        print(f"{remaining_index}/{remaining_csp_df_length}")
        print(f"CSP Professor Data: {row["scraped_name"]} | {row["course_title"]} | {row["course_code"]}\n")
        print("Matching RMP Profiles\n")
        print(matches, end="\n\n")

        if selection_index < len(selections):
            line = selections[selection_index].strip()
            selection = int(line)
            selection_index += 1
        else:
            selection = int(input(f"Enter 1 through {len(matches)} to select the matching one, -1 if no match, or 0 to quit:\n"))
            if selection == 0:
                print("Break Invoked. All Selections Saved!")
                outfile.close()
                return
            outfile.write(f"{selection}\n")
            outfile.flush() 

        remaining_index += 1 

        if selection == -1:
            print()
            continue
        
        count += 1 
        selected_id = matches.iloc[selection - 1]['id']
        csp_df.at[row.name, 'id'] = selected_id
        rmp_professors_df.loc[rmp_professors_df['id'] == selected_id, 'matched'] = True

        print("\nUpdated!")
        print(csp_df.loc[csp_df["scraped_name"] == row["scraped_name"]], end="\n\n")

    return csp_df, rmp_professors_df, count 
        

if __name__ == "__main__":
    match_csp_scraped_names_to_rmp()

#missing in rmp 
# Shuo-Chieh Huang 