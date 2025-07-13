# # import heapq
# import json

# # # def boss_battle_solver(data):
# # #     B = data["B"]
# # #     skills = data["PlayerSkills"]
# # #     num_boss = len(B)

# # #     max_dmg = max(s[0] for s in skills)
# # #     effective_dps = max([d / (cd + 1) for d, cd in skills])

# # #     # 初始状态
# # #     init_state = (0, 0, tuple(B), tuple([0] * len(skills)), [])

# # #     # 优先队列 (估值, g=turns, boss_index, boss_hp_tuple, cooldowns, actions)
# # #     heap = []
# # #     heapq.heappush(heap, (0, *init_state))

# # #     visited = dict()  # 状态 -> 最小回合数
# # #     min_turns = float('inf')
# # #     best_actions = []

# # #     while heap:
# # #         f, turns, boss_index, boss_hp_tuple, cooldowns, actions = heapq.heappop(heap)

# # #         # 检查是否优于当前最优解
# # #         if turns >= min_turns:
# # #             continue

# # #         state_key = (boss_index, boss_hp_tuple, cooldowns)
# # #         if state_key in visited and visited[state_key] <= turns:
# # #             continue
# # #         visited[state_key] = turns

# # #         # 成功击败所有BOSS
# # #         if boss_index == num_boss:
# # #             if turns < min_turns:
# # #                 min_turns = turns
# # #                 best_actions = actions
# # #             continue

# # #         curr_hp = boss_hp_tuple[boss_index]

# # #         # 技能按伤害从大到小排序，增加剪枝机会
# # #         for i, (dmg, cd) in sorted(enumerate(skills), key=lambda x: -x[1][0]):
# # #             if cooldowns[i] == 0:
# # #                 next_hp = curr_hp - dmg
# # #                 next_boss_index = boss_index
# # #                 next_boss_hp = list(boss_hp_tuple)

# # #                 if next_hp <= 0:
# # #                     next_boss_index += 1
# # #                     if next_boss_index < num_boss:
# # #                         next_boss_hp[next_boss_index] = B[next_boss_index]
# # #                     next_hp = 0
# # #                 next_boss_hp[boss_index] = max(0, next_hp)

# # #                 next_cooldowns = tuple([max(c-1, 0) for c in cooldowns])
# # #                 next_cooldowns = list(next_cooldowns)
# # #                 next_cooldowns[i] = cd
# # #                 next_cooldowns = tuple(next_cooldowns)

# # #                 remaining_hp = sum(next_boss_hp[next_boss_index:])
# # #                 h = int((remaining_hp + effective_dps - 1) // effective_dps)  # 更细致估算
# # #                 g = turns + 1
# # #                 fn = g + h

# # #                 heapq.heappush(heap, (
# # #                     fn, g, next_boss_index, tuple(next_boss_hp), next_cooldowns, actions + [i]
# # #                 ))

# # #     return {"min_turns": min_turns, "actions": best_actions}

# import heapq
# import math

# def boss_battle_solver(data):
#     B = data["B"]
#     skills = data["PlayerSkills"]
#     num_boss = len(B)

#     max_dmg = max(s[0] for s in skills)
#     effective_dps = max([d / (cd + 1) for d, cd in skills])

#     # 初始状态：估值f, 回合数g, 当前BOSS索引, 当前HP列表, 冷却状态, 技能序列
#     init_state = (0, 0, 0, tuple(B), tuple([0] * len(skills)), [])

#     heap = []
#     heapq.heappush(heap, init_state)

#     visited = {}
#     min_turns = float('inf')
#     best_actions = []

#     while heap:
#         f, turns, boss_index, boss_hp, cooldowns, actions = heapq.heappop(heap)

#         if turns >= min_turns:
#             continue

#         state_key = (boss_index, boss_hp, cooldowns)
#         if state_key in visited and visited[state_key] <= turns:
#             continue
#         visited[state_key] = turns

#         # 胜利条件：所有 BOSS 被按顺序打死
#         if boss_index == num_boss:
#             if turns < min_turns:
#                 min_turns = turns
#                 best_actions = actions
#             continue

#         # 只允许攻击当前 BOSS（boss_index）
#         curr_hp = boss_hp[boss_index]

#         for i, (dmg, cd) in sorted(enumerate(skills), key=lambda x: -x[1][0]):
#             if cooldowns[i] == 0:
#                 # 模拟攻击当前BOSS
#                 new_hp_list = list(boss_hp)
#                 new_hp_list[boss_index] = max(0, curr_hp - dmg)

#                 # 冷却更新
#                 new_cooldowns = [max(c - 1, 0) for c in cooldowns]
#                 new_cooldowns[i] = cd

#                 # 如果当前BOSS死了，则前进
#                 new_boss_index = boss_index
#                 if new_hp_list[boss_index] == 0:
#                     new_boss_index += 1

#                 # 估值函数
#                 remaining_hp = sum(new_hp_list[new_boss_index:]) + (new_hp_list[boss_index] if new_boss_index < num_boss else 0)
#                 h = int((remaining_hp + effective_dps - 1) // effective_dps)
#                 g = turns + 1
#                 fn = g + h

