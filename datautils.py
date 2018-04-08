import RedisKey,random, base64, requests, json

MachinePerLogVol = 3
NumLogic = 3
MaxLogicSize = 1e8  # in terms of Bytes
StoreServerURL = ""


"""
translate photo id to logical Id
"""
def photoId2LogicId(redisCon, photoId):
    return redisCon.get(RedisKey.PID2LID(photoId))

"""
translate logical id to machine id
Using ROUND ROBIN to return only 1 machine Id with the lightest balance
"""
def logicId2BalanceMachineId(redisCon, logicId):
    # 3 physical machine per logical volume
    global MachinePerLogVol
    
    # get the list of machines that the logical ID is corresponding to
    machineList = redisCon.lrange(RedisKey.LID2MACSID(logicId),0,machinePerLogVol-1)
    
    # the RRInd is the round robin index to index the item in the list of machine
    RRInd = redisCon.incr(RedisKey.LID2RRID(logicId))
    RRInd = RRInd % machinePerLogVol
    return int(machineList[RRInd])

"""
return a list of machine IDs
"""
def logicId2MachineList(redisCon, logicId):
    # 3 physical machine per logical volume
    global MachinePerLogVol
    
    # get the list of machines that the logical ID is corresponding to
    machineList = redisCon.lrange(RedisKey.LID2MACSID(logicId),0,machinePerLogVol-1)
    
    return machineList

"""
use current time to round robin to know the logical Id
"""
def allocateLogicId(redisCon):
    global NumLogic
    global MaxLogicSize
    
    logicId = int(time.time() * 10) % NumLogic
    curLogSize = int(redisCon.get(RedisKey.LID2SIZE(logicId)))
    found = True
    if curLogSize >= MaxLogicSize:
        # if exceeded the maximum size, use the first available
        rangeList = list(range(NumLogic))
        random.shuffle(rangeList)
        found = False
        for i in rangeList:
            curLogSize = int(redisCon.get(RedisKey.LID2SIZE(i)))
            if curLogSize < MaxLogicSize:
                logicId = i
                found = True
                break
    if found:
        return logicId
    else:
        # @TODO can not find a valid logical ID
        return None

def updateLogicSize(redisCon, logicId, fileSize):
    redisCon.incrby(RedisKey.LID2SIZE(logicId), fileSize)
    
    
def postStore(logicId, machineIdArr, photoId, imageBlob):
    blobEncode = base64.b64encode(imageBlob)
    r = requests.post(StoreServerURL, data = {'logicId':str(logicId),'photoId':photoId,"image":blobEncode})
    try:
        resDict = json.loads(r.json())
        return resDict["status"]
    except:
        return False

"""
construct the URL to redirect the browser to the store machine to read the photo
"""
def readPhotoURL(logId, machineId, photoId):
    return "http://ghc30.ghc.andrew.cmu.edu:1314/" + str(machineId) + "/" + str(logId) + "," + str(photoId)



