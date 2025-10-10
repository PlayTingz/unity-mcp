extends Node

# Singleton instance - accessed via get_node("/root/GameManager")
static var instance: Node = null

# Make GameManager accessible globally
func _enter_tree():
	instance = self

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

# UI references (set these in the scene)
@onready var score_label: Label = null
@onready var coin_label: Label = null
@onready var multiplier_label: Label = null

func _ready():
	if instance == null:
		instance = self
	else:
		queue_free()
		return
	
	world_speed = initial_world_speed
	next_speed_increase_score = speed_increase_milestone
	
	# Find player
	player_transform = get_tree().get_first_node_in_group("player")

func _process(delta: float):
	# Update score based on distance
	score += world_speed * delta * score_multiplier_value
	
	# Check for speed increase
	if score >= next_speed_increase_score:
		world_speed *= speed_multiplier
		next_speed_increase_score += speed_increase_milestone
	
	# Update power-up timers
	if is_magnet_active:
		magnet_timer -= delta
		if magnet_timer <= 0:
			is_magnet_active = false
	
	if score_multiplier_value > 1:
		multiplier_timer -= delta
		if multiplier_timer <= 0:
			score_multiplier_value = 1
	
	# Update UI
	update_ui()

func update_ui():
	if score_label:
		score_label.text = "Score: %d" % int(score)
	if coin_label:
		coin_label.text = "Coins: %d" % coins_collected
	if multiplier_label:
		multiplier_label.visible = score_multiplier_value > 1
		if score_multiplier_value > 1:
			multiplier_label.text = "x%d" % score_multiplier_value

func collect_coin(amount: int = 1):
	coins_collected += amount

func activate_magnet(duration: float):
	is_magnet_active = true
	magnet_timer = duration

func activate_multiplier(multiplier: int, duration: float):
	score_multiplier_value = multiplier
	multiplier_timer = duration

func game_over():
	print("Game Over! Final Score: ", int(score))
	get_tree().paused = true
