import chess
import math

transposition_table = {}

# Opening book: FEN to UCI move
opening_book = {
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1': 'e2e4',  # 1. e4
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1': 'e7e5',  # 1... e5
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2': 'g1f3',  # 2. Nf3
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2': 'b8c6',  # 2... Nc6
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3': 'f1c4',  # 3. Bc4 (Italian)
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 2 3': 'g8f6',  # 3... Nf6 (Russian)
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3': 'f1b5',  # 3. Bb5 (Spanish)
    # Add more as needed
}

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

# Tunable evaluation weights
WEIGHTS = {
    'bishop_pair': 0,
    'mobility': 0,
    'center_control': 0,
    'development': 0,
    'castling': 0,
    'isolated_pawn': 0,
    'doubled_pawn': 88,
    'passed_pawn': 32,
    'rook_open_file': 0,
    'rook_7th': 0,
    'pawn_shield': 93,
    'king_open_file': 100,
    'tempo': 0,
}

# Load tuned weights if available
try:
    import json
    with open('tuned_weights.json', 'r') as f:
        WEIGHTS = json.load(f)
except FileNotFoundError:
    pass

def evaluate(board: chess.Board) -> int:
    """Enhanced evaluation with material, position, pawn structure, mobility, and more."""
    if board.is_checkmate():
        return -math.inf if board.turn else math.inf
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    score = 0
    
    # (Removed threefold-repetition probing to avoid expensive legal-move generation inside evaluation)

    
    # Material
    for piece_type in PIECE_VALUES:
        score += len(board.pieces(piece_type, chess.WHITE)) * PIECE_VALUES[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * PIECE_VALUES[piece_type]

    # Bishop pair bonus
    white_bishops = len(board.pieces(chess.BISHOP, chess.WHITE))
    black_bishops = len(board.pieces(chess.BISHOP, chess.BLACK))
    if white_bishops >= 2:
        score += WEIGHTS['bishop_pair']
    if black_bishops >= 2:
        score -= WEIGHTS['bishop_pair']

    # Position
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            table = PIECE_TABLES[piece.piece_type]
            if piece.color == chess.WHITE:
                score += table[square]
            else:
                score -= table[63 - square]  # Flip for black

    # Mobility: count legal moves for each side from the same position
    original_turn = board.turn

    board.turn = chess.WHITE
    white_mobility = len(list(board.legal_moves))

    board.turn = chess.BLACK
    black_mobility = len(list(board.legal_moves))

    board.turn = original_turn  # restore

    score += WEIGHTS['mobility'] * (white_mobility - black_mobility)



    # Center control (squares d4, e4, d5, e5)
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    for sq in center_squares:
        piece = board.piece_at(sq)
        if piece:
            if piece.color == chess.WHITE:
                score += WEIGHTS['center_control']
            else:
                score -= WEIGHTS['center_control']

    # Development (knights and bishops out of starting positions)
    for color in [chess.WHITE, chess.BLACK]:
        sign = 1 if color == chess.WHITE else -1
        # Knights
        knights = board.pieces(chess.KNIGHT, color)
        for knight_sq in knights:
            if color == chess.WHITE and knight_sq in [chess.B1, chess.G1]:
                score -= WEIGHTS['development'] * sign
            elif color == chess.BLACK and knight_sq in [chess.B8, chess.G8]:
                score -= WEIGHTS['development'] * sign
        # Bishops
        bishops = board.pieces(chess.BISHOP, color)
        for bishop_sq in bishops:
            if color == chess.WHITE and bishop_sq in [chess.C1, chess.F1]:
                score -= WEIGHTS['development'] * sign
            elif color == chess.BLACK and bishop_sq in [chess.C8, chess.F8]:
                score -= WEIGHTS['development'] * sign

    # Castling bonus
    if board.has_castling_rights(chess.WHITE):
        score += WEIGHTS['castling']
    if board.has_castling_rights(chess.BLACK):
        score -= WEIGHTS['castling']

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
                score -= WEIGHTS['isolated_pawn'] if color == chess.WHITE else -WEIGHTS['isolated_pawn']
            # Doubled pawn
            doubled = False
            for r in range(8):
                if r != rank and board.piece_at(chess.square(file, r)) == chess.Piece(chess.PAWN, color):
                    doubled = True
                    break
            if doubled:
                score -= WEIGHTS['doubled_pawn'] if color == chess.WHITE else -WEIGHTS['doubled_pawn']
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
                score += WEIGHTS['passed_pawn'] if color == chess.WHITE else -WEIGHTS['passed_pawn']

    # Rooks on open files and 7th rank
    for color in [chess.WHITE, chess.BLACK]:
        rooks = board.pieces(chess.ROOK, color)
        for rook_sq in rooks:
            file = chess.square_file(rook_sq)
            rank = chess.square_rank(rook_sq)
            open_file = True
            for r in range(8):
                piece = board.piece_at(chess.square(file, r))
                if piece and piece.piece_type == chess.PAWN:
                    open_file = False
                    break
            if open_file:
                score += WEIGHTS['rook_open_file'] if color == chess.WHITE else -WEIGHTS['rook_open_file']
            # Rook on 7th rank
            if (color == chess.WHITE and rank == 6) or (color == chess.BLACK and rank == 1):
                score += WEIGHTS['rook_7th'] if color == chess.WHITE else -WEIGHTS['rook_7th']

    # King safety
    for color in [chess.WHITE, chess.BLACK]:
        king_sq = board.king(color)
        if not king_sq:
            continue

        file = chess.square_file(king_sq)
        rank = chess.square_rank(king_sq)
        sign = 1 if color == chess.WHITE else -1

        # Pawn shield (only add squares that are actually on board)
        shield_squares = []
        if color == chess.WHITE and rank >= 1:
            for f in (file - 1, file, file + 1):
                if 0 <= f < 8:
                    shield_squares.append(chess.square(f, rank - 1))
        elif color == chess.BLACK and rank <= 6:
            for f in (file - 1, file, file + 1):
                if 0 <= f < 8:
                    shield_squares.append(chess.square(f, rank + 1))

        shield_count = sum(
            1
            for sq in shield_squares
            if board.piece_at(sq) == chess.Piece(chess.PAWN, color)
        )
        score += shield_count * WEIGHTS['pawn_shield'] * sign

        # Open file near king (penalize king on open/semi-open files)
        for f in (file - 1, file, file + 1):
            if not (0 <= f < 8):
                continue
            open_near = True
            for r in range(8):
                piece = board.piece_at(chess.square(f, r))
                if piece and piece.piece_type == chess.PAWN:
                    open_near = False
                    break
            if open_near:
                score -= WEIGHTS['king_open_file'] * sign


    # Tempo bonus
    score += WEIGHTS['tempo'] if board.turn == chess.WHITE else -WEIGHTS['tempo']

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
    global transposition_table
    key = board.fen()
    if key in transposition_table and transposition_table[key][0] >= depth:
        return transposition_table[key][1], transposition_table[key][2]

    if depth == 0 or board.is_game_over():
        # if board.is_game_over():
        #     score = evaluate(board)
        # else:
        #     score = quiescence(board, alpha, beta)
        score = evaluate(board)
        transposition_table[key] = (depth, score, None)
        return score, None

    # # Null move pruning
    # if maximizing and depth > 2 and not board.is_check():
    #     board.push(chess.Move.null())
    #     null_score, _ = minimax(board, depth - 3, -beta, -beta + 1, False)
    #     null_score = -null_score
    #     board.pop()
    #     if null_score >= beta:
    #         transposition_table[key] = (depth, beta, None)
    #         return beta, None

    best_move = None
    def move_order_key(board, move):
        is_capture = board.is_capture(move)
        is_promo = move.promotion is not None
        return (is_capture, is_promo)

    moves = sorted(board.legal_moves, key=lambda m: move_order_key(board, m), reverse=True)
    # Better move ordering
    if maximizing:
        max_eval = -math.inf
        for i, move in enumerate(moves):
            board.push(move)
            # Late move reduction
            if i >= 4 and depth > 2:
                reduced_depth = depth - 2
            else:
                reduced_depth = depth - 1
            eval_score, _ = minimax(board, reduced_depth, alpha, beta, False)
            # If reduced and promising, re-search
            if i >= 4 and depth > 2 and eval_score > alpha:
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
        for i, move in enumerate(moves):
            board.push(move)
            # Late move reduction
            if i >= 4 and depth > 2:
                reduced_depth = depth - 2
            else:
                reduced_depth = depth - 1
            eval_score, _ = minimax(board, reduced_depth, alpha, beta, True)
            # If reduced and promising, re-search
            if i >= 4 and depth > 2 and eval_score < beta:
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

# def choose_move(board: chess.Board, depth: int = 3) -> chess.Move:
#     """Iterative deepening search with aspiration windows and opening book."""
#     # Check opening book
#     fen = board.fen()
#     if fen in opening_book:
#         return chess.Move.from_uci(opening_book[fen])
    
#     best_move = None
#     prev_score = 0
#     for d in range(1, depth + 1):
#         alpha = prev_score - 50
#         beta = prev_score + 50
#         while True:
#             score, move = minimax(board, d, alpha, beta, board.turn)
#             if alpha < score < beta:
#                 best_move = move
#                 prev_score = score
#                 break
#             elif score <= alpha:
#                 alpha = score - 50
#             else:
#                 beta = score + 50
#     return best_move

def choose_move(board: chess.Board, depth: int = 3) -> chess.Move:
    """Iterative deepening search with simple widening (no aspiration windows)."""
    # Check opening book
    fen = board.fen()
    if fen in opening_book:
        return chess.Move.from_uci(opening_book[fen])

    best_move = None
    for d in range(1, depth + 1):
        score, move = minimax(board, d, -math.inf, math.inf, board.turn)
        if move is not None:
            best_move = move

    return best_move

