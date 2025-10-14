extends CanvasLayer

# UI overlay for runner game
var score_label: Label
var coins_label: Label
var game_over_panel: PanelContainer
var game_over_label: Label
var final_score_label: Label
var restart_button: Button
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
	
	# Create game over panel
	create_game_over_panel()
	
	# Find game manager
	game_manager = get_node_or_null("/root/RunnerGame")
	
	print("UI ready")

func create_game_over_panel():
	# Panel container
	game_over_panel = PanelContainer.new()
	game_over_panel.set_anchors_preset(Control.PRESET_CENTER)
	game_over_panel.position = Vector2(-200, -150)
	game_over_panel.size = Vector2(400, 300)
	game_over_panel.visible = false
	add_child(game_over_panel)
	
	# VBox layout
	var vbox = VBoxContainer.new()
	vbox.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	vbox.add_theme_constant_override("separation", 20)
	game_over_panel.add_child(vbox)
	
	# Add spacer
	var spacer1 = Control.new()
	spacer1.custom_minimum_size = Vector2(0, 20)
	vbox.add_child(spacer1)
	
	# Game Over label
	game_over_label = Label.new()
	game_over_label.text = "GAME OVER"
	game_over_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	game_over_label.add_theme_font_size_override("font_size", 48)
	vbox.add_child(game_over_label)
	
	# Final score label
	final_score_label = Label.new()
	final_score_label.text = "Score: 0"
	final_score_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	final_score_label.add_theme_font_size_override("font_size", 32)
	vbox.add_child(final_score_label)
	
	# Add spacer
	var spacer2 = Control.new()
	spacer2.custom_minimum_size = Vector2(0, 20)
	vbox.add_child(spacer2)
	
	# Restart button
	restart_button = Button.new()
	restart_button.text = "Restart Game"
	restart_button.custom_minimum_size = Vector2(200, 50)
	restart_button.add_theme_font_size_override("font_size", 24)
	restart_button.pressed.connect(_on_restart_pressed)
	
	# Center button in HBox
	var hbox = HBoxContainer.new()
	hbox.alignment = BoxContainer.ALIGNMENT_CENTER
	hbox.add_child(restart_button)
	vbox.add_child(hbox)

func _process(_delta: float):
	if game_manager:
		score_label.text = "Score: %d" % int(game_manager.score)
		coins_label.text = "Coins: %d" % game_manager.coins_collected
		
		# Show multiplier if active
		if game_manager.score_multiplier_value > 1:
			coins_label.text += " x%d" % game_manager.score_multiplier_value

func show_game_over(final_score: int, coins: int):
	game_over_panel.visible = true
	final_score_label.text = "Score: %d\nCoins: %d" % [final_score, coins]
	score_label.visible = false
	coins_label.visible = false

func _on_restart_pressed():
	get_tree().reload_current_scene()
