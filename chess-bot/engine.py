import chess
import math

transposition_table = {}
killer_moves = {}  # Depth -> list of killer moves
history_moves = {}  # (from_square, to_square) -> count

# Opening book: FEN to UCI move - Comprehensive opening coverage
opening_book = {
    # Starting position
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1': 'e2e4',
    
    # King's Pawn Openings (1.e4)
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1': 'e7e5',
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2': 'g1f3',
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2': 'b8c6',
    
    # Italian Game
    'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3': 'f1c4',
    'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4': 'd2d3',
    'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4': 'f8c5',
    'r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 5 5': 'c2c3',
    'r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2PP1N2/PP3PPP/RNBQK2R b KQkq - 0 5': 'd7d6',
    
    # Spanish Opening (Ruy Lopez)
    'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3': 'f1b5',
    'r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3': 'a7a6',
    'r1bqkbnr/1ppp1ppp/p1n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4': 'b5a4',
    'r1bqkbnr/1ppp1ppp/p1n5/4p3/B3P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 1 4': 'g8f6',
    'r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 5': 'e1g1',
    'r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 b kq - 3 5': 'f8e7',
    'r1bqk2r/1pppbppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6': 'f1e1',
    'r1bqk2r/1pppbppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQR1K1 b kq - 5 6': 'b7b5',
    'r1bqk2r/2ppbppp/p1n2n2/1p2p3/B3P3/5N2/PPPP1PPP/RNBQR1K1 w kq - 0 7': 'a4b3',
    'r1bqk2r/2ppbppp/p1n2n2/1p2p3/4P3/1B3N2/PPPP1PPP/RNBQR1K1 b kq - 1 7': 'd7d6',
    
    # Scotch Game
    'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3': 'd2d4',
    'r1bqkbnr/pppp1ppp/2n5/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3': 'e5d4',
    'r1bqkbnr/pppp1ppp/2n5/8/3pP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 0 4': 'f3d4',
    
    # Two Knights Defense
    'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3': 'b1c3',
    'r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 4 4': 'f1c4',
    
    # Petrov Defense
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2': 'g8f6',
    'rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3': 'f3e5',
    'rnbqkb1r/pppp1ppp/5n2/4N3/4P3/8/PPPP1PPP/RNBQKB1R b KQkq - 0 3': 'd7d6',
    'rnbqkb1r/ppp2ppp/3p1n2/4N3/4P3/8/PPPP1PPP/RNBQKB1R w KQkq - 0 4': 'e5f3',
    'rnbqkb1r/ppp2ppp/3p1n2/8/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 4': 'f6e4',
    
    # Sicilian Defense - Main Lines
    'rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2': 'g1f3',
    'rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2': 'd7d6',
    'rnbqkbnr/pp2pppp/3p4/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3': 'd2d4',
    'rnbqkbnr/pp2pppp/3p4/2p5/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3': 'c5d4',
    'rnbqkbnr/pp2pppp/3p4/8/3pP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 0 4': 'f3d4',
    'rnbqkbnr/pp2pppp/3p4/8/3NP3/8/PPP2PPP/RNBQKB1R b KQkq - 0 4': 'g8f6',
    'rnbqkb1r/pp2pppp/3p1n2/8/3NP3/8/PPP2PPP/RNBQKB1R w KQkq - 1 5': 'b1c3',
    
    # Sicilian - Najdorf Variation
    'rnbqkb1r/pp2pppp/3p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R b KQkq - 2 5': 'a7a6',
    'rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6': 'f1e2',
    'rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP1BPPP/R1BQK2R b KQkq - 1 6': 'e7e5',
    'rnbqkb1r/1p3ppp/p2p1n2/4p3/3NP3/2N5/PPP1BPPP/R1BQK2R w KQkq - 0 7': 'd4b3',
    
    # Sicilian - Dragon Variation
    'rnbqkb1r/pp2pppp/3p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R b KQkq - 2 5': 'g7g6',
    'rnbqkb1r/pp2pp1p/3p1np1/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6': 'f1e3',
    'rnbqkb1r/pp2pp1p/3p1np1/8/3NP3/2N1B3/PPP2PPP/R2QKB1R b KQkq - 1 6': 'f8g7',
    'rnbqk2r/pp2ppbp/3p1np1/8/3NP3/2N1B3/PPP2PPP/R2QKB1R w KQkq - 2 7': 'f2f3',
    
    # French Defense
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1': 'e7e6',
    'rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2': 'd2d4',
    'rnbqkbnr/pppp1ppp/4p3/8/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2': 'd7d5',
    'rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3': 'b1c3',
    'rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/2N5/PPP2PPP/R1BQKBNR b KQkq - 1 3': 'g8f6',
    'rnbqkb1r/ppp2ppp/4pn2/3p4/3PP3/2N5/PPP2PPP/R1BQKBNR w KQkq - 2 4': 'c1g5',
    'rnbqkb1r/ppp2ppp/4pn2/3p2B1/3PP3/2N5/PPP2PPP/R2QKBNR b KQkq - 3 4': 'f8e7',
    'rnbqk2r/ppp1bppp/4pn2/3p2B1/3PP3/2N5/PPP2PPP/R2QKBNR w KQkq - 4 5': 'e4e5',
    
    # Caro-Kann Defense
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1': 'c7c6',
    'rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2': 'd2d4',
    'rnbqkbnr/pp1ppppp/2p5/8/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2': 'd7d5',
    'rnbqkbnr/pp2pppp/2p5/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3': 'b1c3',
    'rnbqkbnr/pp2pppp/2p5/3p4/3PP3/2N5/PPP2PPP/R1BQKBNR b KQkq - 1 3': 'd5e4',
    'rnbqkbnr/pp2pppp/2p5/8/3Pp3/2N5/PPP2PPP/R1BQKBNR w KQkq - 0 4': 'c3e4',
    'rnbqkbnr/pp2pppp/2p5/8/3PN3/8/PPP2PPP/R1BQKBNR b KQkq - 0 4': 'c8f5',
    'rn1qkbnr/pp2pppp/2p5/5b2/3PN3/8/PPP2PPP/R1BQKBNR w KQkq - 1 5': 'e4g3',
    
    # Pirc Defense
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1': 'd7d6',
    'rnbqkbnr/ppp1pppp/3p4/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2': 'd2d4',
    'rnbqkbnr/ppp1pppp/3p4/8/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2': 'g8f6',
    'rnbqkb1r/ppp1pppp/3p1n2/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 1 3': 'b1c3',
    'rnbqkb1r/ppp1pppp/3p1n2/8/3PP3/2N5/PPP2PPP/R1BQKBNR b KQkq - 2 3': 'g7g6',
    'rnbqkb1r/ppp1pp1p/3p1np1/8/3PP3/2N5/PPP2PPP/R1BQKBNR w KQkq - 0 4': 'f1e2',
    
    # Queen's Gambit
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1': 'd2d4',
    'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1': 'd7d5',
    'rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2': 'c2c4',
    'rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2': 'e7e6',
    'rnbqkbnr/ppp2ppp/4p3/3p4/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3': 'b1c3',
    'rnbqkbnr/ppp2ppp/4p3/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR b KQkq - 1 3': 'g8f6',
    'rnbqkb1r/ppp2ppp/4pn2/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4': 'c1g5',
    'rnbqkb1r/ppp2ppp/4pn2/3p2B1/2PP4/2N5/PP2PPPP/R2QKBNR b KQkq - 3 4': 'f8e7',
    'rnbqk2r/ppp1bppp/4pn2/3p2B1/2PP4/2N5/PP2PPPP/R2QKBNR w KQkq - 4 5': 'e2e3',
    
    # Queen's Gambit Accepted
    'rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2': 'd5c4',
    'rnbqkbnr/ppp1pppp/8/8/2pP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3': 'g1f3',
    'rnbqkbnr/ppp1pppp/8/8/2pP4/5N2/PP2PPPP/RNBQKB1R b KQkq - 1 3': 'g8f6',
    'rnbqkb1r/ppp1pppp/5n2/8/2pP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 2 4': 'e2e3',
    
    # Slav Defense
    'rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2': 'c7c6',
    'rnbqkbnr/pp2pppp/2p5/3p4/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3': 'g1f3',
    'rnbqkbnr/pp2pppp/2p5/3p4/2PP4/5N2/PP2PPPP/RNBQKB1R b KQkq - 1 3': 'g8f6',
    'rnbqkb1r/pp2pppp/2p2n2/3p4/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 2 4': 'b1c3',
    
    # Nimzo-Indian Defense
    'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1': 'g8f6',
    'rnbqkb1r/pppppppp/5n2/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 1 2': 'c2c4',
    'rnbqkb1r/pppppppp/5n2/8/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2': 'e7e6',
    'rnbqkb1r/pppp1ppp/4pn2/8/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3': 'b1c3',
    'rnbqkb1r/pppp1ppp/4pn2/8/2PP4/2N5/PP2PPPP/R1BQKBNR b KQkq - 1 3': 'f8b4',
    'rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4': 'e2e3',
    'rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N1P3/PP3PPP/R1BQKBNR b KQkq - 0 4': 'e8g8',
    
    # King's Indian Defense
    'rnbqkb1r/pppppppp/5n2/8/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2': 'g7g6',
    'rnbqkb1r/pppppp1p/5np1/8/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3': 'b1c3',
    'rnbqkb1r/pppppp1p/5np1/8/2PP4/2N5/PP2PPPP/R1BQKBNR b KQkq - 1 3': 'f8g7',
    'rnbqk2r/ppppppbp/5np1/8/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4': 'e2e4',
    'rnbqk2r/ppppppbp/5np1/8/2PPP3/2N5/PP3PPP/R1BQKBNR b KQkq - 0 4': 'd7d6',
    'rnbqk2r/ppp1ppbp/3p1np1/8/2PPP3/2N5/PP3PPP/R1BQKBNR w KQkq - 0 5': 'g1f3',
    
    # English Opening
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1': 'c2c4',
    'rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 1': 'e7e5',
    'rnbqkbnr/pppp1ppp/8/4p3/2P5/8/PP1PPPPP/RNBQKBNR w KQkq - 0 2': 'b1c3',
    'rnbqkbnr/pppp1ppp/8/4p3/2P5/2N5/PP1PPPPP/R1BQKBNR b KQkq - 1 2': 'g8f6',
    'rnbqkb1r/pppp1ppp/5n2/4p3/2P5/2N5/PP1PPPPP/R1BQKBNR w KQkq - 2 3': 'g1f3',
}

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 320,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# Piece-square tables for MIDDLEGAME (for white, from a1 to h8)
PAWN_MG = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 27, 27, 10,  5,  5,
    0,  0,  0, 25, 25,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-25,-25, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

