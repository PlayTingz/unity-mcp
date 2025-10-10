extends Area3D

# Player controller for 3-lane runner
@export var lane_distance: float = 4.0
@export var lane_change_speed: float = 15.0
@export var jump_force: float = 15.0
@export var gravity_strength: float = 30.0

var current_lane: int = 1  # 0=left, 1=center, 2=right
var target_x: float = 0.0
var velocity_y: float = 0.0
var is_grounded: bool = true
var is_alive: bool = true

func _ready():
	print("Runner Player ready at lane:", current_lane)
	target_x = (current_lane - 1) * lane_distance
	
	# Connect collision signals
	body_entered.connect(_on_body_entered)
	area_entered.connect(_on_area_entered)

func _process(delta: float):
	if not is_alive:
		return
	
	# Handle input
	if Input.is_action_just_pressed("move_left") or Input.is_action_just_pressed("ui_left"):
		move_lane(false)
	
	if Input.is_action_just_pressed("move_right") or Input.is_action_just_pressed("ui_right"):
		move_lane(true)
	
	if Input.is_action_just_pressed("jump") or Input.is_action_just_pressed("ui_up"):
		if is_grounded:
			jump()
	
	# Apply gravity
	if not is_grounded:
		velocity_y -= gravity_strength * delta
	else:
		velocity_y = 0
	
	# Move horizontally to target lane
	position.x = lerp(position.x, target_x, lane_change_speed * delta)
	
	# Move vertically (jumping)
	position.y += velocity_y * delta
	
	# Simple ground check
	if position.y <= 1.0:
		position.y = 1.0
		is_grounded = true
	else:
		is_grounded = false

func move_lane(going_right: bool):
	if not is_alive:
		return
	
	current_lane += 1 if going_right else -1
	current_lane = clampi(current_lane, 0, 2)
	target_x = (current_lane - 1) * lane_distance
	print("Moving to lane:", current_lane)

func jump():
	velocity_y = jump_force
	is_grounded = false
	print("Jump!")

func die():
	if not is_alive:
		return
	
	is_alive = false
	print("Player died!")
	
	var game_manager = get_node_or_null("/root/RunnerGame")
	if game_manager and game_manager.has_method("game_over"):
		game_manager.game_over()

func _on_body_entered(body: Node3D):
	if body.is_in_group("obstacle"):
		die()

func _on_area_entered(area: Area3D):
	# Coins will handle their own collection
	pass
