import pygame
import random
import sys

# ============== 配置部分 ==============
# 网格大小（单位：格子数量）
GRID_WIDTH = 60
GRID_HEIGHT = 40

# 每个格子的像素大小
CELL_SIZE = 15

# 活细胞/死细胞 颜色
COLOR_ALIVE = (0, 255, 0)  # 绿色
COLOR_DEAD = (0, 0, 0)  # 黑色背景

# 背景色（画网格线）
COLOR_GRID = (40, 40, 40)

# 帧率
FPS = 10

# 初始存活概率
PROB_LIVE = 0.2


# ======================================


def create_board(width, height, prob_live=0.2):
    """
    随机创建一个细胞网格（board）。
    其中 board[row][col] = 1 表示活细胞，0 表示死细胞。
    """
    board = []
    for _ in range(height):
        row = [1 if random.random() < prob_live else 0 for _ in range(width)]
        board.append(row)
    return board


def count_neighbors(board, x, y):
    """
    计算位置 (x, y) 的细胞周围 8 个邻居的存活数。
    board[y][x] 表示第 y 行, 第 x 列。
    """
    height = len(board)
    width = len(board[0])
    neighbors = 0
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue  # 排除自身
            nx = x + dx
            ny = y + dy
            if 0 <= nx < width and 0 <= ny < height:
                neighbors += board[ny][nx]
    return neighbors


def next_generation(board):
    """
    根据当前网格 board 计算下一代状态，并返回新的网格。
    经典生命游戏规则：
      1. 孤独死亡: 存活细胞, 周围 <2 个活邻居 → 死
      2. 维持现状: 存活细胞, 周围 2 or 3 个活邻居 → 继续活
      3. 拥挤死亡: 存活细胞, 周围 >3 个活邻居 → 死
      4. 繁殖: 死细胞, 周围 =3 个活邻居 → 活
    """
    height = len(board)
    width = len(board[0])
    new_board = [[0] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            live_neighbors = count_neighbors(board, x, y)
            if board[y][x] == 1:
                # 存活细胞
                if live_neighbors < 2:
                    new_board[y][x] = 0  # 孤独死
                elif live_neighbors in [2, 3]:
                    new_board[y][x] = 1  # 继续活
                else:
                    new_board[y][x] = 0  # 拥挤死
            else:
                # 死细胞
                if live_neighbors == 3:
                    new_board[y][x] = 1  # 繁殖
    return new_board


def draw_board(screen, board):
    """
    使用 pygame 在 screen 上绘制当前网格状态。
    """
    screen.fill(COLOR_DEAD)  # 整个背景先涂黑
    height = len(board)
    width = len(board[0])
    for y in range(height):
        for x in range(width):
            if board[y][x] == 1:  # 活细胞
                rect = (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, COLOR_ALIVE, rect)

    # 画网格线（可选）
    for y in range(height):
        pygame.draw.line(
            screen,
            COLOR_GRID,
            (0, y * CELL_SIZE),
            (width * CELL_SIZE, y * CELL_SIZE)
        )
    for x in range(width):
        pygame.draw.line(
            screen,
            COLOR_GRID,
            (x * CELL_SIZE, 0),
            (x * CELL_SIZE, height * CELL_SIZE)
        )


def main():
    pygame.init()
    screen_width = GRID_WIDTH * CELL_SIZE
    screen_height = GRID_HEIGHT * CELL_SIZE
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Conway's Game of Life - Pygame")

    clock = pygame.time.Clock()

    # 创建初始网格
    board = create_board(GRID_WIDTH, GRID_HEIGHT, PROB_LIVE)

    paused = False  # 是否暂停

    while True:
        clock.tick(FPS)
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_SPACE:
                    # 切换暂停状态
                    paused = not paused
                elif event.key == pygame.K_r:
                    # 重新随机初始化
                    board = create_board(GRID_WIDTH, GRID_HEIGHT, PROB_LIVE)
                elif event.key == pygame.K_n:
                    # 单步前进一代（仅在暂停时有用）
                    if paused:
                        board = next_generation(board)

            # ========== 新增：鼠标点击，切换细胞生死状态 ==========
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()  # 鼠标点击的像素坐标
                x = mx // CELL_SIZE
                y = my // CELL_SIZE
                # 确保没点到边缘之外
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    # 切换生死：若是 0（死），改 1（生）；若是 1（生），改 0（死）
                    board[y][x] = 1 - board[y][x]
            # ========== 新增结束 ==========

        # 如果没暂停，就演化到下一代
        if not paused:
            board = next_generation(board)

        # 绘制
        draw_board(screen, board)
        pygame.display.flip()


if __name__ == "__main__":
    main()
