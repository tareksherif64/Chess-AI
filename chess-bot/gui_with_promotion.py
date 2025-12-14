import pygame
import chess
from engine import choose_move
import threading

WIDTH, HEIGHT = 640, 640
SQ_SIZE = WIDTH // 8
LIGHT = (240, 217, 181)
DARK = (181, 136, 99)

pygame.init()
FONT = pygame.font.SysFont("segoe ui symbol", 50)

PIECE_SYMBOLS = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
}

SELECTED_COLOR = (255, 255, 0, 100)
LAST_MOVE_COLOR = (255, 255, 0, 50)
CHECK_COLOR = (255, 0, 0, 100)
LEGAL_MOVE_COLOR = (0, 255, 0, 150)

bot_move_result = None
bot_thread = None

def compute_bot_move(board, depth):
    global bot_move_result
    bot_move_result = choose_move(board, depth)


def draw_promotion_dialog(screen, color):
    """Draw a dialog for user to select promotion piece."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    dialog_width = 400
    dialog_height = 150
    dialog_x = (WIDTH - dialog_width) // 2
    dialog_y = (HEIGHT - dialog_height) // 2
    pygame.draw.rect(screen, (60, 60, 60), (dialog_x, dialog_y, dialog_width, dialog_height))
    pygame.draw.rect(screen, (255, 255, 255), (dialog_x, dialog_y, dialog_width, dialog_height), 3)
    
    title_font = pygame.font.SysFont("segoe ui", 24, bold=True)
    title = title_font.render("Choose Promotion Piece", True, (255, 255, 255))
    screen.blit(title, (dialog_x + 20, dialog_y + 15))
    
    pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
    piece_symbols = {
        chess.QUEEN: "♕" if color == chess.WHITE else "♛",
        chess.ROOK: "♖" if color == chess.WHITE else "♜",
        chess.BISHOP: "♗" if color == chess.WHITE else "♝",
        chess.KNIGHT: "♘" if color == chess.WHITE else "♞"
    }
    
    button_width = 80
    button_height = 80
    button_y = dialog_y + 55
    spacing = 10
    start_x = dialog_x + (dialog_width - (button_width * 4 + spacing * 3)) // 2
    
    buttons = []
    for i, piece_type in enumerate(pieces):
        button_x = start_x + i * (button_width + spacing)
        rect = pygame.Rect(button_x, button_y, button_width, button_height)
        buttons.append((rect, piece_type))
        
        pygame.draw.rect(screen, (100, 100, 100), rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)
        
        piece_text = FONT.render(piece_symbols[piece_type], True, (255, 255, 255))
        text_rect = piece_text.get_rect(center=rect.center)
        screen.blit(piece_text, text_rect)
    
    return buttons


def draw_board(screen, board, selected_square=None, last_move=None, in_check=False, game_over=False, legal_moves=None, check_flash_timer=0, game_over_fade=0, animating_move=None, animation_progress=0.0):
    for rank in range(8):
        for file in range(8):
            color = LIGHT if (rank + file) % 2 == 0 else DARK
            rect = pygame.Rect(file * SQ_SIZE, rank * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            pygame.draw.rect(screen, color, rect)

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
            pygame.draw.circle(screen, LEGAL_MOVE_COLOR[:3], center, SQ_SIZE // 8)

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            if animating_move and square == animating_move.from_square:
                continue
            if animating_move and square == animating_move.to_square and board.is_capture(animating_move):
                continue
            symbol = piece.symbol()
            rank = 7 - chess.square_rank(square)
            file = chess.square_file(square)
            rect = pygame.Rect(file * SQ_SIZE, rank * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            if piece.color == chess.WHITE:
                piece_color = (200, 200, 200)
                outline_color = (0, 0, 0)
            else:
                piece_color = (50, 50, 50)
                outline_color = (255, 255, 255)
            text = FONT.render(PIECE_SYMBOLS[symbol], True, outline_color)
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                text_rect = text.get_rect(center=(rect.centerx + dx, rect.centery + dy))
                screen.blit(text, text_rect)
            text = FONT.render(PIECE_SYMBOLS[symbol], True, piece_color)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

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
            if piece.color == chess.WHITE:
                piece_color = (200, 200, 200)
                outline_color = (0, 0, 0)
            else:
                piece_color = (50, 50, 50)
                outline_color = (255, 255, 255)
            text = FONT.render(PIECE_SYMBOLS[symbol], True, outline_color)
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                screen.blit(text, (center_x - text.get_width()//2 + dx, center_y - text.get_height()//2 + dy))
            text = FONT.render(PIECE_SYMBOLS[symbol], True, piece_color)
            screen.blit(text, (center_x - text.get_width()//2, center_y - text.get_height()//2))

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
    promotion_dialog_active = False
    promotion_move = None
    running = True

    while running:
        clock.tick(60)
        if board.is_check():
            check_flash_timer += 1
        else:
            check_flash_timer = 0
        if board.is_game_over() and game_over_fade < 255:
            game_over_fade += 5
        if animating_move and not promotion_dialog_active:
            animation_progress += 0.05
            if animation_progress >= 1.0:
                board.push(animating_move)
                last_move = animating_move
                animating_move = None
                animation_progress = 0.0
                if not board.is_game_over() and not board.turn:
                    bot_move_result = None
                    bot_thread = threading.Thread(target=compute_bot_move, args=(board.copy(), 3))
                    bot_thread.start()
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
                    promotion_dialog_active = False
                    promotion_move = None
                    if bot_thread:
                        bot_thread.join()
                    bot_thread = None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if promotion_dialog_active:
                    # Check if clicked on promotion dialog button
                    promotion_buttons = draw_promotion_dialog(screen, board.turn)
                    for rect, piece_type in promotion_buttons:
                        if rect.collidepoint(event.pos):
                            # Create the promotion move with selected piece
                            move_with_promotion = chess.Move(promotion_move.from_square, promotion_move.to_square, promotion=piece_type)
                            animating_move = move_with_promotion
                            animation_progress = 0.0
                            promotion_dialog_active = False
                            promotion_move = None
                            selected_square = None
                            legal_moves = None
                            break
                elif not board.is_game_over() and not animating_move:
                    sq = square_from_mouse(event.pos)
                    if sq is not None:
                        if selected_square is None:
                            if board.piece_at(sq) and board.piece_at(sq).color == chess.WHITE:
                                selected_square = sq
                                legal_moves = [move.to_square for move in board.legal_moves if move.from_square == sq]
                        else:
                            move = chess.Move(selected_square, sq)
                            # Check if this is a pawn promotion
                            piece = board.piece_at(selected_square)
                            if piece and piece.piece_type == chess.PAWN:
                                to_rank = chess.square_rank(sq)
                                if (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0):
                                    # This is a promotion - show dialog
                                    if move in board.legal_moves or any(m.from_square == selected_square and m.to_square == sq for m in board.legal_moves):
                                        promotion_dialog_active = True
                                        promotion_move = move
                                        continue
                            
                            if move in board.legal_moves:
                                animating_move = move
                                animation_progress = 0.0
                                selected_square = None
                                legal_moves = None
                            else:
                                selected_square = None
                                legal_moves = None

        draw_board(screen, board, selected_square, last_move, board.is_check(), board.is_game_over(), legal_moves, check_flash_timer, game_over_fade, animating_move, animation_progress)
        
        if promotion_dialog_active:
            draw_promotion_dialog(screen, board.turn)
        
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run_gui()
