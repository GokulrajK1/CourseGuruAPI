class RMPQuery:
    url = "https://www.ratemyprofessors.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic dGVzdDp0ZXN0",
        "Origin": "https://www.ratemyprofessors.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }   
    fetch_all_professor_info_query_with_id = """
        query TeacherRatingsPageQuery($id: ID!, $count: Int!) {
            node(id: $id) {
                ... on Teacher {
                    firstName
                    lastName
                    department
                    avgRating
                    wouldTakeAgainPercent
                    avgDifficulty
                    id
                    ratings(first: $count) {
                        edges {
                            node {
                                comment
                                textbookUse
                                attendanceMandatory
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