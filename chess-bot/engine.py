import chess
import math

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 320,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# Piece-square tables (for white, from a1 to h8)
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

PIECE_TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
    chess.KING: KING_TABLE,
}

transposition_table = {}

def evaluate(board: chess.Board) -> int:
    """Enhanced evaluation with material and position."""
    if board.is_checkmate():
        return -math.inf if board.turn else math.inf
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    # Material
    for piece_type in PIECE_VALUES:
        score += len(board.pieces(piece_type, chess.WHITE)) * PIECE_VALUES[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * PIECE_VALUES[piece_type]

    # Position
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            table = PIECE_TABLES[piece.piece_type]
            if piece.color == chess.WHITE:
                score += table[square]
            else:
                score -= table[63 - square]  # Flip for black

    # Pawn structure
    for color in [chess.WHITE, chess.BLACK]:
        pawns = board.pieces(chess.PAWN, color)
        for pawn_sq in pawns:
            file = chess.square_file(pawn_sq)
            rank = chess.square_rank(pawn_sq)
            # Isolated pawn
            isolated = True
            for f in [file-1, file+1]:
                if 0 <= f < 8 and any(board.piece_at(chess.square(f, r)) == chess.Piece(chess.PAWN, color) for r in range(8)):
                    isolated = False
                    break
            if isolated:
                score -= 10 if color == chess.WHITE else -10
            # Doubled pawn
            doubled = False
            for r in range(8):
                if r != rank and board.piece_at(chess.square(file, r)) == chess.Piece(chess.PAWN, color):
                    doubled = True
                    break
            if doubled:
                score -= 10 if color == chess.WHITE else -10
            # Passed pawn
            passed = True
            direction = 1 if color == chess.WHITE else -1
            for r in range(rank + direction, 8 if color == chess.WHITE else -1, direction):
                for f in [file-1, file, file+1]:
                    if 0 <= f < 8:
                        piece = board.piece_at(chess.square(f, r))
                        if piece and piece.piece_type == chess.PAWN and piece.color != color:
                            passed = False
                            break
                if not passed:
                    break
            if passed:
                score += 20 if color == chess.WHITE else -20

    # Rooks on open files
    for color in [chess.WHITE, chess.BLACK]:
        rooks = board.pieces(chess.ROOK, color)
        for rook_sq in rooks:
            file = chess.square_file(rook_sq)
            open_file = True
            for r in range(8):
                piece = board.piece_at(chess.square(file, r))
                if piece and piece.piece_type == chess.PAWN:
                    open_file = False
                    break
            if open_file:
                score += 10 if color == chess.WHITE else -10

    # Simple king safety
    for color in [chess.WHITE, chess.BLACK]:
        king_sq = board.king(color)
        if king_sq:
            file = chess.square_file(king_sq)
            open_file = True
            for r in range(8):
                piece = board.piece_at(chess.square(file, r))
                if piece and piece.piece_type == chess.PAWN:
                    open_file = False
                    break
            if open_file:
                score -= 20 if color == chess.WHITE else 20  # Penalty for king on open file

    return score

def quiescence(board: chess.Board, alpha: int, beta: int, depth: int = 0) -> int:
    """Quiescence search for captures."""
    if depth > 5:  # Reduced from 10
        return evaluate(board)
    stand_pat = evaluate(board)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    for move in board.legal_moves:
        if board.is_capture(move):
            board.push(move)
            score = -quiescence(board, -beta, -alpha, depth + 1)
            board.pop()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
    return alpha

def minimax(board: chess.Board, depth: int, alpha: int, beta: int, maximizing: bool):
    key = board.fen()
    if key in transposition_table and transposition_table[key][0] >= depth:
        return transposition_table[key][1], transposition_table[key][2]

    if depth == 0 or board.is_game_over():
        if board.is_game_over():
            score = evaluate(board)
        else:
            score = quiescence(board, alpha, beta)
        transposition_table[key] = (depth, score, None)
        return score, None

    # Null move pruning
    if maximizing and depth > 2 and not board.is_check():
        board.push(chess.Move.null())
        null_score, _ = minimax(board, depth - 3, -beta, -beta + 1, False)
        null_score = -null_score
        board.pop()
        if null_score >= beta:
            transposition_table[key] = (depth, beta, None)
            return beta, None

    best_move = None
    moves = sorted(board.legal_moves, key=lambda m: board.is_capture(m), reverse=True)  # Move ordering
    if maximizing:
        max_eval = -math.inf
        for move in moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        transposition_table[key] = (depth, max_eval, best_move)
        return max_eval, best_move
    else:
        min_eval = math.inf
        for move in moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        transposition_table[key] = (depth, min_eval, best_move)
        return min_eval, best_move

def choose_move(board: chess.Board, depth: int = 4) -> chess.Move:
    """Iterative deepening search."""
    best_move = None
    for d in range(1, depth + 1):
        _, move = minimax(board, d, -math.inf, math.inf, board.turn)
        if move:
            best_move = move
    return best_move
