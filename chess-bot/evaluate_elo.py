import chess
import chess.engine
from engine import choose_move
import time

# Path to Stockfish executable (download from https://stockfishchess.org/)
STOCKFISH_PATH = r"C:\Users\Tarek\Desktop\Personal Projects\Chess AI\Chess-AI\stockfish\stockfish-windows-x86-64-avx2.exe"

def play_game(white_player, black_player, time_limit=chess.engine.Limit(time=0.1)):
    board = chess.Board()
    moves = []
    while not board.is_game_over():
        if board.turn == chess.WHITE:
            if hasattr(white_player, 'play'):
                result = white_player.play(board, time_limit)
                move = result.move
            else:
                move = white_player(board)
        else:
            if hasattr(black_player, 'play'):
                result = black_player.play(board, time_limit)
                move = result.move
            else:
                move = black_player(board)
        if move:
            board.push(move)
            moves.append(move)
        else:
            break
    return board.result(), moves

def evaluate_elo(num_games=10):
    # Our engine as white
    our_engine = lambda board: choose_move(board, depth=5)

    # Stockfish with time limit to simulate ~1200 ELO (adjust for strength)
    stockfish = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    stockfish.configure({"Skill Level": 5})  # Lower skill for ~1200 ELO

    wins = 0
    losses = 0
    draws = 0

    for i in range(num_games):
        print(f"Playing game {i+1}...")
        # Alternate colors
        if i % 2 == 0:
            # Our engine white
            result, _ = play_game(our_engine, lambda b: stockfish.play(b, chess.engine.Limit(time=0.1)).move)
        else:
            # Our engine black
            result, _ = play_game(lambda b: stockfish.play(b, chess.engine.Limit(time=0.1)).move, our_engine)

        if result == "1-0":
            if i % 2 == 0:
                wins += 1
            else:
                losses += 1
        elif result == "0-1":
            if i % 2 == 0:
                losses += 1
            else:
                wins += 1
        else:
            draws += 1

    stockfish.quit()

    total_games = wins + losses + draws
    win_rate = wins / total_games if total_games > 0 else 0
    # Rough ELO estimation (simplified)
    # Assuming Stockfish at 1000, win rate to ELO difference
    elo_diff = 400 * math.log10(win_rate / (1 - win_rate)) if win_rate > 0 and win_rate < 1 else 0
    estimated_elo = 1000 + elo_diff

    print(f"Results: {wins} wins, {losses} losses, {draws} draws")
    print(f"Win rate: {win_rate:.2f}")
    print(f"Estimated ELO: {estimated_elo:.0f}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--games', type=int, default=10, help='Number of games to play')
    args = parser.parse_args()
    evaluate_elo(args.games)