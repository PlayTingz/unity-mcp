extends CanvasLayer

# UI overlay for runner game
var score_label: Label
var coins_label: Label
var game_manager = null

func _ready():
	# Create UI labels
	score_label = Label.new()
	score_label.position = Vector2(20, 20)
	score_label.add_theme_font_size_override("font_size", 32)
	add_child(score_label)
	
	coins_label = Label.new()
	coins_label.position = Vector2(20, 60)
	coins_label.add_theme_font_size_override("font_size", 32)
	add_child(coins_label)
	
	# Find game manager
	game_manager = get_node_or_null("/root/RunnerGame")
	
	print("UI ready")

func _process(_delta: float):
	if game_manager:
		score_label.text = "Score: %d" % int(game_manager.score)
		coins_label.text = "Coins: %d" % game_manager.coins_collected
		
		# Show multiplier if active
		if game_manager.score_multiplier_value > 1:
			coins_label.text += " x%d" % game_manager.score_multiplier_value
