extends CharacterBody3D

# Player controller for endless runner game

@export var lane_distance: float = 4.0
@export var jump_force: float = 15.0
@export var gravity: float = 30.0
@export var lane_change_speed: float = 15.0

var current_lane: int = 1  # 0=left, 1=center, 2=right
var is_alive: bool = true

# Input tracking
var swipe_threshold: float = 50.0

func _ready():
	add_to_group("player")

func _physics_process(delta: float):
	if not is_alive:
		return
	
	handle_input()
	
	# Apply gravity
	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		if velocity.y < 0:
			velocity.y = 0
	
	# Lane movement
	var target_x = (current_lane - 1) * lane_distance
	var current_x = position.x
	velocity.x = (target_x - current_x) * lane_change_speed
	
	move_and_slide()

func handle_input():
	# Keyboard controls
	if Input.is_action_just_pressed("ui_left") or Input.is_action_just_pressed("move_left"):
		move_left()
	elif Input.is_action_just_pressed("ui_right") or Input.is_action_just_pressed("move_right"):
		move_right()
	
	if Input.is_action_just_pressed("ui_up") or Input.is_action_just_pressed("jump"):
		if is_on_floor():
			velocity.y = jump_force

func move_left():
	if current_lane > 0:
		current_lane -= 1

func move_right():
	if current_lane < 2:
		current_lane += 1

func die():
	is_alive = false
	var game_manager = get_node_or_null("/root/RunnerGame")
	if game_manager:
		game_manager.game_over()
