# # labyrinthos/components/strategy_core/dp_planner.py


import collections
import sys

sys.setrecursionlimit(10000)


def dp_planner(env):
    """
    状态: (x, y, boss_flag, resource_mask) - 位置、是否经过BOSS、资源点收集状态
    """
    # 获取迷宫尺寸
    width = env.width
    height = env.height
    
    # 寻找起点和终点
    start_pos, end_pos = None, None
    for y in range(height):
        for x in range(width):
            cell = env.get_cell(x, y)
            if cell == env.START:
                start_pos = (x, y)
            elif cell == env.EXIT:
                end_pos = (x, y)
    
    if start_pos is None or end_pos is None:
        print("错误: 迷宫缺少起点或终点")
        return None, None
    
    # 收集所有资源点（金币和陷阱）和BOSS点
    resource_points = {}  # {(x, y): (index, type)}
    boss_points = set()
    n_resources = 0
    
    for y in range(height):
        for x in range(width):
            cell = env.get_cell(x, y)
            if cell == env.GOLD or cell == env.TRAP:
                resource_points[(x, y)] = (n_resources, cell)
                n_resources += 1
            elif cell == env.BOSS:
                boss_points.add((x, y))
    
    # 状态表示: (x, y, boss_flag, resource_mask)
    # 使用字典存储每个状态的最佳金币数和前驱状态
    dp = {}
    pre = {}
    
    # 初始化起点状态
    start_x, start_y = start_pos
    start_boss_flag = 1 if start_pos in boss_points else 0
    start_mask = 0
    
    # 如果起点是资源点，收集它
    if start_pos in resource_points:
        idx, res_type = resource_points[start_pos]
        start_mask |= (1 << idx)
        start_coins = 5 if res_type == env.GOLD else -3
    else:
        start_coins = 0
    
    start_state = (start_x, start_y, start_boss_flag, start_mask)
    dp[start_state] = start_coins
    pre[start_state] = None
    
    # 创建队列并加入起点状态
    queue = collections.deque([start_state])
    
    # 移动方向: 右, 左, 下, 上
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    
    # 记录最佳终点状态
    best_end_state = None
    best_coins = -10**9
    
    while queue:
        state = queue.popleft()
        x, y, boss_flag, resource_mask = state
        current_coins = dp[state]
        
        # 如果到达终点，检查是否满足BOSS条件并更新最佳解
        if (x, y) == end_pos and boss_flag == 1:
            if current_coins > best_coins:
                best_coins = current_coins
                best_end_state = state
            continue
        
        # 尝试四个方向移动
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            # 检查边界
            if not (0 <= nx < width and 0 <= ny < height):
                continue
                
            # 跳过墙壁
            if env.get_cell(nx, ny) == env.WALL:
                continue
            
            # 计算新位置的BOSS标志
            new_boss_flag = boss_flag
            if (nx, ny) in boss_points and boss_flag == 0:
                new_boss_flag = 1
            
            # 计算新位置的资源状态和金币变化
            new_mask = resource_mask
            coin_delta = 0
            
            # 如果新位置是未收集的资源点
            if (nx, ny) in resource_points:
                idx, res_type = resource_points[(nx, ny)]
                # 检查是否已收集过该资源点
                if not (resource_mask & (1 << idx)):
                    new_mask |= (1 << idx)
                    coin_delta = 5 if res_type == env.GOLD else -3
            
            new_coins = current_coins + coin_delta
            new_state = (nx, ny, new_boss_flag, new_mask)
            
            # 如果新状态更优，更新状态
            if new_state not in dp or new_coins > dp[new_state]:
                dp[new_state] = new_coins
                pre[new_state] = state
                queue.append(new_state)
    
    if best_end_state is None:
        print("错误: 未找到有效路径")
        return None, None
    
    # 回溯重建路径
    path = []
    state = best_end_state
    
    while state is not None:
        x, y, _, _ = state
        path.append((x, y))
        state = pre[state]
    
    path.reverse()
    return best_coins, path


def find_optimal_path_dp(env):
    final_gold, path = dp_planner(env)
    if final_gold is not None:
        print(f"计算完成！最大可获得金币: {final_gold}")
        print(f"最优路径: {path}")
    return final_gold, path