PAWN_EG = [
    0,  0,  0,  0,  0,  0,  0,  0,
    80, 80, 80, 80, 80, 80, 80, 80,
    50, 50, 50, 50, 50, 50, 50, 50,
    30, 30, 30, 30, 30, 30, 30, 30,
    20, 20, 20, 20, 20, 20, 20, 20,
    10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10,
    0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_MG = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

KNIGHT_EG = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_MG = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

BISHOP_EG = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_MG = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

ROOK_EG = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_MG = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

QUEEN_EG = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_MG = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

KING_EG = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

def get_game_phase(board: chess.Board) -> float:
    """Calculate game phase (0.0 = endgame, 1.0 = opening/middlegame)."""
    knight_phase = 1
    bishop_phase = 1
    rook_phase = 2
    queen_phase = 4
    total_phase = knight_phase * 4 + bishop_phase * 4 + rook_phase * 4 + queen_phase * 2
    
    phase = 0
    phase += len(board.pieces(chess.KNIGHT, chess.WHITE)) * knight_phase
    phase += len(board.pieces(chess.KNIGHT, chess.BLACK)) * knight_phase
    phase += len(board.pieces(chess.BISHOP, chess.WHITE)) * bishop_phase
    phase += len(board.pieces(chess.BISHOP, chess.BLACK)) * bishop_phase
    phase += len(board.pieces(chess.ROOK, chess.WHITE)) * rook_phase
    phase += len(board.pieces(chess.ROOK, chess.BLACK)) * rook_phase
    phase += len(board.pieces(chess.QUEEN, chess.WHITE)) * queen_phase
    phase += len(board.pieces(chess.QUEEN, chess.BLACK)) * queen_phase
    
    phase = min(phase, total_phase)
    return phase / total_phase

def get_pst_value(piece_type: chess.PieceType, square: int, phase: float) -> int:
    """Get piece-square table value with phase interpolation."""
    mg_tables = {
        chess.PAWN: PAWN_MG,
        chess.KNIGHT: KNIGHT_MG,
        chess.BISHOP: BISHOP_MG,
        chess.ROOK: ROOK_MG,
        chess.QUEEN: QUEEN_MG,
        chess.KING: KING_MG,
    }
    eg_tables = {
        chess.PAWN: PAWN_EG,
        chess.KNIGHT: KNIGHT_EG,
        chess.BISHOP: BISHOP_EG,
        chess.ROOK: ROOK_EG,
        chess.QUEEN: QUEEN_EG,
        chess.KING: KING_EG,
    }
    
    mg_value = mg_tables[piece_type][square]
    eg_value = eg_tables[piece_type][square]
    
    # Linear interpolation between middlegame and endgame
    return int(mg_value * phase + eg_value * (1 - phase))

# Tunable evaluation weights
WEIGHTS = {
    'bishop_pair': 50,
    'mobility': 5,
    'center_control': 10,
    'development': 20,
    'castling': 30,
    'isolated_pawn': 20,
    'doubled_pawn': 88,
    'passed_pawn': 32,
    'backward_pawn': 15,
    'rook_open_file': 25,
    'rook_7th': 40,
    'rook_connected': 20,
    'pawn_shield': 93,
    'king_open_file': 100,
    'king_attack': 30,
    'tempo': 10,
    'contempt': 50,  # Penalty for draws (discourage drawing)
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
        # Contempt factor: treat draws as slightly negative
        return -WEIGHTS['contempt'] if board.turn == chess.WHITE else WEIGHTS['contempt']
    
    # Check for draw by repetition
    if position_history:
        current_pos = board.fen().split(' ')[0]
        if position_history.count(current_pos) >= 2:
            return -WEIGHTS['contempt'] if board.turn == chess.WHITE else WEIGHTS['contempt']
    
    score = 0
    
    # Check for basic mating patterns
    mate_score = evaluate_basic_mates(board)
    if mate_score != 0:
        return mate_score
    
    # Calculate game phase for smooth PST interpolation
    phase = get_game_phase(board)
    in_endgame = phase < 0.4  # Consider endgame when phase drops below 40%
    
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

    # Position with phase-based interpolation
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            pst_value = get_pst_value(piece.piece_type, square, phase)
            if piece.color == chess.WHITE:
                score += pst_value
            else:
                score -= get_pst_value(piece.piece_type, 63 - square, phase)

    # Efficient mobility calculation (only count pieces, not all moves)
    if not in_endgame:
        white_mobility = 0
        black_mobility = 0
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece:
                if piece.color == chess.WHITE:
                    white_mobility += 1
                else:
                    black_mobility += 1
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
            
            # Backward pawn (no pawn behind on adjacent files, and can't advance safely)
            backward = False
            if not isolated:
                has_support = False
                direction = 1 if color == chess.WHITE else -1
                for f in [file-1, file+1]:
                    if 0 <= f < 8:
                        for r in range(rank - direction, -1 if color == chess.WHITE else 8, -direction):
                            if board.piece_at(chess.square(f, r)) == chess.Piece(chess.PAWN, color):
                                has_support = True
                                break
                        if has_support:
                            break
                if not has_support:
                    # Check if advance square is attacked
                    advance_rank = rank + direction
                    if 0 <= advance_rank < 8:
                        advance_sq = chess.square(file, advance_rank)
                        # Simplified: check if enemy pawn attacks this square
                        for f in [file-1, file+1]:
                            if 0 <= f < 8:
                                enemy_pawn_rank = advance_rank + direction
                                if 0 <= enemy_pawn_rank < 8:
                                    if board.piece_at(chess.square(f, enemy_pawn_rank)) == chess.Piece(chess.PAWN, not color):
                                        backward = True
                                        break
                if backward:
                    score -= WEIGHTS['backward_pawn'] if color == chess.WHITE else -WEIGHTS['backward_pawn']
            
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
                bonus = WEIGHTS['passed_pawn']
                # Stronger bonus for advanced passed pawns
                advancement = rank if color == chess.WHITE else 7 - rank
                bonus += advancement * 10
                score += bonus if color == chess.WHITE else -bonus

    # Rooks on open files and 7th rank
    for color in [chess.WHITE, chess.BLACK]:
        rooks = board.pieces(chess.ROOK, color)
        rook_list = list(rooks)
        for i, rook_sq in enumerate(rook_list):
            file = chess.square_file(rook_sq)
            rank = chess.square_rank(rook_sq)
            
            # Rook on open file
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
            
            # Connected rooks (on same rank or file)
            if i < len(rook_list) - 1:
                for j in range(i + 1, len(rook_list)):
                    other_rook = rook_list[j]
                    if chess.square_file(rook_sq) == chess.square_file(other_rook) or \
                       chess.square_rank(rook_sq) == chess.square_rank(other_rook):
                        score += WEIGHTS['rook_connected'] if color == chess.WHITE else -WEIGHTS['rook_connected']

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
        
        # King attack zone (count enemy pieces attacking near king)
        if not in_endgame:
            attack_count = 0
            for attack_file in range(max(0, file-2), min(8, file+3)):
                for attack_rank in range(max(0, rank-2), min(8, rank+3)):
                    attack_sq = chess.square(attack_file, attack_rank)
                    attackers = board.attackers(not color, attack_sq)
                    attack_count += len(attackers)
            score -= WEIGHTS['king_attack'] * attack_count * sign


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
    """Quiescence search with delta pruning and stand-pat."""
    if depth > 6:  # Increased depth for better tactical vision
        return evaluate(board)
    
    stand_pat = evaluate(board)
    if stand_pat >= beta:
        return beta
    
    # Delta pruning: if we're too far behind even with a queen capture, prune
    BIG_DELTA = 975  # Queen value + margin
    if stand_pat < alpha - BIG_DELTA:
        return alpha
    
    if alpha < stand_pat:
        alpha = stand_pat

    # Order captures by MVV/LVA
    captures = [m for m in board.legal_moves if board.is_capture(m)]
    def capture_score(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        victim_value = PIECE_VALUES.get(victim.piece_type, 0) if victim else 0
        attacker_value = PIECE_VALUES.get(attacker.piece_type, 0) if attacker else 0
        return victim_value * 10 - attacker_value
    
    captures.sort(key=capture_score, reverse=True)
    
    for move in captures:
        board.push(move)
        score = -quiescence(board, -beta, -alpha, depth + 1)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

def pvs_search(board: chess.Board, depth: int, alpha: int, beta: int, position_history=None, null_move_allowed=True):
    """Principal Variation Search with null move pruning and check extensions."""
    global transposition_table, killer_moves, history_moves
    if position_history is None:
        position_history = []
    
    key = board.fen()
    
    # Check transposition table
    if key in transposition_table and transposition_table[key][0] >= depth:
        return transposition_table[key][1], None
    
    # Check for draw by repetition
    current_pos = board.fen().split(' ')[0]
    if position_history.count(current_pos) >= 2:
        return 0, None  # Draw by repetition
    
    # Terminal nodes
    if board.is_game_over():
        score = evaluate(board, position_history)
        transposition_table[key] = (depth, score, None)
        return score, None
    
    # Check extension: extend search if in check
    in_check = board.is_check()
    if in_check:
        depth += 1
    
    if depth == 0:
        score = quiescence(board, alpha, beta)
        transposition_table[key] = (0, score, None)
        return score, None
    
    # Null move pruning: if we can afford to pass, position is too good
    if null_move_allowed and depth >= 3 and not in_check:
        # Don't do null move if we're in zugzwang-prone endgame (only pawns+king)
        has_pieces = any(board.piece_at(sq) and board.piece_at(sq).piece_type not in [chess.PAWN, chess.KING] 
                        and board.piece_at(sq).color == board.turn for sq in chess.SQUARES)
        if has_pieces:
            board.push(chess.Move.null())
            null_score, _ = pvs_search(board, depth - 3, -beta, -beta + 1, position_history, False)
            null_score = -null_score
            board.pop()
            if null_score >= beta:
                return beta, None  # Beta cutoff
    
    # Razoring: if position is hopeless and depth is low, reduce search
    if not in_check and depth <= 3:
        eval_score = evaluate(board, position_history)
        razor_margin = 300 * depth
        if eval_score + razor_margin < alpha:
            # Try quiescence to see if we can improve
            q_score = quiescence(board, alpha - razor_margin, alpha - razor_margin + 1)
            if q_score + razor_margin <= alpha:
                return q_score, None
    
    # Futility pruning: at low depth, if we're far behind, skip quiet moves
    futility_pruning = False
    futility_margin = 0
    if not in_check and depth <= 3:
        eval_score = evaluate(board, position_history)
        futility_margin = 150 * depth
        if eval_score + futility_margin <= alpha:
            futility_pruning = True
    
    # Move ordering
    def move_score(move):
        score = 0
        if depth in killer_moves and move in killer_moves[depth]:
            score += 9000
        move_key = (move.from_square, move.to_square)
        if move_key in history_moves:
            score += history_moves[move_key]
        if move.promotion:
            score += 10000
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            victim_value = PIECE_VALUES.get(victim.piece_type, 0) if victim else 0
            attacker_value = PIECE_VALUES.get(attacker.piece_type, 0) if attacker else 0
            score += 8000 + victim_value - attacker_value
        return score
    
    moves = sorted(board.legal_moves, key=move_score, reverse=True)
    if not moves:
        return evaluate(board, position_history), None
    
    best_move = None
    best_score = -math.inf
    new_history = position_history + [current_pos]
    
    # Principal Variation Search
    for i, move in enumerate(moves):
        # Futility pruning: skip quiet moves if position is hopeless
        if futility_pruning and i > 0 and not board.is_capture(move) and not move.promotion:
            continue
        
        # Late move pruning: at low depth, prune moves late in the list
        if not in_check and depth <= 3 and i >= (3 + depth * depth):
            if not board.is_capture(move) and not move.promotion:
                continue
        
        board.push(move)
        
        if i == 0:
            # Full window search for first move (PV)
            score, _ = pvs_search(board, depth - 1, -beta, -alpha, new_history, True)
            score = -score
        else:
            # Late Move Reduction (LMR): reduce depth for later moves
            reduction = 0
            if depth >= 3 and i >= 4 and not board.is_capture(move) and not move.promotion and not in_check:
                reduction = 1
                if i >= 8:
                    reduction = 2
            
            # Null window search for remaining moves
            score, _ = pvs_search(board, depth - 1 - reduction, -alpha - 1, -alpha, new_history, True)
            score = -score
            
            # If it fails high, re-search with full window
            if alpha < score < beta:
                score, _ = pvs_search(board, depth - 1, -beta, -alpha, new_history, True)
                score = -score
        
        board.pop()
        
        if score > best_score:
            best_score = score
            best_move = move
        
        if score > alpha:
            alpha = score
        
        if alpha >= beta:
            # Beta cutoff - update killer and history
            if not board.is_capture(move):
                if depth not in killer_moves:
                    killer_moves[depth] = []
                if move not in killer_moves[depth]:
                    killer_moves[depth].insert(0, move)
                    if len(killer_moves[depth]) > 2:
                        killer_moves[depth] = killer_moves[depth][:2]
            
            move_key = (move.from_square, move.to_square)
            history_moves[move_key] = history_moves.get(move_key, 0) + depth * depth
            break
    
    transposition_table[key] = (depth, best_score, None)
    return best_score, best_move

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

def choose_move(board: chess.Board, depth: int = 5) -> chess.Move:
    """Iterative deepening with aspiration windows."""
    global killer_moves, transposition_table
    
    # Clear old killer moves periodically
    if len(killer_moves) > 100:
        killer_moves.clear()
    
    # Clear transposition table periodically
    if len(transposition_table) > 100000:
        transposition_table.clear()
    
    # Check opening book
    fen = board.fen()
    if fen in opening_book:
        return chess.Move.from_uci(opening_book[fen])
    
    # Build position history
    position_history = []
    temp_board = chess.Board()
    for move in board.move_stack:
        position_history.append(temp_board.fen().split(' ')[0])
        temp_board.push(move)
    
    best_move = None
    prev_score = 0
    
    # Iterative deepening with aspiration windows
    for d in range(1, depth + 1):
        if d == 1:
            # First iteration: full window
            score, move = pvs_search(board, d, -math.inf, math.inf, position_history)
        else:
            # Aspiration window: narrow search around previous score
            aspiration_window = 50
            alpha = prev_score - aspiration_window
            beta = prev_score + aspiration_window
            
            score, move = pvs_search(board, d, alpha, beta, position_history)
            
            # If we fall outside window, re-search with wider window
            if score <= alpha or score >= beta:
                score, move = pvs_search(board, d, -math.inf, math.inf, position_history)
        
        if move is not None:
            best_move = move
            prev_score = score
        
        # If mate found, stop searching
        if abs(score) >= 50000:
            break
    
    return best_move