#                 heapq.heappush(heap, (
#                     fn, g, new_boss_index, tuple(new_hp_list), tuple(new_cooldowns), actions + [i]
#                 ))

#     return {"min_turns": min_turns, "actions": best_actions}


# def main():
#     import os
#     folder_path = r"D:\MyMazeGame\样例\BOSS战样例"
#     if not os.path.exists(folder_path):
#         print("路径不存在:", folder_path)
#         return

#     for filename in os.listdir(folder_path):
#         if filename.endswith(".json"):
#             full_path = os.path.join(folder_path, filename)
#             try:
#                 with open(full_path, "r", encoding="utf-8") as f:
#                     data = json.load(f)
#                 result = boss_battle_solver(data)
#                 print(f"文件名: {filename}")
#                 print(f"最小回合数: {result['min_turns']}")
#                 print(f"技能序列: {result['actions']}\n")
#             except Exception as e:
#                 print(f"文件读取或解析出错: {filename}，错误: {e}\n")
                
# if __name__=="__main__":
#     main()


import heapq
import json
import os

def estimate_remaining_turns(boss_hp_list, skills):
    total_hp = sum(boss_hp_list)
    avg_dps = sum(d for d, _ in skills)
    return total_hp / avg_dps if avg_dps > 0 else float('inf')

def boss_battle_solver(data):
    boss_list = data["B"]
    skills = data["PlayerSkills"]
    num_bosses = len(boss_list)

    heap = []
    init_boss_hps = tuple(boss_list)
    init_cooldowns = tuple(0 for _ in skills)
    heapq.heappush(heap, (estimate_remaining_turns(boss_list, skills), 0, 0, init_boss_hps, init_cooldowns, []))

    visited = set()
    best_turns = float('inf')
    best_actions = []
    best_verbose_log = []

    while heap:
        fn, turn, boss_index, boss_hps, cooldowns, actions = heapq.heappop(heap)
        state_key = (boss_index, boss_hps, cooldowns)
        if state_key in visited:
            continue
        visited.add(state_key)

        if boss_index >= num_bosses:
            if turn < best_turns:
                best_turns = turn
                best_actions = actions
                best_verbose_log = []  # Reset the log to reconstruct below
                current_boss_index = 0
                current_boss_hp = boss_list[current_boss_index]
                cooldowns_sim = [0] * len(skills)
                for t, skill_id in enumerate(actions):
                    damage, cd = skills[skill_id]
                    # Reduce cooldowns
                    for i in range(len(cooldowns_sim)):
                        if cooldowns_sim[i] > 0:
                            cooldowns_sim[i] -= 1
                    cooldowns_sim[skill_id] = cd

                    current_boss_hp -= damage
                    best_verbose_log.append(
                        f"Turn {t+1}: Use skill {skill_id} (Dmg={damage}, CD={cd}) -> BOSS {current_boss_index} HP now {max(current_boss_hp, 0)}"
                    )
                    if current_boss_hp <= 0 and current_boss_index < len(boss_list) - 1:
                        current_boss_index += 1
                        current_boss_hp = boss_list[current_boss_index]
            continue

        current_hp = boss_hps[boss_index]
        if current_hp <= 0:
            boss_index += 1
            continue

        for skill_id, (damage, cd) in enumerate(skills):
            if cooldowns[skill_id] > 0:
                continue

            new_boss_hps = list(boss_hps)
            new_boss_hps[boss_index] = max(0, new_boss_hps[boss_index] - damage)

            next_boss_index = boss_index
            if new_boss_hps[boss_index] == 0:
                next_boss_index += 1

            new_cooldowns = [max(0, c - 1) for c in cooldowns]
            new_cooldowns[skill_id] = cd

            new_actions = actions + [skill_id]
            next_turn = turn + 1

            h = estimate_remaining_turns(new_boss_hps[next_boss_index:], skills) if next_boss_index < num_bosses else 0
            f = next_turn + h

            if f >= best_turns:
                continue

            heapq.heappush(heap, (
                f, next_turn, next_boss_index, tuple(new_boss_hps), tuple(new_cooldowns), new_actions
            ))

    return {
        "min_turns": best_turns,
        "actions": best_actions,
        "verbose_log": best_verbose_log
    }


def main():
    # folder_path = r"D:\MyMazeGame\样例\BOSS战样例"
    folder_path = r"D:\\MyMazeGame\\TEST\\5_boss_test"
    if not os.path.exists(folder_path):
        print("路径不存在:", folder_path)
        return

    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            full_path = os.path.join(folder_path, filename)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                result = boss_battle_solver(data)
                for log in result['verbose_log']:
                    print(log)
                print(f"文件名: {filename}")
                print(f"最小回合数: {result['min_turns']}")
                print(f"技能序列: {result['actions']}\n")
            except Exception as e:
                print(f"文件读取或解析出错: {filename}，错误: {e}\n")

if __name__ == "__main__":
    main()
