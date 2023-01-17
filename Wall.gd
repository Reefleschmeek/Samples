#Handles generation of obstacle polygons and collision bounds.
class Wall:
	
	var id
	var wall_quality
	var polygon
	var offset
	var theta_b
	var theta_l
	var theta_r
	var radius0
	var radius1
	var collision_left
	var collision_right
	
	#Constructor.
	#id_: Whether the wall should be the "main" or "secondary" color/type.
	#wall_quality_: Graphical quality of the wall.
	#radius0_: Starting inner radius of the wall.
	#radius1_: Starting outer radius of the wall.
	#offset_: Angular location of the left side of the wall.
	#theta_b_: Angle that the bottom of the wall sweeps through.
	#theta_l_: Angle that the left side of the wall's location will change by between the inner and outer radius.
	#theta_r_: Angle that the right side of the wall's location will change by between the inner and outer radius.
	func _init(id_, wall_quality_, radius0_, radius1_, offset_, theta_b_, theta_l_, theta_r_):
		id = id_
		wall_quality = wall_quality_
		polygon = PoolVector2Array()
		radius0 = radius0_
		radius1 = radius1_
		offset = offset_
		theta_b = theta_b_
		theta_l = theta_l_
		theta_r = theta_r_
		collision_left = null
		collision_right = null
	
	#Moves the wall inwards by a distance d.
	func process(d):
		radius0 -= d
		radius1 -= d
		if radius0 < 25:
			if radius1 > 25:
				var proportion = (25 - radius0) / (radius1 - radius0)
				offset += proportion * theta_l
				theta_b += proportion * (theta_r - theta_l)
				theta_l -= proportion * theta_l
				theta_r -= proportion * theta_r
			radius0 = 25
		if radius0 < 100 and radius1 > 100:
			var proportion = (100 - radius0) / (radius1 - radius0)
			collision_left = offset + proportion * theta_l
			collision_right = offset + theta_b + proportion * theta_r
			collision_left = fposmod(collision_left, TAU)
			collision_right = fposmod(collision_right, TAU)
		else:
			collision_left = null
			collision_right = null
		
		process_points()
	
	#Generates a new polygon representing the wall's boundary.
	func process_points():
		polygon = PoolVector2Array()
		
		#Determine the required number of vertices for each side of the wall. n0: bottom, n1: top, nl: left, nr: right.
		var n0 = clamp(int((0.5 + radius0 / 3000) * (theta_b + 0.3) / TAU * wall_quality), 2, INF)
		var n1 = clamp(int((0.5 + radius1 / 3000) * (theta_b - theta_l + theta_r + 0.3) / TAU * wall_quality), 2, INF)
		if radius1 > 1500:
			n1 = 50
		var nr = 0
		var nl = 0
		if theta_l != 0:
			nl = int((0.5 + (radius1 - radius0) / 3000) * (abs(theta_l) + 0.3) / TAU * wall_quality)
		if theta_r != 0:
			nr = int((0.5 + (radius1 - radius0) / 3000) * (abs(theta_r) + 0.3) / TAU * wall_quality)
		
		var increment
		var increment2
		
		#Generate the bottom side of the wall.
		increment = theta_b / (n0 - 1)
		for i in range(n0):
			var theta = offset + increment * i
			polygon.append(radius0 * Vector2.UP.rotated(theta))
		
		#Generate the right side of the wall.
		increment = (radius1 - radius0) / (nr + 1)
		increment2 = theta_r / (nr + 1)
		for i in range(nr):
			var radius = radius0 + increment * (i + 1)
			var theta = offset + theta_b + increment2 * (i + 1)
			polygon.append(radius * Vector2.UP.rotated(theta))
		
		#Generate the top side of the wall.
		increment = (theta_b + theta_r - theta_l) / (n1 - 1)
		for i in range(n1):
			var theta = offset + theta_l + increment * (n1 - i - 1)
			polygon.append(radius1 * Vector2.UP.rotated(theta))
		
		#Generate the left side of the wall.
		increment = (radius1 - radius0) / (nl + 1)
		increment2 = theta_l / (nl + 1)
		for i in range(nl):
			var radius = radius0 + increment * (nl - i)
			var theta = offset + increment2 * (nl - i)
			polygon.append(radius * Vector2.UP.rotated(theta))
