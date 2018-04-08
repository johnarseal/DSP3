from flask import Flask,abort,redirect,render_template,request
from flask_redis import FlaskRedis
from datautils import *


REDIS_URL = "redis://localhost:6236/0"

app = Flask(__name__)
app.config["REDIS_URL"] = REDIS_URL
redis_store = FlaskRedis(app)
AllowedExt = set(['bpm','tif','tiff','png', 'jpg', 'jpeg', 'gif'])
MaxAllowedSize = 1e7
@app.route('/photo/<int:id>', methods=['GET'])  
def getPhoto(id):
    logicId = photoId2LogicId(redis_store, id)
    if logicId is None:
        abort(404)
        
    machineId = logicId2BalanceMachineId(redis_store, logicId)
    return redirect(readPhotoURL(logicId, machineId, id))

    
@app.route('/photo/upload/', methods=['GET','POST'])  
def uploadPhoto():
    
    file = request.files["img"]
    if file.filename.split(".")[-1].lower() not in AllowedExt:
        return "upload fail: wrong file name extension"
    
    blob = file.read()
    fileSize = len(blob)
    
    if fileSize > MaxAllowedSize:
        return "upload fail: file exceed 10MB"
    
    logicId = allocateLogicId()
    machineIdArr = logicId2MachineList(redis_store, logicId)
    photoId = uuid.uuid4().hex
    
    result = postStore(logicId, machineIdArr, photoId, blob)
    if result:
        updateLogicSize(redis_store, logicId, fileSize)
        return "upload success!"
    else:
        return "upload fail: unable to post to store server"
    
    
    
    
@app.route('/test/', methods=['GET'])  
def test():
    pass
    
    

@app.route('/photo/index/', methods=['GET'])
def index():
    return render_template('index.html')


if __name__ == '__main__':  
    app.run(host='0.0.0.0', port=5000, debug=True)
    
    
    
    