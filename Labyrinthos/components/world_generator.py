# labyrinthos/components/world_generator.py
import sys
import os
import random

# 添加项目根目录到模块搜索路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from environment import Environment
from io_handler import load_maze_from_json


def load_world_from_file(env: Environment, filename: str) -> bool:
    """
    从指定的JSON文件加载迷宫数据到Environment对象中。
    """
    map_data = load_maze_from_json(filename)
    if not map_data:
        return False
    
    grid = map_data.get("grid")
    
    if not grid:
        grid = map_data.get("maze")
        
        
    metadata = map_data.get("metadata", {})
    width = metadata.get("width", len(grid[0]) if grid and grid[0] else 0)
    height = metadata.get("height", len(grid) if grid else 0)

    if not grid or not width or not height:
        print("错误: 地图文件数据格式不正确或已损坏。")
        return False
        
    env.width = width
    env.height = height
    env.grid = grid
    
    return True

# --- 主生成函数，现在只生成无环迷宫 ---
def generate_world(env: Environment,difficulty:str):
    """
    主函数，使用分治法生成一个完美的、无环的迷宫。
    任意两点之间有且只有一条通路。
    """
    # 1. 初始化迷宫内部为通路，这是“在空白区域建墙”的前提
    for y in range(1, env.height - 1):
        for x in range(1, env.width - 1):
            env.set_cell(x, y, env.PATH)

    # 2. 使用能保证无环的分治法来建造墙壁
    _recursive_division_perfect(env, 0, 0, env.width-1, env.height-1)
    
    # 3. 计算并放置元素
    _calculate_and_place_elements(env,difficulty)

# --- 核心的完美迷宫生成算法 ---
def _recursive_division_perfect(env: Environment, x: int, y: int, width: int, height: int):
    """
    一个精确的分治算法，用于生成完美的、无环的迷宫。
    """
    if width < 3 or height < 3:
        return

    is_horizontal = height > width
    if height == width:
        is_horizontal = random.choice([True, False])

    if is_horizontal:
        wall_y = y + random.randrange(2, height, 2)
        passage_x = x + random.randrange(1, width, 2)
        for i in range(x, x + width + 1):
            if i != passage_x:
                env.set_cell(i, wall_y, env.WALL)
        _recursive_division_perfect(env, x, y, width, wall_y - y)
        _recursive_division_perfect(env, x, wall_y, width, height - (wall_y - y))
    else:
        wall_x = x + random.randrange(2, width, 2)
        passage_y = y + random.randrange(1, height, 2)
        for i in range(y, y + height + 1):
            if i != passage_y:
                env.set_cell(wall_x, i, env.WALL)
        _recursive_division_perfect(env, x, y, wall_x - x, height)
        _recursive_division_perfect(env, wall_x, y, width - (wall_x - x), height)

# --- 元素计算与放置部分 ---
def _calculate_and_place_elements(env: Environment,difficulty:str):
    """统一计算并放置迷宫元素"""
    total_paths = len(env.get_all_paths())
    maze_area = env.width * env.height
    
    if difficulty=='简单':
        # if maze_area < 25*25: num_boss = 1
        # elif maze_area < 50*50: num_boss = 2
        # elif maze_area < 80*80: num_boss = 3
        # else: num_boss = 4
        num_boss=1
            
        num_lockers = num_boss
        total_interest_points = total_paths // 20
        remaining_slots = total_interest_points - num_boss - num_lockers
        
        if remaining_slots > 2:
            num_gold = int(remaining_slots * 0.75)
            num_traps = remaining_slots - num_gold
        else:
            num_gold = max(1, total_paths // 100)
            num_traps = max(1, total_paths // 150)
    else:
        # # num_gold, num_traps, num_lockers, num_boss =15,10,4,4
        # if maze_area < 25*25: num_boss = 2
        # elif maze_area < 50*50: num_boss = 3
        # elif maze_area < 80*80: num_boss = 4
        # else: num_boss = 5
        num_boss=1
            
        num_lockers = num_boss
        total_interest_points = total_paths // 10
        remaining_slots = total_interest_points - num_boss - num_lockers
        
        if remaining_slots > 2:
            num_gold = int(remaining_slots * 0.75)
            num_traps = remaining_slots - num_gold
        else:
            num_gold = max(1, total_paths // 100)
            num_traps = max(1, total_paths // 150)
    
    print(f"--- 地图生成参数 (无环模式) ---")
    print(f"尺寸: {env.width}x{env.height}, BOSS: {num_boss}, 机关: {num_lockers}, 金币: {num_gold}, 陷阱: {num_traps}")
    
    _place_elements(env, num_gold, num_traps, num_lockers, num_boss)

def _place_elements(env: Environment, num_gold: int, num_traps: int, num_lockers: int, num_boss: int):
    """在迷宫通路中放置游戏元素"""
    all_paths = env.get_all_paths()
    if not all_paths: return
    
    total_elements_needed = 2 + num_gold + num_traps + num_lockers + num_boss
    if len(all_paths) < total_elements_needed:
        shortage = total_elements_needed - len(all_paths)
        removed_traps = min(num_traps, shortage); num_traps -= removed_traps; shortage -= removed_traps
        removed_gold = min(num_gold, shortage); num_gold -= removed_gold
        print(f"警告: 通路不足，元素数量已自动减少。")

    random.shuffle(all_paths)
    start_pos = all_paths.pop()
    env.set_cell(start_pos[0], start_pos[1], env.START)
    
    exit_pos = max(all_paths, key=lambda pos: abs(pos[0]-start_pos[0]) + abs(pos[1]-start_pos[1]), default=None)
    if exit_pos:
        env.set_cell(exit_pos[0], exit_pos[1], env.EXIT)
        all_paths.remove(exit_pos)
    
    def place_element(element_char, count):
        for _ in range(count):
            if all_paths:
                env.set_cell(*all_paths.pop(), element_char)
    
    place_element(env.BOSS, num_boss)
    place_element(env.LOCKER, num_lockers)
    place_element(env.GOLD, num_gold)
    place_element(env.TRAP, num_traps)

