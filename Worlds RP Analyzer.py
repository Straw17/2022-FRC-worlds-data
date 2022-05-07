import requests
import json
import pprint
import matplotlib.pyplot as plt
import numpy as np
import math

pp = pprint.PrettyPrinter()

header = {"X-TBA-Auth-Key": "3wLRTILycDU48itKMw8a5PhZtUwoyQ58a010KTKV8KsWRmmda2fO0BRluI1dboW4"}

def calculateRP(autoReq, autoBonus, cargoReq, hangReq, match):
    cargo = match[1] + (autoBonus if match[0] >= autoReq else 0)
    RP = [(1 if cargo >= cargoReq else 0), (1 if match[2] >= hangReq else 0)]
    return RP

def fetchData(event):
    request = event + "/rankings"
    response = requests.get("https://www.thebluealliance.com/api/v3/"+request, params=header)
    sortData = json.loads(response.text)
    sortData = sortData["rankings"]
    sortOrder = {}
    for i in sortData:
        sortOrder[int(i["team_key"].replace("frc", ""))] = [0] + i["sort_orders"][1:4]
    
    request = event + "/matches/keys"
    response = requests.get("https://www.thebluealliance.com/api/v3/"+request, params=header)
    matchKeys = json.loads(response.text)
    matchKeys = list(filter(lambda x: "qm" in x, matchKeys))
    reference = [int(i.replace("2022" + div + "_qm","")) for i in matchKeys]

    request = event + "/matches"
    response = requests.get("https://www.thebluealliance.com/api/v3/"+request, params=header)
    matchData = json.loads(response.text)
    matchData = list(filter(lambda x: "qm" in x['key'], matchData))
    reference, matchData = (list(t) for t in zip(*sorted(zip(reference, matchData))))

    #matchArray level one: [red data, blue data]
    #matchArray level two: [auto cargo, total cargo, hang points]
    matchArray = [[0,0,0] for i in range(2*len(matchKeys))]
    matchWinners = []
    matchPlayers = [[0,0,0] for i in range(2*len(matchKeys))]

    for i in range(0,len(matchKeys)):
        matchArray[2*i][0] = matchData[i]["score_breakdown"]["red"]["autoCargoTotal"]
        matchArray[2*i][1] = matchData[i]["score_breakdown"]["red"]["matchCargoTotal"]
        matchArray[2*i][2] = matchData[i]["score_breakdown"]["red"]["endgamePoints"]
        matchArray[2*i+1][0] = matchData[i]["score_breakdown"]["blue"]["autoCargoTotal"]
        matchArray[2*i+1][1] = matchData[i]["score_breakdown"]["blue"]["matchCargoTotal"]
        matchArray[2*i+1][2] = matchData[i]["score_breakdown"]["blue"]["endgamePoints"]
        
        if matchData[i]["winning_alliance"] == "red":
            matchWinners.append(2)
            matchWinners.append(0)
        elif matchData[i]["winning_alliance"] == "blue":
            matchWinners.append(0)
            matchWinners.append(2)
        else:
            matchWinners.append(1)
            matchWinners.append(1)

        redTeams = matchData[i]["alliances"]["red"]["team_keys"]
        redTeams = [("frc0" if x in matchData[i]["alliances"]["red"]["dq_team_keys"] else x) for x in redTeams]
        redTeams = [("frc0" if x in matchData[i]["alliances"]["red"]["surrogate_team_keys"] else x) for x in redTeams]
        matchPlayers[2*i] = [int(i.replace("frc", "")) for i in redTeams]
        blueTeams = matchData[i]["alliances"]["blue"]["team_keys"]
        blueTeams = [("frc0" if x in matchData[i]["alliances"]["blue"]["dq_team_keys"] else x) for x in blueTeams]
        blueTeams = [("frc0" if x in matchData[i]["alliances"]["blue"]["surrogate_team_keys"] else x) for x in blueTeams]
        matchPlayers[2*i+1] = [int(i.replace("frc", "")) for i in blueTeams]

    matchRPs = [calculateRP(autoReq, autoBonus, cargoReq, hangReq, matchArray[i]) + [matchWinners[i]] for i in range(len(matchArray))]

    return [matchArray, matchRPs, matchPlayers, sortOrder]

def printRPPercents():
    cargoRPs = 0
    hangRPs = 0
    for match in matchRPs:
        cargoRPs += match[0]
        hangRPs += match[1]

    print("Cargo RP: " + str(cargoRPs / len(matchRPs) * 100) + "%")
    print("Hang RP: " + str(hangRPs / len(matchRPs) * 100) + "%")

def printRanking():
    ranks = list(sortOrder.keys())
    ranks.sort(key=lambda x: sortOrder[x][3], reverse=True)
    ranks.sort(key=lambda x: sortOrder[x][2], reverse=True)
    ranks.sort(key=lambda x: sortOrder[x][1], reverse=True)
    ranks.sort(key=lambda x: sortOrder[x][0], reverse=True)
    
    for i in range(len(ranks)):
        print(ranks[i])
        firstIndent = 1 - math.floor(math.log10(i+1))
        secondIndent = 4 - math.floor(math.log10(ranks[i]))
        #print("#" + str(i+1) + ": " + " "*firstIndent + str(ranks[i]) + " "*secondIndent + str(sortOrder[ranks[i]][0]))

def getRanking():
    for i in range(len(matchRPs)):
        for player in matchPlayers[i]:
            if player == 0:
                continue
            sortOrder[player][0] += sum(matchRPs[i])

def graphRPs():
    x = []
    y = []
    for match in matchArray:
        x.append(match[1] + (autoBonus if match[0] >= autoReq else 0))
        y.append(match[2])

    colors = []
    for i in range(len(x)):
        if x[i] >= cargoReq:
            if y[i] >= hangReq:
                colors.append("green")
            else:
                colors.append("red")
        else:
            if y[i] >= hangReq:
                colors.append("blue")
            else:
                colors.append("black")

    plt.scatter(x, y, s=5, c=colors)
    plt.xlabel("Cargo")
    plt.ylabel("Hang Points")

    plt.show()

###########################################################################

divs = ["carv", "gal", "hop", "new", "roe", "tur"]

autoReq = 5
autoBonus = 2
cargoReq = 20
hangReq = 16

matchArray = []
matchRPs = []
matchPlayers = []

div = "tur"
returned = fetchData("/event/2022" + div)
matchArray += returned[0]
matchRPs += returned[1]
matchPlayers += returned[2]
sortOrder = returned[3]

getRanking()
printRanking()
