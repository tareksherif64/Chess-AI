import argparse
import json
import math
import random
from typing import Dict, List, Tuple

import numpy as np
import chess
import chess.pgn

# Reuse engine constants
from engine import PIECE_VALUES, PIECE_TABLES, WEIGHTS

FEATURE_NAMES = [
    "bishop_pair",
    "mobility",
    "center_control",
    "development",
    "castling",
    "isolated_pawn",
    "doubled_pawn",
    "passed_pawn",
    "rook_open_file",
    "rook_7th",
    "pawn_shield",
    "king_open_file",
    "tempo",
]

CENTER_SQUARES = [chess.D4, chess.E4, chess.D5, chess.E5]
WHITE_KNIGHT_START = {chess.B1, chess.G1}
BLACK_KNIGHT_START = {chess.B8, chess.G8}
WHITE_BISHOP_START = {chess.C1, chess.F1}
BLACK_BISHOP_START = {chess.C8, chess.F8}


def is_rapid_or_classical(headers: Dict[str, str]) -> bool:
    """Keep games roughly >=10 minutes total per side."""
    tc = headers.get("TimeControl", "")
    if tc in ("-", "?"):
        return True
    parts = tc.split("+")
    try:
        base = int(parts[0])
    except ValueError:
        return True
    return base >= 600  # 10 minutes


def outcome_from_headers(headers: Dict[str, str]) -> float:
    res = headers.get("Result", "*")
    if res == "1-0":
        return 1.0
    if res == "0-1":
        return -1.0
    if res == "1/2-1/2":
        return 0.0
    return None


def rating_band_ok(headers: Dict[str, str], rmin: int, rmax: int) -> bool:
    try:
        wr = int(headers.get("WhiteElo", "0"))
        br = int(headers.get("BlackElo", "0"))
    except ValueError:
        return False
    return rmin <= wr <= rmax and rmin <= br <= rmax


def add_pawn_shield_squares(color: chess.Color, king_file: int, king_rank: int) -> List[int]:
    squares: List[int] = []
    if color == chess.WHITE and king_rank >= 1:
        for df in (-1, 0, 1):
            f = king_file + df
            if 0 <= f < 8:
                squares.append(chess.square(f, king_rank - 1))
    elif color == chess.BLACK and king_rank <= 6:
        for df in (-1, 0, 1):
            f = king_file + df
            if 0 <= f < 8:
                squares.append(chess.square(f, king_rank + 1))
    return squares


def feature_vector(board: chess.Board) -> Dict[str, float]:
    """Compute raw feature counts matching the evaluation structure (no weights applied)."""
    feats = {name: 0.0 for name in FEATURE_NAMES}

    # Bishop pair
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        feats["bishop_pair"] += 1
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        feats["bishop_pair"] -= 1

    # Mobility (as in engine evaluate: side-to-move full, other via null move)
    white_mob = len(list(board.legal_moves)) if board.turn == chess.WHITE else 0
    board.push(chess.Move.null())
    black_mob = len(list(board.legal_moves)) if board.turn == chess.BLACK else 0
    board.pop()
    feats["mobility"] += white_mob - black_mob

    # Center control
    for sq in CENTER_SQUARES:
        piece = board.piece_at(sq)
        if piece:
            feats["center_control"] += 1 if piece.color == chess.WHITE else -1

    # Development penalties (undeveloped pieces)
    for knight_sq in board.pieces(chess.KNIGHT, chess.WHITE):
        if knight_sq in WHITE_KNIGHT_START:
            feats["development"] -= 1
    for knight_sq in board.pieces(chess.KNIGHT, chess.BLACK):
        if knight_sq in BLACK_KNIGHT_START:
            feats["development"] += 1
    for bishop_sq in board.pieces(chess.BISHOP, chess.WHITE):
        if bishop_sq in WHITE_BISHOP_START:
            feats["development"] -= 1
    for bishop_sq in board.pieces(chess.BISHOP, chess.BLACK):
        if bishop_sq in BLACK_BISHOP_START:
            feats["development"] += 1

    # Castling rights
    if board.has_castling_rights(chess.WHITE):
        feats["castling"] += 1
    if board.has_castling_rights(chess.BLACK):
        feats["castling"] -= 1

    # Pawn structure
    for color in (chess.WHITE, chess.BLACK):
        pawns = board.pieces(chess.PAWN, color)
        for pawn_sq in pawns:
            file = chess.square_file(pawn_sq)
            rank = chess.square_rank(pawn_sq)
            # Isolated
            isolated = True
            for f in (file - 1, file + 1):
                if 0 <= f < 8:
                    for r in range(8):
                        if board.piece_at(chess.square(f, r)) == chess.Piece(chess.PAWN, color):
                            isolated = False
                            break
                if not isolated:
                    break
            if isolated:
                feats["isolated_pawn"] += 1 if color == chess.WHITE else -1
            # Doubled
            doubled = False
            for r in range(8):
                if r != rank and board.piece_at(chess.square(file, r)) == chess.Piece(chess.PAWN, color):
                    doubled = True
                    break
            if doubled:
                feats["doubled_pawn"] += 1 if color == chess.WHITE else -1
            # Passed
            passed = True
            direction = 1 if color == chess.WHITE else -1
            for r in range(rank + direction, 8 if color == chess.WHITE else -1, direction):
                for f in (file - 1, file, file + 1):
                    if 0 <= f < 8:
                        piece = board.piece_at(chess.square(f, r))
                        if piece and piece.piece_type == chess.PAWN and piece.color != color:
                            passed = False
                            break
                if not passed:
                    break
            if passed:
                feats["passed_pawn"] += 1 if color == chess.WHITE else -1

    # Rooks on open files and 7th
    for color in (chess.WHITE, chess.BLACK):
        for rook_sq in board.pieces(chess.ROOK, color):
            file = chess.square_file(rook_sq)
            rank = chess.square_rank(rook_sq)
            open_file = True
            for r in range(8):
                piece = board.piece_at(chess.square(file, r))
                if piece and piece.piece_type == chess.PAWN:
                    open_file = False
                    break
            if open_file:
                feats["rook_open_file"] += 1 if color == chess.WHITE else -1
            if (color == chess.WHITE and rank == 6) or (color == chess.BLACK and rank == 1):
                feats["rook_7th"] += 1 if color == chess.WHITE else -1

    # King safety
    for color in (chess.WHITE, chess.BLACK):
        king_sq = board.king(color)
        if king_sq is None:
            continue
        file = chess.square_file(king_sq)
        rank = chess.square_rank(king_sq)
        shield_squares = add_pawn_shield_squares(color, file, rank)
        shield_count = sum(1 for sq in shield_squares if board.piece_at(sq) == chess.Piece(chess.PAWN, color))
        if color == chess.WHITE:
            feats["pawn_shield"] += shield_count
        else:
            feats["pawn_shield"] -= shield_count
        for f in (file - 1, file, file + 1):
            if 0 <= f < 8:
                open_near = True
                for r in range(8):
                    piece = board.piece_at(chess.square(f, r))
                    if piece and piece.piece_type == chess.PAWN:
                        open_near = False
                        break
                if open_near:
                    feats["king_open_file"] += -1 if color == chess.WHITE else 1

    # Tempo
    feats["tempo"] += 1 if board.turn == chess.WHITE else -1

    return feats


