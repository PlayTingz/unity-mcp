extends Node3D

# Level generator for endless runner

@export var segment_length: float = 20.0
@export var segments_on_screen: int = 5
@export var despawn_distance: float = -30.0

var active_segments: Array = []
var next_spawn_z: float = 50.0
var theme_models: Dictionary = {}

# Track segment scene (will be created dynamically)
var track_segment_scene: PackedScene = null

func _ready():
	# Initialize with starting segments
	for i in range(segments_on_screen):
		spawn_segment()

func _process(_delta: float):
	# Check if we need to spawn new segments
	if active_segments.size() > 0:
		var first_segment = active_segments[0]
		if first_segment and is_instance_valid(first_segment) and first_segment.is_inside_tree():
			if first_segment.global_position.z < despawn_distance:
				# Remove old segment
				first_segment.queue_free()
				active_segments.pop_front()
				# Spawn new segment
				spawn_segment()

func spawn_segment():
	var segment = create_track_segment()
	segment.position = Vector3(0, 0, next_spawn_z)
	add_child(segment)
	active_segments.append(segment)
	next_spawn_z += segment_length

func create_track_segment() -> Node3D:
	var segment = Node3D.new()
	segment.name = "TrackSegment"
	
	# Add EnvironmentMover script to move the segment
	var mover_script = load("res://scripts/environment_mover.gd")
	if mover_script:
		segment.set_script(mover_script)
	
	# Create ground plane
	var ground = create_ground_mesh()
	ground.position = Vector3(0, 0, segment_length / 2)
	segment.add_child(ground)
	
	# Randomly add obstacles
	if randf() > 0.3:  # 70% chance of obstacle
		var obstacle = create_obstacle()
		if obstacle:
			var lane = randi() % 3  # Random lane
			var lane_x = (lane - 1) * 4.0
			obstacle.position = Vector3(lane_x, 0.5, segment_length / 2)
			segment.add_child(obstacle)
	
	# Add coins
	var num_coins = randi() % 3 + 1  # 1-3 coins
	for i in range(num_coins):
		var coin = create_coin()
		var lane = randi() % 3
		var lane_x = (lane - 1) * 4.0
		var z_offset = randf() * segment_length
		coin.position = Vector3(lane_x, 1.0, z_offset)
		segment.add_child(coin)
	
	return segment

func create_ground_mesh() -> MeshInstance3D:
	var mesh_instance = MeshInstance3D.new()
	var box_mesh = BoxMesh.new()
	box_mesh.size = Vector3(15, 0.5, segment_length)
	mesh_instance.mesh = box_mesh
	
	var material = StandardMaterial3D.new()
	material.albedo_color = Color(0.3, 0.3, 0.3)  # Gray road
	mesh_instance.set_surface_override_material(0, material)
	
	return mesh_instance

func create_obstacle() -> Node3D:
	# Try to load City theme obstacle
	var obstacle_path = "/opt/godot-themes/city/models/Prop_OilBerrel_01.fbx"
	var obstacle_scene = load_fbx_as_scene(obstacle_path)
	
	if obstacle_scene:
		var obstacle = obstacle_scene.instantiate()
		obstacle.scale = Vector3(0.8, 0.8, 0.8)
		
		# Add collision
		var static_body = StaticBody3D.new()
		var collision = CollisionShape3D.new()
		var shape = BoxShape3D.new()
		shape.size = Vector3(1, 1, 1)
		collision.shape = shape
		static_body.add_child(collision)
		static_body.add_to_group("obstacle")
		obstacle.add_child(static_body)
		
		return obstacle
	else:
		# Fallback to simple cube
		return create_simple_obstacle()

func create_simple_obstacle() -> MeshInstance3D:
	var mesh_instance = MeshInstance3D.new()
	var box_mesh = BoxMesh.new()
	box_mesh.size = Vector3(1, 1, 1)
	mesh_instance.mesh = box_mesh
	
	var material = StandardMaterial3D.new()
	material.albedo_color = Color(0.8, 0.2, 0.2)  # Red
	mesh_instance.set_surface_override_material(0, material)
	
	# Add collision
	var static_body = StaticBody3D.new()
	var collision = CollisionShape3D.new()
	var shape = BoxShape3D.new()
	shape.size = Vector3(1, 1, 1)
	collision.shape = shape
	static_body.add_child(collision)
	static_body.add_to_group("obstacle")
	mesh_instance.add_child(static_body)
	
	return mesh_instance

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
	material.albedo_color = Color(1.0, 0.8, 0.0)  # Gold
	material.metallic = 0.8
	mesh_instance.set_surface_override_material(0, material)
	coin.add_child(mesh_instance)
	
	# Collision shape
	var collision = CollisionShape3D.new()
	var shape = CylinderShape3D.new()
	shape.height = 0.2
	shape.radius = 0.5
	collision.shape = shape
	coin.add_child(collision)
	
	# Add collectible script
	var collectible_script = load("res://scripts/collectible.gd")
	if collectible_script:
		coin.set_script(collectible_script)
	
	return coin

func load_fbx_as_scene(fbx_path: String) -> PackedScene:
	# Note: FBX files need to be imported by Godot first
	# This is a placeholder for the actual implementation
	if FileAccess.file_exists(fbx_path):
		return load(fbx_path)
	return null
