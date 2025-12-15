import chess
import chess.engine
import math
import random
import engine
import json
from scipy.optimize import minimize, differential_evolution
import numpy as np
import time

# Path to Stockfish
STOCKFISH_PATH = r"C:\Users\Tarek\Desktop\Personal Projects\Chess AI\Chess-AI\stockfish\stockfish-windows-x86-64-avx2.exe"

# Store original search parameters
ORIGINAL_NULL_MOVE_R = 3
ORIGINAL_RAZOR_MARGIN_MULT = 300
ORIGINAL_FUTILITY_MARGIN_MULT = 150
ORIGINAL_LMR_THRESHOLD = 4
ORIGINAL_LMR_THRESHOLD_DEEP = 8
ORIGINAL_LMR_REDUCTION_1 = 1
ORIGINAL_LMR_REDUCTION_2 = 2
ORIGINAL_ASPIRATION_WINDOW = 50
ORIGINAL_LATE_MOVE_PRUNING_BASE = 3

class EngineOptimizer:
    def __init__(self):
        # Weights (18 parameters)
        self.weight_names = list(engine.WEIGHTS.keys())
        
        # Search parameters (9 parameters)
        self.search_param_names = [
            'null_move_r',           # Null move reduction depth (2-4)
            'razor_margin_mult',     # Razoring margin multiplier (200-400)
            'futility_margin_mult',  # Futility margin multiplier (100-200)
            'lmr_threshold',         # Late move reduction threshold (3-6)
            'lmr_threshold_deep',    # LMR deeper threshold (6-10)
            'lmr_reduction_1',       # LMR first reduction (1-2)
            'lmr_reduction_2',       # LMR second reduction (2-3)
            'aspiration_window',     # Aspiration window size (30-100)
            'late_move_pruning_base' # Late move pruning base (2-5)
        ]
        
        self.all_param_names = self.weight_names + self.search_param_names
        self.num_params = len(self.all_param_names)
        
    def params_to_dict(self, params):
        """Convert parameter array to dictionaries."""
        weights = {name: params[i] for i, name in enumerate(self.weight_names)}
        search_params = {name: params[i + len(self.weight_names)] 
                        for i, name in enumerate(self.search_param_names)}
        return weights, search_params
    
    def dict_to_params(self, weights, search_params):
        """Convert dictionaries to parameter array."""
        params = []
        for name in self.weight_names:
            params.append(weights[name])
        for name in self.search_param_names:
            params.append(search_params[name])
        return np.array(params)
    
    def apply_search_params(self, search_params):
        """Apply search parameters to engine by monkey-patching."""
        # Store as module-level attributes
        engine.NULL_MOVE_R = int(round(search_params['null_move_r']))
        engine.RAZOR_MARGIN_MULT = int(round(search_params['razor_margin_mult']))
        engine.FUTILITY_MARGIN_MULT = int(round(search_params['futility_margin_mult']))
        engine.LMR_THRESHOLD = int(round(search_params['lmr_threshold']))
        engine.LMR_THRESHOLD_DEEP = int(round(search_params['lmr_threshold_deep']))
        engine.LMR_REDUCTION_1 = int(round(search_params['lmr_reduction_1']))
        engine.LMR_REDUCTION_2 = int(round(search_params['lmr_reduction_2']))
        engine.ASPIRATION_WINDOW = int(round(search_params['aspiration_window']))
        engine.LATE_MOVE_PRUNING_BASE = int(round(search_params['late_move_pruning_base']))
    
    def get_bounds(self):
        """Get parameter bounds for optimization."""
        bounds = []
        
        # Weight bounds (0-150)
        for _ in self.weight_names:
            bounds.append((0, 150))
        
        # Search parameter bounds
        bounds.extend([
            (2, 4),      # null_move_r
            (200, 400),  # razor_margin_mult
            (100, 200),  # futility_margin_mult
            (3, 6),      # lmr_threshold
            (6, 10),     # lmr_threshold_deep
            (1, 2),      # lmr_reduction_1
            (2, 3),      # lmr_reduction_2
            (30, 100),   # aspiration_window
            (2, 5)       # late_move_pruning_base
        ])
        
        return bounds
    
    def get_initial_params(self):
        """Get initial parameter values."""
        weights = engine.WEIGHTS.copy()
        search_params = {
            'null_move_r': ORIGINAL_NULL_MOVE_R,
            'razor_margin_mult': ORIGINAL_RAZOR_MARGIN_MULT,
            'futility_margin_mult': ORIGINAL_FUTILITY_MARGIN_MULT,
            'lmr_threshold': ORIGINAL_LMR_THRESHOLD,
            'lmr_threshold_deep': ORIGINAL_LMR_THRESHOLD_DEEP,
            'lmr_reduction_1': ORIGINAL_LMR_REDUCTION_1,
            'lmr_reduction_2': ORIGINAL_LMR_REDUCTION_2,
            'aspiration_window': ORIGINAL_ASPIRATION_WINDOW,
            'late_move_pruning_base': ORIGINAL_LATE_MOVE_PRUNING_BASE,
        }
        return self.dict_to_params(weights, search_params)

