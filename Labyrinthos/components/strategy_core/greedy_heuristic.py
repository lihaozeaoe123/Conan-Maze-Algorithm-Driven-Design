# # labyrinthos/components/strategy_core/greedy_heuristic.py
# from typing import Tuple, List

# def get_greedy_move(vision: List[List[str]], agent_stamina: int, bosses_defeated: bool) -> Tuple[int, int]:
#     """
#     根据3x3视野，使用贪心策略决定下一步的最佳移动方向。

#     Args:
#         vision (List[List[str]]): 3x3的视野网格，中心点是玩家。
#         agent_stamina (int): Agent当前的体力值。
#         bosses_defeated (bool): 是否所有BOSS都已被击败。

#     Returns:
#         Tuple[int, int]: 最佳移动方向(dx, dy)。如果没有好的选择，返回(0, 0)。
#     """
    
#     # 1. 定义性价比估值表
#     # 这个估值代表了踩上一个格子能获得的“即时贪心收益”
#     value_map = {
#         'G': 10,   # 金币
#         'T': -25,  # 陷阱
#         'L': 35,   # 机关 (假设解谜收益大于成本，并且道具很有价值)
#         'B': 10,   # BOSS (假设胜利收益大于战斗成本)
#         'E': 1000 if bosses_defeated else -100, # 只有在打完BOSS后，终点才有巨大吸引力
#         'S': -5,   # 不鼓励回到起点
#         ' ': 0,    # 空地
#         '#': -float('inf') # 墙壁，不可达
#     }

#     best_move = (0, 0)
#     max_score = -float('inf')

#     # 2. 遍历3x3视野内的8个邻居
#     # (dx, dy) 是相对于玩家的偏移量
#     for dy in range(-1, 2):
#         for dx in range(-1, 2):
#             # 跳过中心点（玩家自己）
#             if dx == 0 and dy == 0:
#                 continue

#             # 将偏移量转换为vision数组的索引
#             # vision[1][1] 是玩家位置
#             vision_y, vision_x = 1 + dy, 1 + dx
            
#             cell = vision[vision_y][vision_x]
            
#             # 3. 计算性价比得分
#             # 基础移动成本
#             move_cost = 1 
            
#             # 如果是斜向移动，成本可以设置得更高一些 (可选)
#             # if abs(dx) + abs(dy) == 2:
#             #     move_cost = 1.414 

#             # 获取格子的估值
#             cell_value = value_map.get(cell, 0) # 对未知格子估值为0
            
#             # 性价比 = 预期收益 - 移动成本
#             score = cell_value - move_cost
            
#             # 4. 更新最佳选择
#             if score > max_score:
#                 max_score = score
#                 best_move = (dx, dy)

#     # 5. 最终决策
#     # 如果最高分仍然是负的（比如周围全是陷阱），AI可能会选择不动
#     if max_score < 0:
#         # 在这种情况下，可以增加一个“探索未知”的逻辑，
#         # 但目前我们先让它停在原地
#         # return (0, 0)
#         pass # 我们依然返回得分最高的那个负分选择，让它“两害相权取其轻”

#     print(f"贪心决策: 视野内最佳移动 {best_move}，得分 {max_score:.2f}")
#     return best_move


# # --- 独立测试模块 ---
# if __name__ == '__main__':
#     print("--- 测试贪心算法决策模块 ---")

#     # 样例1: 右边是金币，最佳选择是向右
#     vision1 = [
#         ['#', ' ', '#'],
#         [' ', 'P', 'G'], # P代表玩家
#         ['#', ' ', '#']
#     ]
#     move1 = get_greedy_move(vision1, 300, bosses_defeated=False)
#     print(f"测试1 - 视野: {vision1}, 决策: {move1} (预期: (1, 0))")
#     assert move1 == (1, 0)
#     print("-" * 20)

#     # 样例2: 周围有陷阱和机关，机关的价值更高
#     vision2 = [
#         ['L', '#', ' '],
#         [' ', 'P', 'T'],
#         [' ', ' ', ' ']
#     ]
#     move2 = get_greedy_move(vision2, 300, bosses_defeated=False)
#     print(f"测试2 - 视野: {vision2}, 决策: {move2} (预期: (-1, -1))")
#     assert move2 == (-1, -1)
#     print("-" * 20)
    
#     # 样例3: BOSS已清空，终点E的吸引力变得巨大
#     vision3 = [
#         [' ', ' ', ' '],
#         ['E', 'P', ' '],
#         [' ', 'G', ' ']
#     ]
#     move3 = get_greedy_move(vision3, 300, bosses_defeated=True)
#     print(f"测试3 - 视野: {vision3}, 决策: {move3} (预期: (-1, 0))")
#     assert move3 == (-1, 0)
#     print("-" * 20)
    
#     # 样例4: BOSS未清空，终点E是负收益
#     vision4 = [
#         [' ', ' ', ' '],
#         ['E', 'P', ' '],
#         [' ', 'G', ' ']
#     ]
#     move4 = get_greedy_move(vision4, 300, bosses_defeated=False)
#     print(f"测试4 - 视野: {vision4}, 决策: {move4} (预期: (0, 1))")
#     assert move4 == (0, 1) # 应该选择金币而不是终点
#     print("-" * 20)


# labyrinthos/components/strategy_core/greedy_heuristic.py
from typing import Tuple, List, Set

def get_smarter_greedy_move(
    vision: List[List[str]],
    visited_map: Set[Tuple[int, int]],
    current_pos: Tuple[int, int],
    tabu_list: List[Tuple[int, int]], # <-- 新增：禁忌列表
    bosses_defeated: bool
) -> Tuple[int, int]:
    """
    一个更智能的贪心算法，结合了禁忌列表和探索欲望来避免死循环。
    """
    value_map = {
        'G': 50, 'T': -100, 'L': 60, 'B': 40,
        'E': 1000 if bosses_defeated else -200,
        'S': -5, ' ': 0, '#': -float('inf')
    }

    best_move = (0, 0)
    max_score = -float('inf')

    # 遍历3x3视野内的8个邻居
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dx == 0 and dy == 0: continue
            
            cell = vision[1 + dy][1 + dx]
            if cell == '#': continue

            neighbor_world_pos = (current_pos[0] + dx, current_pos[1] + dy)
            
            # --- 核心修改：新的、包含三层逻辑的评分函数 ---
            score = value_map.get(cell, 0) - 1

            # 1. 探索奖励：优先探索未知区域
            if neighbor_world_pos not in visited_map:
                score += 5
            
            # 2. 禁忌惩罚：强烈避免走回头路
            if neighbor_world_pos in tabu_list:
                # 给予一个巨大的负分，但不是无穷大，以防无路可走
                score -= 500 

            if score > max_score:
                max_score = score
                best_move = (dx, dy)
            elif score == max_score and (abs(dx) + abs(dy) < abs(best_move[0]) + abs(best_move[1])):
                best_move = (dx, dy)
    
    print(f"智能贪心决策: 最佳移动 {best_move}，得分 {max_score:.2f}")
    return best_move