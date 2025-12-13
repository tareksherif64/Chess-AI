import chess
from engine import choose_move

def main():
    board = chess.Board()
    print("You are White. Enter moves in UCI format, e.g. e2e4, g1f3.")
    print(board)

    while not board.is_game_over():
        # Human move
        move_str = input("Your move: ").strip()
        try:
            move = chess.Move.from_uci(move_str)
            if move not in board.legal_moves:
                print("Illegal move, try again.")
                continue
            board.push(move)
        except ValueError:
            print("Invalid format, use e2e4 style.")
            continue

        if board.is_game_over():
            break

        # Bot move
        print("Thinking...")
        bot_move = choose_move(board, depth=3)
        if bot_move is None:
            print("No legal moves for bot.")
            break
        board.push(bot_move)
        print(f"Bot plays: {bot_move.uci()}")
        print(board)

    print("Game over:", board.result())

if __name__ == "__main__":
    main()
