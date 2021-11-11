from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room
import json, copy, os

# Setup the webserver
app = Flask(__name__)
app.config["SECRET_KEY"] = "kjdsfkdhsvuven3434"
socketio = SocketIO(app, async_mode='eventlet')

# The values of the game - dictionary of rooms, with dictionary of player values
playerValuesOfRooms = {}
# An mapping between the sids from the socket and the user ids used in the `playerValues` object
sidToUserId = {}
showValues = False

# Get the favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Serve the homepage
@app.route("/")
def homePage():
    return render_template("home.html")

# Serve the specific room page
@app.route("/room/<roomId>")
def roomPage(roomId):
    name = request.args.get("room")

    if (name == None):
        name = ""
    else:
        name = "- " + name

    return render_template("poker.html", title=name)

# Socket connection for adding a player
@socketio.on("addPlayer")
def addPlayer(json, methods=["POST"]):
    id = json["id"]
    roomId = json["roomId"]
    name = json["name"]
    value = ""
    sidToUserId[request.sid] = id
    
    # If the room doesn't exist, create it
    if (not roomId in playerValuesOfRooms):
        playerValuesOfRooms[roomId] = {}
    
    playerValuesOfRooms[roomId][id] = {"name": name, "value": value}
    join_room(roomId)
    postPlayerValues(roomId)

    return "OK"

# Socket connection for adding the values for a player
@socketio.on("addPlayerValues")
def addPlayerValues(json, methods=["POST"]):
    # If showing, don't allow change
    if (showValues):
        return

    id = json["id"]
    roomId = json["roomId"]
    name = json["name"]
    value = json["value"]
    
    # If the room doesn't exist, create it
    if (not roomId in playerValuesOfRooms):
        playerValuesOfRooms[roomId] = {}
    
    playerValuesOfRooms[roomId][id] = {"name": name, "value": value}

    postPlayerValues(roomId)

    return "OK"

# Post the player values to all clients on the socket
def postPlayerValues(roomId):
    # If the room doesn't exist, create it
    if (not roomId in playerValuesOfRooms):
        playerValuesOfRooms[roomId] = {}
    
    playerValues = playerValuesOfRooms[roomId]
    
    outValues = copy.deepcopy(playerValues)
    global showValues

    # Hide values if necessary
    if (not showValues):
        for value in outValues.values():
            value["value"] = "?" if value["value"] != "" else ""

    socketio.emit("playerValues", json.dumps(outValues), to=roomId)

# Set whether the values should be shown, or whether the ? should be shown
@socketio.on("showValues")
def toggleShowValues(json, methods=["POST"]):
    global showValues
    
    roomId = json["roomId"]
    
    # If the room doesn't exist, create it
    if (not roomId in playerValuesOfRooms):
        playerValuesOfRooms[roomId] = {}
    
    # If there are no values, don't toggle
    hasValue = False
    for value in playerValuesOfRooms[roomId].values():
        if (value["value"] != ""):
            hasValue = True
    
    if (hasValue):
        showValues = not showValues
    
    postPlayerValues(roomId)

# Clear all of the values
@socketio.on("clearValues")
def clearValues(json, methods=["POST"]):
    global showValues
    
    roomId = json["roomId"]
    
    # If the room doesn't exist, create it
    if (not roomId in playerValuesOfRooms):
        playerValuesOfRooms[roomId] = {}

    for v in playerValuesOfRooms[roomId].values():
        v["value"] = ""
    
    showValues = False

    postPlayerValues(roomId)
    return "OK"

# Remove a player from the the game state
@socketio.on("removePlayer")
def removePlayer(json, methods=["POST"]):
    removePlayerFromRoom(request.sid)

# Handle a player disconnecting from the server
@socketio.on("disconnect")
def disconnectedPlayer():
    removePlayerFromRoom(request.sid)
    

def removePlayerFromRoom(sid):
# If the sid exists in the sidToUserId mapping, remove the player
    if (sid in sidToUserId):
        id = sidToUserId[sid]
        
        # Find the room id
        for (roomId, values) in playerValuesOfRooms.items():
            if (id in values.keys()):
                break

        if (roomId == None):
            return
            
        playerValuesOfRooms[roomId].pop(id)
        sidToUserId.pop(sid)
        postPlayerValues(roomId)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=80, debug=True, log_output=False)