def generate_training_data(optimizer, num_games=50, skill_levels=[5, 10, 15, 20]):
    """Play games against Stockfish at various skill levels and collect positions with outcomes."""
    training_data = []
    stockfish = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    
    games_per_skill = num_games // len(skill_levels)
    
    wins = 0
    losses = 0
    draws = 0
    
    for skill in skill_levels:
        stockfish.configure({"Skill Level": skill})
        print(f"\nPlaying {games_per_skill} games at skill level {skill}...")
        
        skill_wins = 0
        skill_losses = 0
        skill_draws = 0
        
        for game_num in range(games_per_skill):
            board = chess.Board()
            game_positions = []
            move_count = 0
            
            while not board.is_game_over() and board.fullmove_number < 100:
                game_positions.append((board.fen(), board.turn))
                move_count += 1
                
                # Progress indicator every 10 moves
                if move_count % 20 == 0:
                    print(f"    Game {game_num+1}, move {board.fullmove_number}", end='\r')
                
                if board.turn == chess.WHITE:
                    # Our engine plays as white
                    move = engine.choose_move(board, depth=3)
                    if move:
                        board.push(move)
                else:
                    # Stockfish plays as black
                    result = stockfish.play(board, chess.engine.Limit(time=0.1))
                    move = result.move
                    if move:
                        board.push(move)

            result = board.result()
            if result == '1-0':
                outcome = 1
                wins += 1
                skill_wins += 1
            elif result == '0-1':
                outcome = -1
                losses += 1
                skill_losses += 1
            else:
                outcome = 0
                draws += 1
                skill_draws += 1

            # Collect positions with outcomes
            for fen, turn in game_positions:
                if turn == chess.WHITE:
                    label = outcome
                else:
                    label = -outcome
                training_data.append((fen, label))
            
            # Progress update after each game
            print(f"  Skill {skill}: Game {game_num + 1}/{games_per_skill} done ({board.fullmove_number} moves) - W:{skill_wins} L:{skill_losses} D:{skill_draws}")
        
        print(f"Skill {skill} completed: W:{skill_wins} L:{skill_losses} D:{skill_draws}")
    
    stockfish.quit()
    
    print(f"\n=== Overall Stats ===")
    print(f"Total: W:{wins} L:{losses} D:{draws}")
    print(f"Win Rate: {wins/(wins+losses+draws)*100:.1f}%")
    print(f"Collected {len(training_data)} positions")
    
    return training_data

def loss_function(params, data, optimizer):
    """Mean squared error loss function."""
    weights, search_params = optimizer.params_to_dict(params)
    
    # Apply parameters
    old_weights = engine.WEIGHTS.copy()
    engine.WEIGHTS = weights
    optimizer.apply_search_params(search_params)
    
    total_loss = 0
    sample_size = min(3000, len(data))  # Sample for faster evaluation
    sampled_data = random.sample(data, sample_size)
    
    for fen, target in sampled_data:
        try:
            board = chess.Board(fen)
            pred = engine.evaluate(board, [])
            # Scale target to centipawns
            total_loss += (pred - target * 100) ** 2
        except:
            continue
    
    # Restore
    engine.WEIGHTS = old_weights
    
    return total_loss / sample_size

