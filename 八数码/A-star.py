import heapq
from copy import deepcopy
import pygame
import sys


def function_heuristic(state, goal_state):
    diff = 0
    for i in range(3):
        for j in range(3):
            val = state[i][j]
            if val != 0:
                for gi in range(3):
                    for gj in range(3):
                        if goal_state[gi][gj] == val:
                            diff += abs(gi - i) + abs(gj - j)
                            break
    return diff


def moves(state, g):
    x, y = None, None
    for i in range(3):
        for j in range(3):
            if state[i][j] == 0:
                x, y = i, j
                break

    arr = []
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 3 and 0 <= ny < 3:
            new_state = deepcopy(state)
            new_state[x][y], new_state[nx][ny] = new_state[nx][ny], new_state[x][y]
            arr.append((new_state, g + 1))
    return arr


def A_star(start_state, goal_state):
    h = function_heuristic(start_state, goal_state)
    counter = 0
    open_set = [(h, counter, 0, start_state)]
    closed_set = set()
    origin = {}

    while open_set:
        _, _, g, current_state = heapq.heappop(open_set)
        current_tuple = tuple(map(tuple, current_state))

        if current_tuple in closed_set:
            continue

        if current_state == goal_state:
            path = []
            state = current_tuple
            while state in origin:
                path.append(state)
                state = origin[state]
            path.append(tuple(map(tuple, start_state)))
            return path[::-1]

        closed_set.add(current_tuple)

        for new_state, new_g in moves(current_state, g):
            new_tuple = tuple(map(tuple, new_state))
            if new_tuple not in closed_set:
                new_h = function_heuristic(new_state, goal_state)
                new_f = new_g + new_h
                counter += 1
                heapq.heappush(open_set, (new_f, counter, new_g, new_state))
                origin[new_tuple] = current_tuple

    return None


# --- Pygame 可视化 ---

map_size = 3
cell_size = 150
info_bar_height = 60
width = cell_size * map_size
height = cell_size * map_size + info_bar_height

BG_COLOR = (240, 240, 245)
LINE_COLOR = (50, 50, 50)
TILE_COLOR = (70, 130, 180)
TEXT_COLOR = (255, 255, 255)
BLANK_COLOR = (220, 220, 225)
INFO_BG = (60, 60, 80)
INFO_TEXT = (255, 255, 255)


def draw_grid(screen, grid, font_tile):
    for i in range(3):
        for j in range(3):
            rect = pygame.Rect(j * cell_size, i * cell_size, cell_size, cell_size)
            if grid[i][j] == 0:
                pygame.draw.rect(screen, BLANK_COLOR, rect)
            else:
                pygame.draw.rect(screen, TILE_COLOR, rect)
                num_surf = font_tile.render(str(grid[i][j]), True, TEXT_COLOR)
                text_rect = num_surf.get_rect(center=rect.center)
                screen.blit(num_surf, text_rect)

    for i in range(4):
        pygame.draw.line(screen, LINE_COLOR, (i * cell_size, 0),
                         (i * cell_size, cell_size * 3), 3)
        pygame.draw.line(screen, LINE_COLOR, (0, i * cell_size),
                         (cell_size * 3, i * cell_size), 3)


def draw_info(screen, step, total_steps, font_info):
    info_rect = pygame.Rect(0, cell_size * 3, width, info_bar_height)
    pygame.draw.rect(screen, INFO_BG, info_rect)
    text = f"步:{step}/{total_steps}  空格:播放/暂停  左右:单步  ESC:退出"
    text_surf = font_info.render(text, True, INFO_TEXT)
    text_rect = text_surf.get_rect(center=info_rect.center)
    screen.blit(text_surf, text_rect)


def main():
    start_state = [
        [2, 8, 3],
        [1, 6, 4],
        [7, 0, 5]
    ]
    goal_state = [
        [1, 2, 3],
        [8, 0, 4],
        [7, 6, 5]
    ]

    print("正在求解...")
    path = A_star(start_state, goal_state)
    if path is None:
        print("无解！")
        return

    total_steps = len(path) - 1
    print(f"找到解法，共 {total_steps} 步")
    for i, state in enumerate(path):
        print(f"\n第 {i} 步:")
        for row in state:
            print(list(row))

    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("八数码问题 - A*算法")

    font_tile = pygame.font.SysFont('Arial', 60, bold=True)
    font_info = pygame.font.SysFont('SimHei', 20)

    current_step = 0
    paused = True
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_RIGHT:
                    if current_step < total_steps:
                        current_step += 1
                    paused = True
                elif event.key == pygame.K_LEFT:
                    if current_step > 0:
                        current_step -= 1
                    paused = True

        if not paused:
            if current_step < total_steps:
                current_step += 1
            else:
                paused = True

        screen.fill(BG_COLOR)
        grid = [list(row) for row in path[current_step]]
        draw_grid(screen, grid, font_tile)
        draw_info(screen, current_step, total_steps, font_info)
        pygame.display.flip()
        clock.tick(2)


if __name__ == "__main__":
    main()
