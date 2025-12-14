import chess
import math

transposition_table = {}
killer_moves = {}  # Depth -> list of killer moves
history_moves = {}  # (from_square, to_square) -> count

# Opening book: FEN to UCI move - Famous openings
opening_book = {
    # Italian Game
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1': 'e2e4',
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1': 'e7e5',
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2': 'g1f3',
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2': 'b8c6',
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3': 'f1c4',
    'rnbqkb1r/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 0 4': 'f8c5',
    
    # Spanish Opening (Ruy Lopez)
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3': 'f1b5',
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 2 3': 'g8f6',
    
    # Sicilian Defense
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1': 'e2e4',
    'rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2': 'g1f3',
    'rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2': 'd7d6',
    
    # French Defense
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1': 'e2e4',
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1': 'e7e6',
    'rnbqkbnr/pppppppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2': 'd2d4',
    
    # Caro-Kann Defense
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1': 'c7c6',
    'rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2': 'd2d4',
    
    # Slav Defense
    'rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 2': 'd7d5',
    
    # Queen's Gambit
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1': 'd2d4',
    'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1': 'd7d5',
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

# Endgame king table - encourages centralization and aggression
KING_ENDGAME_TABLE = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -50,-40,-30,-20,-20,-30,-40,-50
]

PIECE_TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
    chess.KING: KING_TABLE,
}

ENDGAME_PIECE_TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
    chess.KING: KING_ENDGAME_TABLE,
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

def is_endgame(board: chess.Board) -> bool:
    """Detect endgame phase (few pieces left)."""
    total_pieces = len(board.piece_map()) - 2  # Exclude kings
    return total_pieces <= 8


def evaluate_basic_mates(board: chess.Board) -> int:
    """Recognize and handle famous endgame patterns."""
    pieces = board.piece_map()
    white_pieces = [p for p in pieces.values() if p.color == chess.WHITE]
    black_pieces = [p for p in pieces.values() if p.color == chess.BLACK]
    
    white_material = sum(PIECE_VALUES.get(p.piece_type, 0) for p in white_pieces)
    black_material = sum(PIECE_VALUES.get(p.piece_type, 0) for p in black_pieces)
    material_diff = white_material - black_material
    
    # K+Q vs K: Chase enemy king to edge and corner
    if material_diff > 800 and len(white_pieces) == 2 and any(p.piece_type == chess.QUEEN for p in white_pieces):
        black_king_sq = board.king(chess.BLACK)
        if black_king_sq:
            file = chess.square_file(black_king_sq)
            rank = chess.square_rank(black_king_sq)
            edge_distance = min(file, 7-file, rank, 7-rank)
            return 5000 + (3 - edge_distance) * 200
    
    if material_diff < -800 and len(black_pieces) == 2 and any(p.piece_type == chess.QUEEN for p in black_pieces):
        white_king_sq = board.king(chess.WHITE)
        if white_king_sq:
            file = chess.square_file(white_king_sq)
            rank = chess.square_rank(white_king_sq)
            edge_distance = min(file, 7-file, rank, 7-rank)
            return -5000 - (3 - edge_distance) * 200
    
    # K+R vs K: Drive to edge
    if material_diff > 400 and len(white_pieces) == 2 and any(p.piece_type == chess.ROOK for p in white_pieces):
        black_king_sq = board.king(chess.BLACK)
        white_king_sq = board.king(chess.WHITE)
        if black_king_sq and white_king_sq:
            # Rook and king vs king: push enemy king away and centralize own king
            bk_file = chess.square_file(black_king_sq)
            bk_rank = chess.square_rank(black_king_sq)
            wk_file = chess.square_file(white_king_sq)
            wk_rank = chess.square_rank(white_king_sq)
            
            # Bonus for driving black king to edge
            edge_bonus = (7 - min(bk_file, 7-bk_file, bk_rank, 7-bk_rank)) * 100
            # Bonus for centralizing white king
            center_bonus = (7 - abs(wk_file - 3.5) - abs(wk_rank - 3.5)) * 50
            return 5000 + edge_bonus + center_bonus
    
    if material_diff < -400 and len(black_pieces) == 2 and any(p.piece_type == chess.ROOK for p in black_pieces):
        white_king_sq = board.king(chess.WHITE)
        black_king_sq = board.king(chess.BLACK)
        if white_king_sq and black_king_sq:
            wk_file = chess.square_file(white_king_sq)
            wk_rank = chess.square_rank(white_king_sq)
            bk_file = chess.square_file(black_king_sq)
            bk_rank = chess.square_rank(black_king_sq)
            
            edge_bonus = (7 - min(wk_file, 7-wk_file, wk_rank, 7-wk_rank)) * 100
            center_bonus = (7 - abs(bk_file - 3.5) - abs(bk_rank - 3.5)) * 50
            return -5000 - edge_bonus - center_bonus
    
    # K+B vs K: Can't mate, but try to maintain advantage
    # K+N vs K: Can't mate, but try to maintain advantage
    # K+P vs K: Advance pawn and push enemy king away
    if len(white_pieces) <= 3:
        white_pawns = len([p for p in white_pieces if p.piece_type == chess.PAWN])
        if white_pawns > 0:
            # Bonus for advancing pawns
            for pawn_sq in board.pieces(chess.PAWN, chess.WHITE):
                rank = chess.square_rank(pawn_sq)
                return 1000 + rank * 100
    
    if len(black_pieces) <= 3:
        black_pawns = len([p for p in black_pieces if p.piece_type == chess.PAWN])
        if black_pawns > 0:
            for pawn_sq in board.pieces(chess.PAWN, chess.BLACK):
                rank = chess.square_rank(pawn_sq)
                return -1000 - (7 - rank) * 100
    
    return 0


