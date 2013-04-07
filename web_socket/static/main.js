/*
 * These globals define the grid size
*/
var bw = 1000;
var bh = 600;
var square_size_width = bw/60;
var square_size_height = bh/30;

/*
 * for each user a new colored box is displayed on the grid.
 * to keep tracking of new/old users, this boxMap will be used
*/
var boxMap = new Array();

/*
 * basically, this will represent the grid and the colored
 * boxes of each individual user.
*/
var stage = new Kinetic.Stage({
	container: 'map_container',
	width: bw,
	height: bh
});

var layer = new Kinetic.Layer();

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};
/*
 * the updater handles websocket requests and sends new position information
 * to the server
*/
    updater.start();
});

/* this method generates the message and sends it to the server
*/
function newMessage(x, y) {
	msg = {
		x: x,
		y: y
	};
    updater.socket.send(JSON.stringify(msg));
}

/*
 * in order to have a snappy behaviour of the colored boxes,
 * this method corrects the positions to fit into a grid cell
*/
function snapToGrid(obj) {
	var point = obj.getPosition();
	var newX = Math.round(point.x/square_size_width)*square_size_width;
	var newY = Math.round(point.y/square_size_height)*square_size_height;
	obj.setPosition(newX, newY);
}

/*
 * after receiving a message from the server this method will be called.
 * the boxMap will be updated in case of an existing user,
 * or a new entry will be created.
 * Boxes are draggable only for the local user.
 * After finishing the drag, hence 'dragend', the callback function to snap
 * the box is called and afterwards the new positions of the box sent to the server.
*/
function updatePlayerBox(user, color, x, y) {
	if(boxMap[user] != null) {
		box = boxMap[user];
		box.setPosition(x,y);
		boxMap[user]=box;
	} else {
		var box = new Kinetic.Rect({
			x: x,
			y: y,
			width: square_size_width,
			height: square_size_height,
			fill:color,
			stroke:'black',
			strokeWidth: 1,
			draggable: true
		});
		if(user_name == user) {
			box.on('dragend', function() {
				snapToGrid(box);
				layer.draw();
				newMessage(box.getPosition().x, box.getPosition().y);
			});
		} else {
			box.setDraggable(false);
		}
		boxMap[user] = box;
		layer.add(box);
	}
		layer.draw();
}

/*
 * this updater handles the correct creation of the websocket (based on browser)
 * and defines the methods, which are used for message receiving
*/
var updater = {
    socket: null,

    start: function() {
        var url = "ws://" + location.host + "/mapsocket";
        if ("WebSocket" in window) {
			updater.socket = new WebSocket(url);
        } else {
            updater.socket = new MozWebSocket(url);
        }
        updater.socket.onmessage = function(event) {
            updater.update(JSON.parse(event.data));
        }
    },

    update: function(msg) {
		var box = updatePlayerBox(msg.user, msg.color, msg.x, msg.y);
    }
};
