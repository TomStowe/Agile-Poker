from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO
import json, copy, os

# Setup the webserver
app = Flask(__name__)
app.config["SECRET_KEY"] = "kjdsfkdhsvuven3434"
socketio = SocketIO(app)

# The values of the game
playerValues = {}
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
def page():
    name = request.args.get("n")

    if (name == None):
        name = ""
    else:
        name = "- " + name

    return render_template("poker.html", title=name)

# Socket connection for adding a player
@socketio.on("addPlayer")
def addPlayer(json, methods=["POST"]):
    id = json["id"]
    name = json["name"]
    value = ""
    sidToUserId[request.sid] = id
    playerValues[id] = {"name": name, "value": value}
    postPlayerValues()

    return "OK"

# Socket connection for adding the values for a player
@socketio.on("addPlayerValues")
def addPlayerValues(json, methods=["POST"]):
    # If showing, don't allow change
    if (showValues):
        return

    id = json["id"]
    name = json["name"]
    value = json["value"]
    playerValues[id] = {"name": name, "value": value}

    postPlayerValues()

    return "OK"

# Post the player values to all clients on the socket
def postPlayerValues():
    outValues = copy.deepcopy(playerValues)
    global showValues

    # Hide values if necessary
    if (not showValues):
        for value in outValues.values():
            value["value"] = "?" if value["value"] != "" else ""

    socketio.emit("playerValues", json.dumps(outValues))

# Set whether the values should be shown, or whether the ? should be shown
@socketio.on("showValues")
def toggleShowValues(methods=["POST"]):
    global showValues
    
    # If there are no values, don't toggle
    hasValue = False
    for value in playerValues.values():
        if (value["value"] != ""):
            hasValue = True
    
    if (hasValue):
        showValues = not showValues
    
    postPlayerValues()

# Clear all of the values
@socketio.on("clearValues")
def clearValues(methods=["POST"]):
    global showValues

    for v in playerValues.values():
        v["value"] = ""
    
    showValues = False

    postPlayerValues()
    return "OK"

# Remove a player from the the game state
@socketio.on("removePlayer")
def removePlayer(json, methods=["POST"]):
    id = json["id"]
    playerValues.pop(id)

    postPlayerValues()
    return "OK"

# Handle a player disconnecting from the server
@socketio.on("disconnect")
def disconnectedPlayer():
    id = sidToUserId[request.sid]
    playerValues.pop(id)
    sidToUserId.pop(request.sid)
    postPlayerValues()

if __name__ == "__main__":
    socketio.run(app, debug=True)