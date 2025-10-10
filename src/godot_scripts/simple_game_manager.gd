extends Node3D

# Simple game manager that won't crash
var world_speed: float = 10.0
var score: float = 0.0

func _ready():
	print("Game Manager ready! World speed:", world_speed)

func _process(delta: float):
	# Update score
	score += world_speed * delta
