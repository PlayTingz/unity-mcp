extends Node3D

# Game Manager for endless runner
static var instance: Node3D = null

# Player reference
var player_transform: Node3D = null

# World speed and progression
@export var initial_world_speed: float = 10.0
@export var speed_increase_milestone: float = 200.0
@export var speed_multiplier: float = 1.1

var world_speed: float = 0.0
var next_speed_increase_score: float = 0.0

# Score tracking
var score: float = 0.0
var coins_collected: int = 0
var score_multiplier_value: int = 1

# Power-up states
var is_magnet_active: bool = false
var magnet_timer: float = 0.0
var multiplier_timer: float = 0.0

func _enter_tree():
	instance = self

func _ready():
	world_speed = initial_world_speed
	next_speed_increase_score = speed_increase_milestone
	
	# Delay player lookup to next frame to ensure scene is fully loaded
	call_deferred("_find_player")

func _find_player():
	# The manager script is attached to the root RunnerGame node
	# Player is a child of the same node
	player_transform = get_node_or_null("Player")
	if player_transform:
		print("GameManager: Player found at:", player_transform.get_path())
	else:
		print("GameManager: Warning - Player not found!")

func _process(delta: float):
	if world_speed <= 0:
		return
	
	# Update score
	score += world_speed * delta * score_multiplier_value
	
	# Check for speed increase
	if score >= next_speed_increase_score:
		world_speed *= speed_multiplier
		next_speed_increase_score += speed_increase_milestone
		print("Speed increased to:", world_speed)
	
	# Update power-up timers
	if is_magnet_active:
		magnet_timer -= delta
		if magnet_timer <= 0:
			is_magnet_active = false
	
	if score_multiplier_value > 1:
		multiplier_timer -= delta
		if multiplier_timer <= 0:
			score_multiplier_value = 1

func collect_coin(amount: int = 1):
	coins_collected += amount * score_multiplier_value
	print("Coins:", coins_collected, " Score:", int(score))

func activate_magnet(duration: float):
	is_magnet_active = true
	magnet_timer = duration
	print("Magnet activated for", duration, "seconds")

func activate_multiplier(multiplier: int, duration: float):
	score_multiplier_value = multiplier
	multiplier_timer = duration
	print("Multiplier activated: x", multiplier)

func game_over():
	print("Game Over! Final Score:", int(score), " Coins:", coins_collected)
	world_speed = 0