def evaluate(board: chess.Board, position_history=None) -> int:
    """Enhanced evaluation with material, position, pawn structure, and endgame knowledge."""
    if board.is_checkmate():
        return -math.inf if board.turn else math.inf
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    # Skip repetition penalty during search - it's breaking move quality
    # Just rely on basic mating patterns and piece values
    score = 0
    
    # Check for basic mating patterns
    mate_score = evaluate_basic_mates(board)
    if mate_score != 0:
        return mate_score
    
    # Detect if we're in endgame
    in_endgame = is_endgame(board)
    tables = ENDGAME_PIECE_TABLES if in_endgame else PIECE_TABLES

    
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

    # Position (use endgame tables if appropriate)
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            table = tables[piece.piece_type]
            if piece.color == chess.WHITE:
                score += table[square]
            else:
                score -= table[63 - square]  # Flip for black

    # Mobility calculation is too expensive - disabled
    # original_turn = board.turn
    # board.turn = chess.WHITE
    # white_mobility = len(list(board.legal_moves))
    # board.turn = chess.BLACK
    # black_mobility = len(list(board.legal_moves))
    # board.turn = original_turn  # restore
    # score += WEIGHTS['mobility'] * (white_mobility - black_mobility)



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

    # ENDGAME ENHANCEMENTS
    if is_endgame(board):
        # King becomes active in endgame
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        if white_king and black_king:
            # Centralize king in endgame
            white_king_file = chess.square_file(white_king)
            white_king_rank = chess.square_rank(white_king)
            black_king_file = chess.square_file(black_king)
            black_king_rank = chess.square_rank(black_king)
            
            # Distance to center (reward central kings)
            white_center_dist = abs(white_king_file - 3.5) + abs(white_king_rank - 3.5)
            black_center_dist = abs(black_king_file - 3.5) + abs(black_king_rank - 3.5)
            score += (black_center_dist - white_center_dist) * 20
        
        # Strongly reward passed pawns in endgame
        for color in [chess.WHITE, chess.BLACK]:
            pawns = board.pieces(chess.PAWN, color)
            for pawn_sq in pawns:
                file = chess.square_file(pawn_sq)
                rank = chess.square_rank(pawn_sq)
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
                    if color == chess.WHITE:
                        # Reward advancement
                        score += (rank * 30)
                    else:
                        score -= ((7 - rank) * 30)

    return score

def quiescence(board: chess.Board, alpha: int, beta: int, depth: int = 0) -> int:
    """Quiescence search for captures only (no check extensions)."""
    if depth > 3:  # Very limited depth to prevent explosion
        return evaluate(board)
    stand_pat = evaluate(board)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    # Only search captures - no check extensions (too slow)
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

