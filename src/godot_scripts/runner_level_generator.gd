extends Node3D

# Level generator for endless runner
@export var segment_length: float = 20.0
@export var segments_on_screen: int = 5
@export var despawn_distance: float = -30.0

var active_segments: Array = []
var next_spawn_z: float = 0.0
var game_manager = null

func _ready():
	print("Level Generator ready")
	game_manager = get_parent()
	
	# Spawn initial segments
	for i in range(segments_on_screen):
		spawn_segment()

func _process(_delta: float):
	# Move segments backward based on world speed
	if game_manager and game_manager.world_speed > 0:
		for segment in active_segments:
			if is_instance_valid(segment):
				segment.position.z -= game_manager.world_speed * _delta
		
		# Also track how much we've moved for spawn positioning
		next_spawn_z -= game_manager.world_speed * _delta
	
	# Check if we need to despawn old segments and spawn new ones
	if active_segments.size() > 0:
		var first_segment = active_segments[0]
		if is_instance_valid(first_segment) and first_segment.position.z < despawn_distance:
			first_segment.queue_free()
			active_segments.pop_front()
			spawn_segment()

func spawn_segment():
	# Calculate spawn position based on the last segment's current position
	var spawn_z = next_spawn_z
	if active_segments.size() > 0:
		var last_segment = active_segments[active_segments.size() - 1]
		if is_instance_valid(last_segment):
			# Spawn right after the last segment
			spawn_z = last_segment.position.z + segment_length
	
	var segment = create_track_segment()
	segment.position = Vector3(0, 0, spawn_z)
	add_child(segment)
	active_segments.append(segment)
	
	# Update next spawn position
	next_spawn_z = spawn_z + segment_length

func create_track_segment() -> Node3D:
	var segment = Node3D.new()
	segment.name = "TrackSegment"
	
	# Create ground plane
	var ground = MeshInstance3D.new()
	var mesh = BoxMesh.new()
	mesh.size = Vector3(12, 0.2, segment_length)
	ground.mesh = mesh
	
	var material = StandardMaterial3D.new()
	material.albedo_color = Color(0.3, 0.3, 0.3)
	ground.set_surface_override_material(0, material)
	ground.position = Vector3(0, -0.1, segment_length / 2)
	
	segment.add_child(ground)
	
	# Randomly add lane markers
	if randf() > 0.5:
		add_lane_markers(segment)
	
	# Add coins
	if randf() > 0.3:  # 70% chance
		add_coins(segment)
	
	# Add obstacles
	if randf() > 0.6:  # 40% chance
		add_obstacle(segment)
	
	return segment

func add_lane_markers(segment: Node3D):
	# Add visual lane dividers
	for lane in [-4.0, 4.0]:
		var marker = MeshInstance3D.new()
		var mesh = BoxMesh.new()
		mesh.size = Vector3(0.2, 0.1, segment_length)
		marker.mesh = mesh
		
		var material = StandardMaterial3D.new()
		material.albedo_color = Color(1.0, 1.0, 0.0)  # Yellow
		marker.set_surface_override_material(0, material)
		marker.position = Vector3(lane, 0, segment_length / 2)
		
		segment.add_child(marker)

func add_coins(segment: Node3D):
	# Spawn 1-3 coins in random lanes
	var num_coins = randi() % 3 + 1
	for i in range(num_coins):
		var coin = create_coin()
		var lane = randi() % 3  # 0, 1, or 2
		var lane_x = (lane - 1) * 4.0  # -4, 0, or 4
		var z_offset = randf() * segment_length
		coin.position = Vector3(lane_x, 1.5, z_offset)
		segment.add_child(coin)

func create_coin() -> Area3D:
	var coin = Area3D.new()
	
	# Visual mesh
	var mesh_instance = MeshInstance3D.new()
	var cylinder = CylinderMesh.new()
	cylinder.height = 0.2
	cylinder.top_radius = 0.5
	cylinder.bottom_radius = 0.5
	mesh_instance.mesh = cylinder
	
	var material = StandardMaterial3D.new()
	material.albedo_color = Color(1.0, 0.85, 0.0)  # Gold
	material.metallic = 0.8
	material.roughness = 0.2
	mesh_instance.set_surface_override_material(0, material)
	coin.add_child(mesh_instance)
	
	# Collision shape
	var collision = CollisionShape3D.new()
	var shape = CylinderShape3D.new()
	shape.height = 0.2
	shape.radius = 0.5
	collision.shape = shape
	coin.add_child(collision)
	
	# Add coin script
	var coin_script = load("res://scripts/runner_coin.gd")
	if coin_script:
		coin.set_script(coin_script)
	
	return coin

func add_obstacle(segment: Node3D):
	var obstacle = create_obstacle()
	var lane = randi() % 3
	var lane_x = (lane - 1) * 4.0
	obstacle.position = Vector3(lane_x, 0.5, segment_length / 2)
	segment.add_child(obstacle)

func create_obstacle() -> StaticBody3D:
	var obstacle = StaticBody3D.new()
	obstacle.add_to_group("obstacle")
	
	# Visual mesh
	var mesh_instance = MeshInstance3D.new()
	var box = BoxMesh.new()
	box.size = Vector3(1.5, 1.5, 1.5)
	mesh_instance.mesh = box
	
	var material = StandardMaterial3D.new()
	material.albedo_color = Color(0.8, 0.2, 0.2)  # Red
	mesh_instance.set_surface_override_material(0, material)
	obstacle.add_child(mesh_instance)
	
	# Collision shape
	var collision = CollisionShape3D.new()
	var shape = BoxShape3D.new()
	shape.size = Vector3(1.5, 1.5, 1.5)
	collision.shape = shape
	obstacle.add_child(collision)
	
	return obstacle
