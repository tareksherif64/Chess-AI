import pygame
import chess
from engine import choose_move
import threading

WIDTH, HEIGHT = 640, 640
SQ_SIZE = WIDTH // 8
LIGHT = (240, 217, 181)
DARK = (181, 136, 99)

pygame.init()
FONT = pygame.font.SysFont("segoe ui symbol", 50)  # Font with Unicode chess symbols

PIECE_SYMBOLS = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
}

# Highlight colors with alpha
SELECTED_COLOR = (255, 255, 0, 100)
LAST_MOVE_COLOR = (255, 255, 0, 50)
CHECK_COLOR = (255, 0, 0, 100)
LEGAL_MOVE_COLOR = (0, 255, 0, 150)

# Threading variables
bot_move_result = None
bot_thread = None

def compute_bot_move(board, depth):
    global bot_move_result
    bot_move_result = choose_move(board, depth)


def draw_board(screen, board: chess.Board, selected_square=None, last_move=None, in_check=False, game_over=False, legal_moves=None, check_flash_timer=0, game_over_fade=0, animating_move=None, animation_progress=0.0):
    for rank in range(8):
        for file in range(8):
            color = LIGHT if (rank + file) % 2 == 0 else DARK
            rect = pygame.Rect(file * SQ_SIZE, rank * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            pygame.draw.rect(screen, color, rect)

    # Highlights
    if selected_square is not None:
        rank = 7 - chess.square_rank(selected_square)
        file = chess.square_file(selected_square)
        rect = pygame.Rect(file * SQ_SIZE, rank * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        highlight_surf = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
        highlight_surf.fill(SELECTED_COLOR)
        screen.blit(highlight_surf, rect.topleft)

    if last_move is not None:
        for sq in [last_move.from_square, last_move.to_square]:
            rank = 7 - chess.square_rank(sq)
            file = chess.square_file(sq)
            rect = pygame.Rect(file * SQ_SIZE, rank * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            highlight_surf = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
            highlight_surf.fill(LAST_MOVE_COLOR)
            screen.blit(highlight_surf, rect.topleft)

    if in_check and (check_flash_timer // 15) % 2 == 0:
        king_square = board.king(board.turn)
        if king_square is not None:
            rank = 7 - chess.square_rank(king_square)
            file = chess.square_file(king_square)
            rect = pygame.Rect(file * SQ_SIZE, rank * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            highlight_surf = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
            highlight_surf.fill(CHECK_COLOR)
            screen.blit(highlight_surf, rect.topleft)

    if legal_moves:
        for sq in legal_moves:
            rank = 7 - chess.square_rank(sq)
            file = chess.square_file(sq)
            center = (file * SQ_SIZE + SQ_SIZE // 2, rank * SQ_SIZE + SQ_SIZE // 2)
            pygame.draw.circle(screen, LEGAL_MOVE_COLOR[:3], center, SQ_SIZE // 8)  # Semi-transparent green circle

    # Pieces
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            # Skip if animating and this is the moving piece's start square
            if animating_move and square == animating_move.from_square:
                continue
            # Skip if animating capture and this is the destination square
            if animating_move and square == animating_move.to_square and board.is_capture(animating_move):
                continue
            symbol = piece.symbol()
            rank = 7 - chess.square_rank(square)
            file = chess.square_file(square)
            rect = pygame.Rect(file * SQ_SIZE, rank * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            # Piece color
            if piece.color == chess.WHITE:
                piece_color = (200, 200, 200)
                outline_color = (0, 0, 0)
            else:
                piece_color = (50, 50, 50)
                outline_color = (255, 255, 255)
            # Draw outline
            text = FONT.render(PIECE_SYMBOLS[symbol], True, outline_color)
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                text_rect = text.get_rect(center=(rect.centerx + dx, rect.centery + dy))
                screen.blit(text, text_rect)
            # Draw main text
            text = FONT.render(PIECE_SYMBOLS[symbol], True, piece_color)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

    # Draw animating piece
    if animating_move:
        piece = board.piece_at(animating_move.from_square)
        if piece:
            symbol = piece.symbol()
            from_rank = 7 - chess.square_rank(animating_move.from_square)
            from_file = chess.square_file(animating_move.from_square)
            to_rank = 7 - chess.square_rank(animating_move.to_square)
            to_file = chess.square_file(animating_move.to_square)
            current_file = from_file + (to_file - from_file) * animation_progress
            current_rank = from_rank + (to_rank - from_rank) * animation_progress
            center_x = current_file * SQ_SIZE + SQ_SIZE // 2
            center_y = current_rank * SQ_SIZE + SQ_SIZE // 2
            # Piece color
            if piece.color == chess.WHITE:
                piece_color = (200, 200, 200)
                outline_color = (0, 0, 0)
            else:
                piece_color = (50, 50, 50)
                outline_color = (255, 255, 255)
            # Draw outline
            text = FONT.render(PIECE_SYMBOLS[symbol], True, outline_color)
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                screen.blit(text, (center_x - text.get_width()//2 + dx, center_y - text.get_height()//2 + dy))
            # Draw main text
            text = FONT.render(PIECE_SYMBOLS[symbol], True, piece_color)
            screen.blit(text, (center_x - text.get_width()//2, center_y - text.get_height()//2))

    # Overlays
    if in_check and not game_over:
        check_text = FONT.render("CHECK", True, (255, 0, 0))
        screen.blit(check_text, (WIDTH // 2 - check_text.get_width() // 2, HEIGHT // 2 - check_text.get_height() // 2))

    if game_over:
        if board.is_checkmate():
            if board.turn == chess.WHITE:
                msg = "Checkmate - You Lose"
            else:
                msg = "Checkmate - You Win"
        else:
            msg = "Draw"
        # Animated overlay
        overlay_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay_surf.fill((0, 0, 0, game_over_fade))
        screen.blit(overlay_surf, (0, 0))
        game_over_text = FONT.render(msg, True, (255, 255, 255))
        game_over_text.set_alpha(game_over_fade)
        text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(game_over_text, text_rect)

def square_from_mouse(pos):
    x, y = pos
    file = x // SQ_SIZE
    rank = 7 - (y // SQ_SIZE)
    if 0 <= file < 8 and 0 <= rank < 8:
        return chess.square(file, rank)
    return None

def run_gui():
    global bot_thread, bot_move_result
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess AI")
    clock = pygame.time.Clock()

    board = chess.Board()
    selected_square = None
    last_move = None
    legal_moves = None
    check_flash_timer = 0
    game_over_fade = 0
    animating_move = None
    animation_progress = 0.0
    running = True

    while running:
        clock.tick(60)
        # Update animations
        if board.is_check():
            check_flash_timer += 1
        else:
            check_flash_timer = 0
        if board.is_game_over() and game_over_fade < 255:
            game_over_fade += 5  # Fade speed
        if animating_move:
            animation_progress += 0.05  # Animation speed
            if animation_progress >= 1.0:
                board.push(animating_move)
                last_move = animating_move
                animating_move = None
                animation_progress = 0.0
                # Bot move after player animation
                if not board.is_game_over() and not board.turn:  # After white move, turn is black
                    bot_move_result = None
                    bot_thread = threading.Thread(target=compute_bot_move, args=(board.copy(), 3))
                    bot_thread.start()
        # Check if bot thread is done
        if bot_thread and not bot_thread.is_alive():
            if bot_move_result:
                animating_move = bot_move_result
                animation_progress = 0.0
            bot_thread = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if board.is_game_over():
                    board = chess.Board()
                    selected_square = None
                    last_move = None
                    legal_moves = None
                    check_flash_timer = 0
                    game_over_fade = 0
                    animating_move = None
                    animation_progress = 0.0
                    if bot_thread:
                        bot_thread.join()  # Wait for thread to finish
                    bot_thread = None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not board.is_game_over() and not animating_move:
                    sq = square_from_mouse(event.pos)
                    if sq is not None:
                        if selected_square is None:
                            # first click: select square
                            if board.piece_at(sq) and board.piece_at(sq).color == chess.WHITE:
                                selected_square = sq
                                legal_moves = [move.to_square for move in board.legal_moves if move.from_square == sq]
                        else:
                            # second click: try move
                            move = chess.Move(selected_square, sq)
                            if move in board.legal_moves:
                                animating_move = move
                                animation_progress = 0.0
                                selected_square = None
                                legal_moves = None
                            else:
                                # reset selection if illegal
                                selected_square = None
                                legal_moves = None

        draw_board(screen, board, selected_square, last_move, board.is_check(), board.is_game_over(), legal_moves, check_flash_timer, game_over_fade, animating_move, animation_progress)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run_gui()
