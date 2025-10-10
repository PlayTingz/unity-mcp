extends MeshInstance3D

# Simple player that responds to keyboard
@export var lane_distance: float = 4.0
@export var move_speed: float = 10.0

var current_lane: int = 1  # 0=left, 1=center, 2=right
var target_x: float = 0.0

func _ready():
	print("Player ready at lane:", current_lane)
	target_x = (current_lane - 1) * lane_distance

func _process(delta: float):
	# Handle input
	if Input.is_action_just_pressed("move_left") or Input.is_action_just_pressed("ui_left"):
		if current_lane > 0:
			current_lane -= 1
			target_x = (current_lane - 1) * lane_distance
			print("Moving left to lane:", current_lane)
	
	if Input.is_action_just_pressed("move_right") or Input.is_action_just_pressed("ui_right"):
		if current_lane < 2:
			current_lane += 1
			target_x = (current_lane - 1) * lane_distance
			print("Moving right to lane:", current_lane)
	
	# Smoothly move to target position
	position.x = lerp(position.x, target_x, move_speed * delta)
