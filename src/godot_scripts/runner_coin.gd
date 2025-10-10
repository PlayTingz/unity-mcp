extends Area3D

# Collectible coin for runner game
@export var rotation_speed: float = 180.0
@export var magnet_speed: float = 20.0
@export var magnet_distance: float = 10.0

var game_manager = null
var player = null
var is_attracted: bool = false

func _ready():
	# Connect collision signal
	body_entered.connect(_on_body_entered)
	area_entered.connect(_on_area_entered)
	
	# Find game manager and player
	game_manager = get_node_or_null("/root/RunnerGame")
	if game_manager:
		player = game_manager.player_transform

func _process(delta: float):
	# Rotate coin
	rotate_y(deg_to_rad(rotation_speed) * delta)
	
	# Magnet effect
	if player and game_manager:
		if game_manager.is_magnet_active and not is_attracted:
			var distance = global_position.distance_to(player.global_position)
			if distance < magnet_distance:
				is_attracted = true
		
		if is_attracted:
			global_position = global_position.move_toward(player.global_position, magnet_speed * delta)

func _on_body_entered(body: Node3D):
	if body.name == "Player":
		collect()

func _on_area_entered(area: Area3D):
	# In case player becomes an Area3D
	if area.name == "Player":
		collect()

func collect():
	if game_manager:
		game_manager.collect_coin(1)
	queue_free()
