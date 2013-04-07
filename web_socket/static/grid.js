/*
 * In this part, the grid is created
*/

for (var x = 0; x <= bh; x += square_size_height) {
	var line = new Kinetic.Line({
		points: [ 0, 0, bw, 0 ],
		stroke: 'black',
		strokeWidth: 1
	});
	line.move(0,x);
	layer.add(line);
}

for (var x = 0; x <= bw; x += square_size_width) {
	var line = new Kinetic.Line({
		points: [ 0, 0, 0, bh ],
		stroke: 'black',
		strokeWidth: 1
	});
	line.move(x,0);
	layer.add(line);
}
stage.add(layer);