def minimax(board: chess.Board, depth: int, alpha: int, beta: int, maximizing: bool, position_history=None):
    global transposition_table, killer_moves, history_moves
    if position_history is None:
        position_history = []
    
    key = board.fen()
    
    # Only use transposition table for score cutoffs, NOT for move selection
    if key in transposition_table and transposition_table[key][0] >= depth:
        return transposition_table[key][1], None  # Return None for move to force new search
    
    if depth == 0 or board.is_game_over():
        score = quiescence(board, alpha, beta) if not board.is_game_over() else evaluate(board, position_history)
        transposition_table[key] = (depth, score, None)
        return score, None

    # Move ordering: MVV/LVA + History + Killers
    def move_score(move):
        score = 0
        # Killer moves (moves that caused cutoffs at this depth)
        if depth in killer_moves and move in killer_moves[depth]:
            score += 400
        
        # History moves (frequently good moves)
        move_key = (move.from_square, move.to_square)
        if move_key in history_moves:
            score += history_moves[move_key]
        
        # Promotions
        if move.promotion:
            score += 500
        
        # Captures: MVV/LVA (Most Valuable Victim, Least Valuable Attacker)
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            victim_value = PIECE_VALUES.get(victim.piece_type, 0) if victim else 0
            attacker_value = PIECE_VALUES.get(attacker.piece_type, 0) if attacker else 0
            score += 100 + (victim_value - attacker_value) // 10
        
        return score

    moves = sorted(board.legal_moves, key=move_score, reverse=True)
    best_move = None
    original_alpha = alpha
    
    # Track position for this branch
    current_pos = board.fen().split(' ')[0]
    new_history = position_history + [current_pos]
    
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
            eval_score, _ = minimax(board, reduced_depth, alpha, beta, False, new_history)
            # If reduced and promising, re-search
            if i >= 4 and depth > 2 and eval_score > alpha:
                eval_score, _ = minimax(board, depth - 1, alpha, beta, False, new_history)
            board.pop()
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                # Record killer move and update history
                if depth not in killer_moves:
                    killer_moves[depth] = []
                if move not in killer_moves[depth]:
                    killer_moves[depth].append(move)
                move_key = (move.from_square, move.to_square)
                history_moves[move_key] = history_moves.get(move_key, 0) + depth * depth
                break
        
        transposition_table[key] = (depth, max_eval, None)  # Don't store moves in TT
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
            eval_score, _ = minimax(board, reduced_depth, alpha, beta, True, new_history)
            # If reduced and promising, re-search
            if i >= 4 and depth > 2 and eval_score < beta:
                eval_score, _ = minimax(board, depth - 1, alpha, beta, True, new_history)
            board.pop()
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                # Record killer move and update history
                if depth not in killer_moves:
                    killer_moves[depth] = []
                if move not in killer_moves[depth]:
                    killer_moves[depth].append(move)
                move_key = (move.from_square, move.to_square)
                history_moves[move_key] = history_moves.get(move_key, 0) + depth * depth
                break
        
        transposition_table[key] = (depth, min_eval, None)  # Don't store moves in TT
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
    """Iterative deepening search with killer moves and history heuristic."""
    global killer_moves, transposition_table
    
    # Clear old killer moves (keep only current search depth)
    if len(killer_moves) > 100:
        killer_moves.clear()
    
    # Clear transposition table periodically to avoid memory bloat
    if len(transposition_table) > 50000:
        transposition_table.clear()
    
    # Check opening book
    fen = board.fen()
    if fen in opening_book:
        return chess.Move.from_uci(opening_book[fen])

    # Build position history from current game
    position_history = []
    # Reconstruct game history
    temp_board = chess.Board()
    for move in board.move_stack:
        position_history.append(temp_board.fen().split(' ')[0])
        temp_board.push(move)
    
    best_move = None
    best_score = -math.inf if board.turn == chess.WHITE else math.inf
    for d in range(1, depth + 1):
        score, move = minimax(board, d, -math.inf, math.inf, board.turn, position_history)
        if move is not None:
            best_move = move
            best_score = score
            # If mate is found, stop searching
            if abs(score) >= 50000:
                break

    return best_move

