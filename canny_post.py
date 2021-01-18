import  requests, json, csv, sys
from datetime import datetime

#Constants
#The API retuns the list of votes/Posts in a paginated form, so by default it returns 10 objects if we dont add any 'limit' parameter
COUNT_LIMIT = 10
OUTPUT_FILE_NAME    =   'canny.csv'
# HEADER KEYS
HEADER_KEY_BOARD_NAME   =   "BOARD_NAME"
HEADER_KEY_POST_NAME    =   "POST_NAME"
HEADER_KEY_VOTER_EMAIL  =   "VOTER_EMAIL"
HEADER_KEY_VOTER_NAME   =   "VOTER_NAME"
HEADER_KEY_VOTE_DATE    =   "VOTE_DATE"
HEADER_KEY_BY           =   "BY_INFO"

HEADER_CSV_KEYS_ORDER = [HEADER_KEY_BOARD_NAME,
                    HEADER_KEY_POST_NAME,
                    HEADER_KEY_VOTER_EMAIL,
                    HEADER_KEY_VOTER_NAME,
                    HEADER_KEY_VOTE_DATE,
                    HEADER_KEY_BY]

#EndPoints
baseURL = 'https://canny.io/api/v1/'
postEndPoint = 'posts/list'
voteEndPoint = 'votes/list'
fetchboardEndPoint = 'boards/retrieve'
listboardEndpoint = 'boards/list'
apiKey = ''

# URL Utility functions
def getVotesURL():
    return baseURL + voteEndPoint


def getPostURL():
    return baseURL + postEndPoint


def getBoardFetchURL():
    return baseURL + fetchboardEndPoint

def getBoardListURL():
    return baseURL + listboardEndpoint


# Generic method to fetch data from the API
def getDataFromAPI(url,body,method = "POST"):
    body['apiKey'] = apiKey
    response = requests.request(method,url,data = body)
    return response


def getVotersForPost(postID, limit_count = COUNT_LIMIT):
    body = {'postID':postID, 'limit': limit_count}
    return getDataFromAPI(getVotesURL(), body)


def getAllVotesData(limit_count = COUNT_LIMIT):
    body = {'limit' : limit_count}
    return getDataFromAPI(getVotesURL(),body)


def getAllPostsBoard(limit_count = COUNT_LIMIT, sort = "newest"):
    url = getPostURL()
    bodyDic = {'limit': limit_count, 'sort' : sort}
    return getDataFromAPI(url,bodyDic)


def getAllBoardsData():
    body = {}
    response =  getDataFromAPI(getBoardListURL(),body)
    return json.loads(response.text)


def writeDictionaryToCSV(dict, fileName):
    with open(fileName, mode = 'w',encoding='utf-8') as csv_file:
        fieldNames = HEADER_CSV_KEYS_ORDER
        writer = csv.DictWriter(csv_file, fieldnames = fieldNames)
        writer.writeheader()
        for key in dict.keys():
            # Mapping of (POSTNAME, [VOTES])
            votesArr = dict[key]
            print("writing",votesArr)
            for vote in votesArr:
                writer.writerow(vote)
            

def getCSVMapForVote(vote):
    voterEmail = ''
    if 'email' in vote['voter'].keys():
        voterEmail = vote['voter']['email']

    postName = vote['post'].get('title', '')
    boardName = vote['board'].get('name', '')
    voterName = vote['voter'].get('name', '')
    timestamp = vote.get('created','')
    datetimeObj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
    voteDate = str(datetimeObj.strftime("%d/%m/%Y"))
    byEmail = ''

    if vote['by'] is not None:
        byEmail = vote['by'].get('email', '')

    return  {
                   HEADER_KEY_BOARD_NAME    :  boardName,
                   HEADER_KEY_POST_NAME     :  postName,
                   HEADER_KEY_VOTE_DATE     :  voteDate,
                   HEADER_KEY_VOTER_NAME    :  voterName,
                   HEADER_KEY_VOTER_EMAIL   :  voterEmail,
                   HEADER_KEY_BY            :  byEmail
              }


def fetchBoardVoteMapData():
    boardData = getAllBoardsData()
    print(boardData)
    if boardData is None:
        return

    #Retrieve board lists for getting total Post count
    boards = boardData['boards']
    totalPostCount = 0
    postVoteMap = {}
    for board in boards:
        postCount = board['postCount']
        totalPostCount += postCount

    totalVoteCount = 0
    allPostData = getAllPostsBoard(totalPostCount)

    # Get all Posts data to calculate total Vote count
    if allPostData is not None:
        postData = json.loads(allPostData.text)
        posts = postData['posts']
        for post in posts:
            postName = post['title']
            voteCount = post['score']
            totalVoteCount += voteCount

    # fetch all votes from votes/list API and create a mapping of (Postname: (User_Info_Fields))
    print("Vote count", totalVoteCount)
    if totalVoteCount > 0 :
        allVotesData = getAllVotesData(totalVoteCount)
        if allVotesData is not None:
            votesData = json.loads(allVotesData.text)
            votes = votesData['votes']
            for vote in votes:
                postVoteMap[postName] = postVoteMap.get(postName, []) + [getCSVMapForVote(vote)]
    #Finally write the Dict into a CSV
    print("write",postVoteMap)
    return postVoteMap


def performCSVOperations():
    dateToWrite = fetchBoardVoteMapData()
    writeDictionaryToCSV(dateToWrite,OUTPUT_FILE_NAME)


if __name__ == "__main__":
    #param_boardID = sys.argv[1]
    param_apiKey = sys.argv[1]

    if param_apiKey is None:
        print("Error: Empty API Key")

    else:
        apiKey = param_apiKey
        performCSVOperations()