def assemble_matrix(features: List[Dict[str, float]], targets: List[float]) -> Tuple[np.ndarray, np.ndarray]:
    X = np.array([[f[name] for name in FEATURE_NAMES] for f in features], dtype=float)
    y = np.array(targets, dtype=float)
    return X, y


def fit_ridge(X: np.ndarray, y: np.ndarray, lam: float) -> np.ndarray:
    n_features = X.shape[1]
    xtx = X.T @ X
    reg = lam * np.eye(n_features)
    xty = X.T @ y
    return np.linalg.solve(xtx + reg, xty)


def sample_positions(pgn_path: str, max_games: int, max_positions: int, rmin: int, rmax: int) -> Tuple[List[Dict[str, float]], List[float]]:
    feats: List[Dict[str, float]] = []
    targets: List[float] = []
    with open(pgn_path, "r", encoding="utf-8", errors="ignore") as f:
        game_count = 0
        while game_count < max_games:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            game_count += 1
            headers = game.headers
            result = outcome_from_headers(headers)
            if result is None:
                continue
            if not is_rapid_or_classical(headers):
                continue
            if not rating_band_ok(headers, rmin, rmax):
                continue
            board = game.board()
            for node in game.mainline_moves():
                board.push(node)
                if board.is_game_over():
                    break
                # Randomly subsample to avoid huge data
                if random.random() > 0.25:
                    continue
                feats.append(feature_vector(board))
                targets.append(result * 100.0)  # target in centipawns (rough scale)
                if len(feats) >= max_positions:
                    return feats, targets
    return feats, targets


def main() -> None:
    parser = argparse.ArgumentParser(description="Train evaluation weights from PGN data (linear ridge regression).")
    parser.add_argument("--pgn", required=True, help="Path to PGN file")
    parser.add_argument("--max-games", type=int, default=200, help="Maximum games to parse")
    parser.add_argument("--max-positions", type=int, default=50000, help="Maximum positions to sample")
    parser.add_argument("--rating-min", type=int, default=1400, help="Minimum player rating")
    parser.add_argument("--rating-max", type=int, default=2000, help="Maximum player rating")
    parser.add_argument("--lambda", dest="ridge", type=float, default=1e-2, help="L2 regularization strength")
    parser.add_argument("--output", default="tuned_weights.json", help="Output JSON file")
    args = parser.parse_args()

    print(f"Reading PGN: {args.pgn}")
    feats, targets = sample_positions(
        pgn_path=args.pgn,
        max_games=args.max_games,
        max_positions=args.max_positions,
        rmin=args.rating_min,
        rmax=args.rating_max,
    )
    if not feats:
        print("No positions collected; check filters or PGN path.")
        return
    X, y = assemble_matrix(feats, targets)
    print(f"Collected {len(y)} positions. Fitting ridge regression...")
    w = fit_ridge(X, y, args.ridge)
    tuned = {name: float(val) for name, val in zip(FEATURE_NAMES, w)}

    # Preserve any weight names not in FEATURE_NAMES (if engine expands in future)
    for k in WEIGHTS:
        if k not in tuned:
            tuned[k] = WEIGHTS[k]

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(tuned, f)
    print(f"Saved tuned weights to {args.output}")


if __name__ == "__main__":
    main()
