import chess
import chess.engine
import math
import random
import engine
import json
from scipy.optimize import minimize
import numpy as np

# Path to Stockfish
STOCKFISH_PATH = r"C:\Users\Tarek\Desktop\Personal Projects\Chess AI\Chess-AI\stockfish\stockfish-windows-x86-64-avx2.exe"

def evaluate_with_weights(board, weights):
    """Evaluate board with given weights."""
    old_weights = engine.WEIGHTS.copy()
    engine.WEIGHTS = {k: v for k, v in zip(engine.WEIGHTS.keys(), weights)}
    score = engine.evaluate(board)
    engine.WEIGHTS = old_weights
    return score

def generate_training_data(num_games=10, skill_levels=[7, 10, 13, 16, 19]):
    """Play games against Stockfish at various skill levels and collect positions with outcomes."""
    training_data = []
    stockfish = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    
    games_per_skill = num_games // len(skill_levels)
    
    for skill in skill_levels:
        stockfish.configure({"Skill Level": skill})
        print(f"Playing {games_per_skill} games at skill level {skill}...")
        
        for game in range(games_per_skill):
            board = chess.Board()
            game_positions = []
            while not board.is_game_over():
                game_positions.append((board.fen(), board.turn))
                if board.turn == chess.WHITE:
                    move = engine.choose_move(board, depth=3)
                    if move:
                        board.push(move)
                else:
                    result = stockfish.play(board, chess.engine.Limit(time=0.1))
                    move = result.move
                    if move:
                        board.push(move)

            result = board.result()
            if result == '1-0':
                outcome = 1
            elif result == '0-1':
                outcome = -1
            else:
                outcome = 0

            for fen, turn in game_positions:
                if turn == chess.WHITE:
                    label = outcome
                else:
                    label = -outcome
                training_data.append((fen, label))
        
        print(f"Skill {skill}: Collected {len(training_data)} total positions")
    
    stockfish.quit()
    return training_data

def loss_function(weights, data):
    """Mean squared error."""
    total_loss = 0
    for fen, target in data:
        board = chess.Board(fen)
        pred = evaluate_with_weights(board, weights)
        total_loss += (pred - target * 100) ** 2
    return total_loss / len(data)

def tune_weights(data):
    """Use scipy to minimize loss."""
    initial_weights = list(engine.WEIGHTS.values())
    bounds = [(0, 100) for _ in initial_weights]
    result = minimize(loss_function, initial_weights, args=(data,), bounds=bounds, method='L-BFGS-B')
    tuned = {k: v for k, v in zip(engine.WEIGHTS.keys(), result.x)}
    return tuned

if __name__ == "__main__":
    print("Generating training data from self-play vs Stockfish...")
    data = generate_training_data(50, skill_levels=[7, 10, 13, 16, 19])
    print(f"Collected {len(data)} positions")

    print("Tuning weights...")
    tuned_weights = tune_weights(data)
    print("Tuned weights:", tuned_weights)

    with open('tuned_weights.json', 'w') as f:
        json.dump(tuned_weights, f)
    print("Saved to tuned_weights.json")
