extends Node3D

# Level generator for endless runner
@export var segment_length: float = 20.0
@export var segments_on_screen: int = 5
@export var despawn_distance: float = -30.0

var active_segments: Array = []
var next_spawn_z: float = 0.0
var game_manager = null

var road_model = null
var barrel_model = null
var cone_model = null
var city_props: Array = []
var city_texture = null
var city_material = null

func _ready():
	print("Level Generator ready")
	game_manager = get_parent()
	
	# Try to preload city models
	load_city_models()
	
	# Spawn initial segments
	for i in range(segments_on_screen):
		spawn_segment()

func load_city_models():
	# Try to load FBX models from assets directory
	var road_path = "res://assets/city/Env_Road_Straight_01.fbx"
	var barrel_path = "res://assets/city/Prop_OilBerrel_01.fbx"
	var cone_path = "res://assets/city/Prop_RoadCone_01.fbx"
	
	if ResourceLoader.exists(road_path):
		road_model = load(road_path)
		print("Loaded road model")
	else:
		print("Road model not found at:", road_path)
	
	if ResourceLoader.exists(barrel_path):
		barrel_model = load(barrel_path)
		city_props.append(barrel_model)
		print("Loaded barrel model")
	else:
		print("Barrel model not found at:", barrel_path)
	
	if ResourceLoader.exists(cone_path):
		cone_model = load(cone_path)
		city_props.append(cone_model)
		print("Loaded cone model")
	else:
		print("Cone model not found at:", cone_path)
	
	if city_props.size() == 0:
		print("No city models found, using primitives")
	
	# Load texture and create material
	var texture_path = "res://assets/city/PandaMat.png"
	if ResourceLoader.exists(texture_path):
		city_texture = load(texture_path)
		city_material = StandardMaterial3D.new()
		city_material.albedo_texture = city_texture
		city_material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		print("Loaded PandaMat texture and created material")
	else:
		print("Texture not found at:", texture_path)
		# Create default colorful material
		city_material = StandardMaterial3D.new()
		city_material.albedo_color = Color(0.8, 0.6, 0.4)

func apply_material_to_mesh_instances(node: Node):
	# Recursively apply material to all MeshInstance3D nodes
	if node is MeshInstance3D and city_material:
		for i in range(node.get_surface_override_material_count()):
			node.set_surface_override_material(i, city_material)
	
	for child in node.get_children():
		apply_material_to_mesh_instances(child)

func load_city_road_model():
	return road_model

func load_random_city_prop():
	if city_props.size() > 0:
		return city_props[randi() % city_props.size()]
	return null

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
	
	# Try to load real road model, fallback to primitive
	var road_scene = load_city_road_model()
	if road_scene:
		var road_instance = road_scene.instantiate()
		road_instance.position = Vector3(0, 0, segment_length / 2)
		road_instance.rotation_degrees = Vector3(0, 90, 0)
		road_instance.scale = Vector3(2.0, 1.0, 2.0)
		apply_material_to_mesh_instances(road_instance)
		segment.add_child(road_instance)
	else:
		# Fallback to primitive ground
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
	
	# Try to load random city prop model
	var prop_scene = load_random_city_prop()
	if prop_scene:
		var prop_instance = prop_scene.instantiate()
		prop_instance.scale = Vector3(1.5, 1.5, 1.5)
		apply_material_to_mesh_instances(prop_instance)
		obstacle.add_child(prop_instance)
	else:
		# Fallback to primitive box
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