def tune_parameters(data, optimizer):
    """Use scipy differential evolution to optimize all parameters."""
    print("\n=== Starting Parameter Optimization ===")
    print(f"Optimizing {optimizer.num_params} parameters:")
    print(f"  - {len(optimizer.weight_names)} evaluation weights")
    print(f"  - {len(optimizer.search_param_names)} search parameters")
    
    initial_params = optimizer.get_initial_params()
    bounds = optimizer.get_bounds()
    
    print("\nInitial parameters:")
    weights, search_params = optimizer.params_to_dict(initial_params)
    print("Weights:", {k: f"{v:.1f}" for k, v in weights.items()})
    print("Search:", {k: f"{v:.1f}" for k, v in search_params.items()})
    
    # Calculate initial loss
    initial_loss = loss_function(initial_params, data, optimizer)
    print(f"\nInitial loss: {initial_loss:.2f}")
    
    print("\nRunning differential evolution optimization...")
    print("This may take a while...\n")
    
    # Use differential evolution for global optimization
    result = differential_evolution(
        loss_function,
        bounds,
        args=(data, optimizer),
        strategy='best1bin',
        maxiter=10,  # Reduced for faster training
        popsize=8,
        tol=0.01,
        mutation=(0.5, 1.5),
        recombination=0.7,
        seed=42,
        workers=1,
        updating='deferred',
        polish=True
    )
    
    optimized_weights, optimized_search = optimizer.params_to_dict(result.x)
    
    print("\n=== Optimization Complete ===")
    print(f"Final loss: {result.fun:.2f}")
    print(f"Improvement: {((initial_loss - result.fun) / initial_loss * 100):.1f}%")
    
    print("\nOptimized weights:")
    for k, v in optimized_weights.items():
        print(f"  {k}: {v:.1f}")
    
    print("\nOptimized search parameters:")
    for k, v in optimized_search.items():
        print(f"  {k}: {v:.1f}")
    
    return optimized_weights, optimized_search

def save_optimized_config(weights, search_params):
    """Save optimized configuration."""
    # Save weights
    with open('tuned_weights.json', 'w') as f:
        json.dump(weights, f, indent=2)
    print("\nSaved weights to tuned_weights.json")
    
    # Save search parameters
    with open('tuned_search_params.json', 'w') as f:
        json.dump(search_params, f, indent=2)
    print("Saved search parameters to tuned_search_params.json")
    
    # Generate engine configuration code
    config_code = f"""
# Optimized Search Parameters
# Add these to engine.py after imports:

NULL_MOVE_R = {int(round(search_params['null_move_r']))}
RAZOR_MARGIN_MULT = {int(round(search_params['razor_margin_mult']))}
FUTILITY_MARGIN_MULT = {int(round(search_params['futility_margin_mult']))}
LMR_THRESHOLD = {int(round(search_params['lmr_threshold']))}
LMR_THRESHOLD_DEEP = {int(round(search_params['lmr_threshold_deep']))}
LMR_REDUCTION_1 = {int(round(search_params['lmr_reduction_1']))}
LMR_REDUCTION_2 = {int(round(search_params['lmr_reduction_2']))}
ASPIRATION_WINDOW = {int(round(search_params['aspiration_window']))}
LATE_MOVE_PRUNING_BASE = {int(round(search_params['late_move_pruning_base']))}

# Then update the pvs_search and choose_move functions to use these constants
# Example replacements:
#   depth - 3  ->  depth - NULL_MOVE_R
#   300 * depth  ->  RAZOR_MARGIN_MULT * depth
#   150 * depth  ->  FUTILITY_MARGIN_MULT * depth
#   i >= 4  ->  i >= LMR_THRESHOLD
#   i >= 8  ->  i >= LMR_THRESHOLD_DEEP
#   reduction = 1  ->  reduction = LMR_REDUCTION_1
#   reduction = 2  ->  reduction = LMR_REDUCTION_2
#   prev_score - 50  ->  prev_score - ASPIRATION_WINDOW
#   3 + depth * depth  ->  LATE_MOVE_PRUNING_BASE + depth * depth
"""
    
    with open('engine_config_update.txt', 'w') as f:
        f.write(config_code)
    print("Saved configuration instructions to engine_config_update.txt")

if __name__ == "__main__":
    print("=== COMPREHENSIVE CHESS ENGINE OPTIMIZER ===")
    print("Optimizing evaluation weights AND search parameters")
    print("=" * 50)
    
    start_time = time.time()
    
    # Initialize optimizer
    optimizer = EngineOptimizer()
    
    # Generate training data
    print("\n[1/3] Generating training data from self-play vs Stockfish...")
    # Use skill levels from beginner to advanced
    data = generate_training_data(optimizer, num_games=150, skill_levels=[5, 10, 15, 20])
    
    # Optimize parameters
    print("\n[2/3] Optimizing parameters...")
    optimized_weights, optimized_search = tune_parameters(data, optimizer)
    
    # Save results
    print("\n[3/3] Saving optimized configuration...")
    save_optimized_config(optimized_weights, optimized_search)
    
    elapsed = time.time() - start_time
    print(f"\n=== TRAINING COMPLETE ===")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print("\nNext steps:")
    print("1. Review tuned_weights.json and tuned_search_params.json")
    print("2. Follow instructions in engine_config_update.txt to update engine.py")
    print("3. Test the optimized engine with gui.py or evaluate_elo.py")
