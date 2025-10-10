extends Area3D

# Collectible script for coins/power-ups

@export var rotation_speed: float = 100.0
@export var magnet_speed: float = 20.0
@export var magnet_activation_distance: float = 15.0

var player_transform: Node3D = null
var is_attracted: bool = false
var game_manager = null

func _ready():
	# Connect collision signal
	body_entered.connect(_on_body_entered)
	
	# Find game manager and player
	game_manager = get_node_or_null("/root/RunnerGame")
	if game_manager:
		player_transform = game_manager.player_transform

func _process(delta: float):
	# Rotate the collectible
	rotate_y(deg_to_rad(rotation_speed) * delta)
	
	if not is_inside_tree() or player_transform == null:
		return
	
	# Magnet effect
	if game_manager and not is_attracted and game_manager.is_magnet_active:
		var distance = global_position.distance_to(player_transform.global_position)
		if distance < magnet_activation_distance:
			is_attracted = true
	
	if is_attracted:
		global_position = global_position.move_toward(player_transform.global_position, magnet_speed * delta)

func _on_body_entered(body: Node):
	if body.is_in_group("player"):
		collect()

func collect():
	if game_manager:
		game_manager.collect_coin(1)
	queue_free()
