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
    # Temporarily set WEIGHTS
    old_weights = engine.WEIGHTS.copy()
    engine.WEIGHTS = {k: v for k, v in zip(engine.WEIGHTS.keys(), weights)}
    score = engine.evaluate(board)
    engine.WEIGHTS = old_weights
    return score

def generate_training_data(num_games=10):
    """Play games against Stockfish and collect positions with outcomes."""
    training_data = []
    stockfish = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    stockfish.configure({"Skill Level": 3})

    for game in range(num_games):
        board = chess.Board()
        game_positions = []
        while not board.is_game_over():
            game_positions.append((board.fen(), board.turn))
            if board.turn == chess.WHITE:
                # Bot move
                move = engine.choose_move(board, depth=3)
                if move:
                    board.push(move)
            else:
                # Stockfish move
                result = stockfish.play(board, chess.engine.Limit(time=0.1))
                move = result.move
                if move:
                    board.push(move)

        # Determine outcome
        result = board.result()
        if result == '1-0':
            outcome = 1  # Bot won
        elif result == '0-1':
            outcome = -1  # Stockfish won
        else:
            outcome = 0  # Draw

        # Label positions
        for fen, turn in game_positions:
            if turn == chess.WHITE:
                label = outcome  # If bot to move, outcome as is
            else:
                label = -outcome  # If Stockfish to move, invert
            training_data.append((fen, label))

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
    bounds = [(0, 100) for _ in initial_weights]  # Reasonable bounds
    result = minimize(loss_function, initial_weights, args=(data,), bounds=bounds, method='L-BFGS-B')
    tuned = {k: v for k, v in zip(engine.WEIGHTS.keys(), result.x)}
    return tuned

if __name__ == "__main__":
    print("Generating training data...")
    data = generate_training_data(5)
    print(f"Collected {len(data)} positions")

    print("Tuning weights...")
    tuned_weights = tune_weights(data)
    print("Tuned weights:", tuned_weights)

    # Save to file
    with open('tuned_weights.json', 'w') as f:
        json.dump(tuned_weights, f)