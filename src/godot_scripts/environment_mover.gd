extends Node3D

# This script moves objects backward to simulate forward player movement

func _process(delta: float):
	var game_manager = get_node_or_null("/root/RunnerGame")
	if game_manager == null or game_manager.world_speed <= 0:
		return
	
	# Move the object backward based on world speed
	translate(Vector3.BACK * game_manager.world_speed * delta)
