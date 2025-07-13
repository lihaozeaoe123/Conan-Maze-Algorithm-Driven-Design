# labyrinthos/game_engine.py

import os
import pygame
import sys
import json
import tkinter as tk
from tkinter import filedialog


from agent import Agent
from environment import Environment
from renderer import Renderer
from camera import Camera
from io_handler import save_maze_to_json, get_saved_maps
from components.world_generator import generate_world, load_world_from_file
from components.strategy_core.dp_planner import find_optimal_path_dp
from components.strategy_core.puzzle_solver import PasswordSolver, hash_password
from components.strategy_core.combat_optimizer import boss_battle_solver 
from components.strategy_core.greedy_heuristic import get_smarter_greedy_move
from collections import defaultdict


# --- 最终修复版的InputBox ---
class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = text
        self.active = False
        try:
            self.font = pygame.font.SysFont('Consolas', 32)
        except pygame.error:
            self.font = pygame.font.Font(None, 32)
        self.txt_surface = self.font.render(text, True, (255, 255, 255))
        self.key_map = {pygame.K_0:'0', pygame.K_1:'1', pygame.K_2:'2', pygame.K_3:'3', pygame.K_4:'4', pygame.K_5:'5', pygame.K_6:'6', pygame.K_7:'7', pygame.K_8:'8', pygame.K_9:'9'}
        
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN and self.active:
            text_changed = False
            if event.key == pygame.K_RETURN:
                self.active = False
                self.color = self.color_inactive
            elif event.key == pygame.K_BACKSPACE:
                if self.text:
                    self.text = self.text[:-1]
                    text_changed = True
            elif event.key in self.key_map:
                self.text += self.key_map[event.key]
                text_changed = True
            
            if text_changed:
                self.txt_surface = self.font.render(self.text, True, (255, 255, 255))

    def update(self):
        self.rect.w = max(100, self.txt_surface.get_width() + 10)

    def draw(self, screen):
        pygame.draw.rect(screen, (30, 30, 60), self.rect)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)


# --- 最终整合版的游戏引擎 ---
class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen_width, self.screen_height = 800, 700
        self.hud_height = 80
        self.game_viewport_rect = pygame.Rect(0, self.hud_height, self.screen_width, self.screen_height - self.hud_height)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.game_state = 'MENU'
        self.running = True
        self.difficulty = '简单'
        
        # --- 新增：自动寻路相关属性 ---
        self.autoplay_mode = False
        self.autoplay_path = []
        self.autoplay_step = 0
        self.autoplay_timer = 0
        self.autoplay_speed = 0.1 # 每0.1秒走一步
        self.visited_map = set() # <-- 新增：用于贪心算法的全局地图
        self.tabu_list = [] # <-- 新增：禁忌列表
        self.tabu_list_size = 5 # <-- 禁忌列表的长度（记住最近5步）
        # 新增解密界面相关的属性
        self.puzzle_data = None
        self.puzzle_result = None
        self.puzzle_thinking = False
        # 新增：文件选择属性
        self.selected_boss_file = None
        self.selected_puzzle_file = None
        # self.boss_battle_thinking = False
        # --- 新增：BOSS战动画相关的属性 ---
        self.boss_battle_data = None     # 存储从JSON加载的战斗数据
        self.boss_battle_solution = None # 存储算法算出的最优解
        self.battle_turn_index = 0       # 当前播放到第几回合
        self.battle_animation_timer = 0  # 动画计时器
        self.battle_animation_speed = 0.4 # 每秒一个动画阶段
        self.battle_animation_phase = 'highlight' # 动画阶段: 'highlight' 或 'damage'
        self.battle_current_state = None # 存储战斗过程中的实时状态
        
        # --- 新增：加载并存储所有战斗图片 ---
        self.boss_images = self._load_images("boss", 6, (128, 128))
        self.skill_images = self._load_images("skill", 6, (80, 80))
        
        self._init_menu()
        # --- 新增：定义HUD上的按钮 ---
        # 按钮将位于HUD的右侧
        button_w, button_h = 120, 30
        margin = 10
        # 动态规划按钮
        self.dp_button_rect = pygame.Rect(
            self.screen_width - (button_w * 2 + margin * 3), # x
            (self.hud_height - button_h) // 2,                # y (垂直居中)
            button_w, button_h
        )
        # 贪心算法按钮
        self.greedy_button_rect = pygame.Rect(
            self.screen_width - (button_w + margin * 2),      # x
            (self.hud_height - button_h) // 2,                # y
            button_w, button_h
        )

        self.game_state = 'MENU'
        self.running = True
        self._init_menu()
    
    def _load_images(self, prefix, count, size):
        """通用图片加载函数"""
        images = []
        for i in range(count):
            path = os.path.join("assets", f"{prefix}{i}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                images.append(pygame.transform.scale(img, size))
            except pygame.error:
                print(f"警告: 无法加载图片 {path}")
                # 创建一个占位符图像
                placeholder = pygame.Surface(size, pygame.SRCALPHA)
                placeholder.fill((128, 128, 128, 100))
                images.append(placeholder)
        return images
    
    def _init_menu(self):
        pygame.display.set_caption("Labyrinthos - 设置")
        try:
            self.font = pygame.font.SysFont('SimHei', 50)
            self.small_font = pygame.font.SysFont('Microsoft YaHei', 28)
            self.button_font = pygame.font.SysFont('Microsoft YaHei', 20)
        except pygame.error:
            self.font = pygame.font.Font(None, 50)
            self.small_font = pygame.font.Font(None, 32)
            self.button_font = pygame.font.Font(None, 24)
        self.input_rows = InputBox(350, 200, 140, 32, "20")
        self.input_cols = InputBox(350, 250, 140, 32, "25")
        self.input_boxes = [self.input_rows, self.input_cols]
        self.difficulty_button_rect = pygame.Rect(300, 300, 200, 40)
        self.generate_button_rect = pygame.Rect(300, 360, 200, 50)
        self.load_button_rect = pygame.Rect(300, 430, 200, 50)
        # 新增：文件选择按钮
        self.select_boss_button_rect = pygame.Rect(300, 500, 200, 50)
        self.select_puzzle_button_rect = pygame.Rect(300, 560, 200, 50)
        self.error_message = ""
        self.env = self.agent = self.renderer = self.camera = None
        # 新增解密界面的UI元素
        self.think_button_rect = pygame.Rect(300, 250, 200, 50)
        self.puzzle_back_button_rect = pygame.Rect(300, 580, 200, 50)
        # # 新增BOSS战UI元素
        # self.start_battle_button_rect = pygame.Rect(300, 280, 200, 50)
        # self.battle_end_button_rect = pygame.Rect(300, 580, 200, 50)
        # --- 新增/修改按钮定义 ---
        self.battle_exit_button_rect = pygame.Rect(self.screen_width - 170, self.screen_height - 70, 150, 50)
        #继续上次
        # self.continue_button_rect = pygame.Rect(180, 120, 200, 50)
        self.continue_button_rect = pygame.Rect(300, 620, 200, 50)
        
    def _setup_game_screen_and_camera(self, map_width: int, map_height: int):
        """根据地图尺寸和布局规则，设置屏幕、视口和相机。"""
        IDEAL_CELL_SIZE = 32
        
        # ... (四象限布局逻辑保持不变) ...

        if map_width >= 25 and map_height >= 20:
            window_w = 25 * IDEAL_CELL_SIZE
            window_h = 20 * IDEAL_CELL_SIZE + self.hud_height
            self.game_viewport_rect.size = (window_w, window_h - self.hud_height)
            self.game_viewport_rect.x = 0
        elif map_width >= 25 and map_height < 20:
            window_w = 25 * IDEAL_CELL_SIZE
            window_h = map_height * IDEAL_CELL_SIZE + self.hud_height
            self.game_viewport_rect.size = (window_w, window_h - self.hud_height)
            self.game_viewport_rect.x = 0
        elif map_width < 25 and map_height >= 20:
            window_w = 25 * IDEAL_CELL_SIZE
            window_h = 20 * IDEAL_CELL_SIZE + self.hud_height
            viewport_w = map_width * IDEAL_CELL_SIZE
            viewport_x = (window_w - viewport_w) // 2
            self.game_viewport_rect.size = (viewport_w, window_h - self.hud_height)
            self.game_viewport_rect.x = viewport_x
        else: # map_width < 25 and map_height < 20
            window_w = 25 * IDEAL_CELL_SIZE
            window_h = map_height * IDEAL_CELL_SIZE + self.hud_height
            viewport_w = map_width * IDEAL_CELL_SIZE
            viewport_x = (window_w - viewport_w) // 2
            self.game_viewport_rect.size = (viewport_w, window_h - self.hud_height)
            self.game_viewport_rect.x = viewport_x
            
        self.screen = pygame.display.set_mode((window_w, window_h))
        self.renderer = Renderer(self.screen, self.env, IDEAL_CELL_SIZE, self.game_viewport_rect)
        self.camera = Camera(map_width * IDEAL_CELL_SIZE, map_height * IDEAL_CELL_SIZE)

    def _open_file_dialog(self, title="选择文件", filetypes=(("JSON files", "*.json"), ("All files", "*.*"))):
        """
        打开文件选择对话框
        """
        root = tk.Tk()
        root.withdraw()
        
        # # 设置默认目录为游戏目录
        # initial_dir = os.path.join(os.path.dirname(__file__), "generated_maps")
        # if not os.path.exists(initial_dir):
        #     initial_dir = os.path.dirname(__file__)
         # 设置默认目录为 D:\MyMazeGame
        initial_dir = r"D:\MyMazeGame"
        if not os.path.exists(initial_dir):
            initial_dir = os.path.dirname(__file__)
            
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title=title,
            filetypes=filetypes
        )
        
        root.destroy()
        return file_path

    def _start_game_from_generator(self, width: int, height: int,difficulty:str):
        self.tabu_list.clear()
        try:
            if width % 2 == 0 or height % 2 == 0:
                width += 1 if width % 2 == 0 else 0
                height += 1 if height % 2 == 0 else 0
            self.env = Environment(width, height)
            generate_world(self.env,difficulty) # 假设generate_world内部处理难度
            save_maze_to_json(self.env)
            start_pos = self._find_start_position()
            if start_pos is None: raise RuntimeError("生成的地图中找不到起点 'S'。")
            self.agent = Agent(x=start_pos[0], y=start_pos[1])
            self._setup_game_screen_and_camera(width, height)
            self.game_state = 'PLAYING'
            pygame.display.set_caption("Labyrinthos - 迷宫探险")
        except Exception as e:
            self.error_message = f"生成失败: {e}"; print(self.error_message); self.game_state = 'MENU'; self._init_menu()

    def _start_game_from_file(self, filename: str):
        self.tabu_list.clear()
        try:
            self.env = Environment(1, 1) 
            success = load_world_from_file(self.env, filename)
            if not success: raise ValueError(f"无法从 {filename} 加载地图。")
            width, height = self.env.width, self.env.height
            start_pos = self._find_start_position()
            if start_pos is None: raise RuntimeError("加载的地图中找不到起点 'S'。")
            self.agent = Agent(x=start_pos[0], y=start_pos[1])
            self._setup_game_screen_and_camera(width, height)
            self.game_state = 'PLAYING'
            pygame.display.set_caption("Labyrinthos - 迷宫探险")
        except Exception as e:
            self.error_message = f"加载游戏失败: {e}"; print(self.error_message); self.game_state = 'MENU'; self._init_menu()

    def _find_start_position(self) -> tuple[int, int] | None:
        for y in range(self.env.height):
            for x in range(self.env.width):
                if self.env.get_cell(x, y) == Environment.START:
                    return (x, y)
        return None
    
    def _start_boss_battle(self):
        """加载BOSS数据，计算策略，并切换到战斗模式"""
        try:
            # 使用用户选择的文件
            if not self.selected_boss_file:
                print("错误: 未选择BOSS文件")
                return
                
            with open(self.selected_boss_file, 'r') as f:
                self.boss_battle_data = json.load(f)

            print("正在计算最优战斗策略...")
            # boss_battle_solver 返回的是一个字典
            solution_dict = boss_battle_solver(self.boss_battle_data) 
            
            # 检查算法是否找到了解
            if not solution_dict or solution_dict.get("min_turns") is None or solution_dict.get("min_turns") == float('inf'):
                print("未能找到获胜策略，战斗自动失败！")
                self.agent.stamina = 0
                self.game_state = 'PLAYING' # 直接返回游戏
                return

            # 将字典格式的解保存到 self.boss_battle_solution
            self.boss_battle_solution = solution_dict
            # --- 修改结束 ---

            # 初始化战斗动画
            self.battle_turn_index = -1
            self.battle_animation_timer = 0
            self.battle_animation_phase = 'highlight'
            
            initial_healths = list(self.boss_battle_data['B'])
            self.battle_current_state = {
                "boss_healths": list(initial_healths),
                "initial_healths": tuple(initial_healths),
                "cooldowns": [0] * len(self.boss_battle_data['PlayerSkills'])
            }
            
            self.game_state = 'BOSS_BATTLE'
            self.screen = pygame.display.set_mode((1000, 800))
            pygame.display.set_caption("Labyrinthos - BOSS 战")
            
        except Exception as e:
            print(f"启动BOSS战模式失败: {e}")
            self.game_state = 'PLAYING'

    def _update_boss_battle_animation(self, dt):
        """更新BOSS战动画的逻辑（修复：按顺序攻击）"""
        self.battle_animation_timer += dt
        if self.battle_animation_timer < self.battle_animation_speed:
            return

        self.battle_animation_timer = 0
        actions = self.boss_battle_solution["actions"]
        if self.battle_turn_index >= len(actions):
            return

        if self.battle_turn_index == -1:
            self.battle_turn_index = 0
            return

        # 当前技能
        skill_idx = actions[self.battle_turn_index]
        dmg, cd = self.boss_battle_data['PlayerSkills'][skill_idx]

        # --- 修复：按顺序攻击 BOSS ---
        target_idx = None
        for i, hp in enumerate(self.battle_current_state['boss_healths']):
            if hp > 0:
                target_idx = i
                break

        if target_idx is not None:
            self.battle_current_state['boss_healths'][target_idx] = max(
                0, self.battle_current_state['boss_healths'][target_idx] - dmg)
            print(f"回合 {self.battle_turn_index + 1}: 使用技能 {skill_idx}，对 BOSS {target_idx} 造成 {dmg} 伤害，剩余HP: {self.battle_current_state['boss_healths'][target_idx]}")

        # 冷却更新
        self.battle_current_state['cooldowns'] = [max(0, c - 1) for c in self.battle_current_state['cooldowns']]
        self.battle_current_state['cooldowns'][skill_idx] = cd

        # 进入下一回合
        self.battle_turn_index += 1     
                  
    def _start_puzzle_mode(self):
        """加载一个随机的密码文件并切换到解密模式"""
        try:
            # puzzle_dir = r"D:\\MyMazeGame\\TEST\\4_password_test"
            # json_files = [f for f in os.listdir(puzzle_dir) if f.endswith('.json')]
            # if not json_files:
            #     print("错误: password_test 目录下没有找到密码文件。")
            #     self.game_state = 'PLAYING' # 无法开始，直接返回游戏
            #     return
            
            # chosen_file = random.choice(json_files)
            # with open(os.path.join(puzzle_dir, chosen_file), 'r') as f:
            #     self.puzzle_data = json.load(f)
            
            # 使用用户选择的文件
            if not self.selected_puzzle_file:
                print("错误: 未选择谜题文件")
                return
                
            with open(self.selected_puzzle_file, 'r') as f:
                self.puzzle_data = json.load(f)
            
            # --- 核心修改：在进入解密模式前，重置窗口大小 ---
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            # --- 修改结束 ---

            # 重置解密状态
            self.puzzle_result = None
            self.puzzle_thinking = False
            self.game_state = 'PUZZLE'
            pygame.display.set_caption("Labyrinthos - 破解机关")
            
        except Exception as e:
            print(f"启动解密模式失败: {e}")
            self.game_state = 'PLAYING'
    
    def _update_game_state(self):
        """处理玩家移动后可能触发的事件，并检查胜利/失败条件。"""
        pos = self.agent.get_position()
        cell = self.env.get_cell(pos[0], pos[1])
        
        # --- 事件处理 ---
        if cell == Environment.GOLD:
            self.agent.gold += 50 # 金币+5
            self.env.set_cell(pos[0], pos[1], Environment.PATH)
            print("获得金币！金币+50")
        elif cell == Environment.TRAP:
            self.agent.gold -= 30 # 金币-3
            self.env.set_cell(pos[0], pos[1], Environment.PATH)
            print("掉入陷阱！金币-30")
        elif cell == Environment.LOCKER:
            print("\n--- 遇见LOCKER，准备解谜！ ---")
            if self.selected_puzzle_file:
                self._start_puzzle_mode()
                
            else:
                print("警告: 未选择谜题文件，无法启动解密")
            self.env.set_cell(pos[0], pos[1], Environment.PATH)
            
            
            # if self.game_state == 'PUZZLE' and self.puzzle_result:
            #     tries = self.puzzle_result.get('tries', 0)
            #     self.agent.gold -= tries
            #     print(f"解密尝试 {tries} 次，金币减少 {tries}")
                
            self._start_puzzle_mode()
            self.env.set_cell(pos[0], pos[1], Environment.PATH) # 踩上后机关就消失
        elif cell == Environment.BOSS:
            print("\n--- 遭遇BOSS，准备战斗！ ---")
            if self.selected_boss_file:
                self._start_boss_battle()
            else:
                print("警告: 未选择BOSS文件，无法启动战斗")
            self.env.set_cell(pos[0], pos[1], Environment.PATH)
            
            self._start_boss_battle()# 不移除BOSS，等战斗胜利后再移除
            # 战斗后将格子变通路
            self.env.set_cell(pos[0], pos[1], Environment.PATH)
        
        # --- 胜利条件检查 ---
        elif cell == Environment.EXIT:
            # 统计地图上是否还有未被击败的BOSS
            remaining_bosses = sum(1 for row in self.env.grid for c in row if c == Environment.BOSS)
            if remaining_bosses == 0:
                print("\n--- 恭喜！已击败所有BOSS并到达终点！ ---")
                self.game_state = 'VICTORY' # 切换到胜利状态
                pygame.display.set_caption("Labyrinthos - 游戏胜利")
            else:
                print(f"提示：你已到达终点，但还有 {remaining_bosses} 个BOSS尚未击败！")

        # --- 失败条件检查 (放在最后) ---
        if self.agent.stamina <= 0:
            print("\n--- 体力耗尽，游戏失败！ ---")
            self.game_state = 'GAME_OVER'
            pygame.display.set_caption("Labyrinthos - 游戏结束")
        
        # self._save_game()
        self.save_game_state("savegame.json", self.env, self.agent)

    def _handle_menu_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False; return
            for box in self.input_boxes: box.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.difficulty_button_rect.collidepoint(event.pos):
                    self.difficulty = '困难' if self.difficulty == '简单' else '简单'; return
                if self.load_button_rect.collidepoint(event.pos):
                    filepath = self._open_file_dialog()
                    if filepath: self._start_game_from_file(os.path.basename(filepath)); return
                # 新增：BOSS文件选择
                if self.select_boss_button_rect.collidepoint(event.pos):
                    filepath = self._open_file_dialog("选择BOSS文件", [("JSON files", "*.json")])
                    if filepath:
                        self.selected_boss_file = filepath
                        print(f"已选择BOSS文件: {filepath}")
                    return
                
                # 新增：谜题文件选择
                if self.select_puzzle_button_rect.collidepoint(event.pos):
                    filepath = self._open_file_dialog("选择谜题文件", [("JSON files", "*.json")])
                    if filepath:
                        self.selected_puzzle_file = filepath
                        print(f"已选择谜题文件: {filepath}")
                    return
                if self.generate_button_rect.collidepoint(event.pos):
                    rows_text, cols_text = self.input_rows.text, self.input_cols.text
                    if rows_text.isdigit() and cols_text.isdigit():
                        rows, cols = int(rows_text), int(cols_text)
                        if 5 <= rows <= 101 and 5 <= cols <= 101:
                            self.error_message = ""
                            self._start_game_from_generator(width=cols, height=rows,difficulty=self.difficulty); return # <-- 使用正确的方法名
                        else: self.error_message = "尺寸必须在 5 和 101 之间！"
                    else: self.error_message = "请输入有效的数字！"
                    return
                
                # 例：菜单输入处理处新增 "继续上次" 按钮事件
                if self.continue_button_rect.collidepoint(event.pos):
                    self._load_game()
                    return
                    
    def _handle_playing_input(self):
        """处理游戏状态下的输入，包括HUD按钮点击和自动寻路。"""
        # 如果在自动寻路模式下，则不处理任何玩家输入
        if self.autoplay_mode:
            # 允许按ESC退出自动寻路
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False; return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.autoplay_mode = False # 停止自动寻路
                    print("自动寻路已停止。")
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False; return
            
            # 处理HUD按钮点击
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.dp_button_rect.collidepoint(event.pos):
                    print("\n--- 按钮点击：开始执行动态规划 ---")
                    max_gold, optimal_path = find_optimal_path_dp(self.env)
                    if optimal_path:
                        print("最优路径已找到，开始自动寻路演示...")
                        print(optimal_path)
                        # --- 启动自动寻路模式 ---
                        self.autoplay_path = optimal_path
                        self.autoplay_step = 0
                        self.autoplay_mode = "DP"
                        # 将agent位置重置到路径起点，以防玩家之前移动过
                        start_pos = self.autoplay_path[0]
                        self.agent.x, self.agent.y = start_pos[0], start_pos[1]
                        
                elif self.greedy_button_rect.collidepoint(event.pos):
                    print("\n--- 按钮点击：开始执行贪心算法演示 ---")
                    # 启动自动寻路，但路径是动态生成的
                    self.autoplay_path = [] # 清空旧路径
                    self.autoplay_mode = "GREEDY" # 使用一个新的模式名
                    self.agent.x, self.agent.y = self._find_start_position() # 重置到起点
                        
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = 'MENU'
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
                    self._init_menu()
                    # 重置视口，以防下次进入游戏受影响
                    self.game_viewport_rect = pygame.Rect(0, self.hud_height, self.screen_width, self.screen_height - self.hud_height)
                    return
                
                # --- 核心修改：仅保留WASD控制 ---
                dx, dy = 0, 0
                if event.key == pygame.K_w:      # W键控制向上
                    dy = -1
                elif event.key == pygame.K_s:    # S键控制向下
                    dy = 1
                elif event.key == pygame.K_a:    # A键控制向左
                    dx = -1
                elif event.key == pygame.K_d:    # D键控制向右
                    dx = 1
                
                if dx != 0 or dy != 0:
                    next_x, next_y = self.agent.x + dx, self.agent.y + dy
                    if self.env.is_walkable(next_x, next_y):
                        self.agent.move(dx, dy, self.visited_map) # 移动后检查事件
                        self._update_game_state() # 移动后检查事件
                        # --- 更新禁忌列表 ---
                        self.tabu_list.append((self.agent.x, self.agent.y))
                        if len(self.tabu_list) > self.tabu_list_size:
                            self.tabu_list.pop(0) # 移除最旧的记录
            
        # self._save_game()
        self.save_game_state("savegame.json", self.env, self.agent)
        self._update_game_state()

    def _handle_puzzle_input(self):
        """处理解密界面的输入，包含返回游戏时的窗口重置。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False; return

            if event.type == pygame.MOUSEBUTTONDOWN:
                # --- 统一的返回游戏逻辑 ---
                def return_to_game():
                    self.game_state = 'PLAYING'
                    # --- 核心修改：重新调用布局函数来恢复游戏窗口大小 ---
                    self._setup_game_screen_and_camera(self.env.width, self.env.height)
                    pygame.display.set_caption("Labyrinthos - 迷宫探险")
                    # 解密完成后更新金币值
                    if self.puzzle_result:
                        tries = self.puzzle_result.get('tries', 0)
                        self.agent.gold -= tries
                        print(f"解密尝试 {tries} 次，金币减少 {tries}")
                # --- 逻辑结束 ---

                # 阶段1：尚未解密
                if self.puzzle_result is None:
                    if self.think_button_rect.collidepoint(event.pos) and not self.puzzle_thinking:
                        # ... (解密计算逻辑不变) ...
                        self.puzzle_thinking = True
                        self._draw_puzzle_screen() # 立即刷新显示“思考中”
                        solver = PasswordSolver(self.puzzle_data['C'], self.puzzle_data['L'])
                        password, tries = solver.solve()
                        self.puzzle_result = {"password": password, "tries": tries}
                        # ... (更新玩家状态的逻辑不变) ...
                        self.puzzle_thinking = False
                
                # 阶段2：解密已完成
                else:
                    if self.think_button_rect.collidepoint(event.pos):
                        return_to_game()
                        return

                # “放弃破解”按钮
                if self.puzzle_back_button_rect.collidepoint(event.pos):
                    print("玩家放弃破解，返回游戏。")
                    return_to_game()
                    return

    def _handle_boss_battle_input(self):
        """处理BOSS战界面的输入，主要是退出。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False; return
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 只有当动画播放完毕后，退出按钮才有效
                if self.battle_turn_index >= len(self.boss_battle_solution['actions']):
                    if self.battle_exit_button_rect.collidepoint(event.pos):
                        # 找到地图上的BOSS并移除
                        for y in range(self.env.height):
                           for x in range(self.env.width):
                               if self.env.get_cell(x, y) == Environment.BOSS:
                                   self.env.set_cell(x, y, Environment.PATH)
                                   break
                        
                        # 返回游戏
                        self.game_state = 'PLAYING'
                        self._setup_game_screen_and_camera(self.env.width, self.env.height)
                        pygame.display.set_caption("Labyrinthos - 迷宫探险")
                        return
    
    def _draw_puzzle_screen(self):
        """绘制解密界面，根据不同阶段显示不同内容。"""
        self.screen.fill((30, 40, 50)) # 深色科技蓝背景
        
        # --- 绘制线索和哈希 (这部分不变) ---
        y_offset = 50
        title_surf = self.font.render("破解机关", True, (100, 200, 255))
        self.screen.blit(title_surf, (self.screen_width/2 - title_surf.get_width()/2, y_offset))
        
        y_offset += 80
        clue_text = f"线索 (C):  {str(self.puzzle_data['C'])}"
        clue_surf = self.small_font.render(clue_text, True, (200, 200, 200))
        self.screen.blit(clue_surf, (50, y_offset))

        y_offset += 50
        hash_text = f"哈希 (L):  {self.puzzle_data['L'][:32]}..." # 只显示部分哈希
        hash_surf = self.small_font.render(hash_text, True, (200, 200, 200))
        self.screen.blit(hash_surf, (50, y_offset))

        # --- 核心修改：动态绘制主按钮 ---
        button_text_str = ""
        # 阶段1：待解密
        if self.puzzle_result is None:
            if self.puzzle_thinking:
                button_text_str = "思考中..."
            else:
                button_text_str = "开始解密"
        # 阶段2：解密完成
        else:
            button_text_str = "继续"
        
        pygame.draw.rect(self.screen, (0, 150, 150), self.think_button_rect, border_radius=8)
        think_text = self.font.render(button_text_str, True, (255, 255, 255))
        self.screen.blit(think_text, think_text.get_rect(center=self.think_button_rect.center))

        # --- 绘制输出窗口 (只有在解密完成后才显示内容) ---
        y_offset = 350
        output_rect = pygame.Rect(50, y_offset, self.screen_width - 100, 200)
        pygame.draw.rect(self.screen, (10, 20, 30), output_rect)
        pygame.draw.rect(self.screen, (100, 200, 255), output_rect, 2)
        
        if self.puzzle_result:
            if self.puzzle_result['password']:
                res_pass_text = f"找到密码: {self.puzzle_result['password']}"
                pass_surf = self.font.render(res_pass_text, True, (50, 255, 50)) # 绿色
                self.screen.blit(pass_surf, (output_rect.x + 30, output_rect.y + 40))
            else:
                res_pass_text = "破解失败！"
                pass_surf = self.font.render(res_pass_text, True, (255, 50, 50)) # 红色
                self.screen.blit(pass_surf, (output_rect.x + 30, output_rect.y + 40))

            res_tries_text = f"消耗体力: {15 + self.puzzle_result['tries']}"
            tries_surf = self.font.render(res_tries_text, True, (200, 200, 200))
            self.screen.blit(tries_surf, (output_rect.x + 30, output_rect.y + 110))

        # --- 修复：总是绘制返回按钮 ---
        # 这个按钮现在是一个紧急出口，以防解密卡住
        # 主要的流程是通过“继续”按钮
        pygame.draw.rect(self.screen, (150, 0, 0), self.puzzle_back_button_rect, border_radius=8)
        back_text = self.font.render("放弃破解", True, (255, 255, 255))
        self.screen.blit(back_text, back_text.get_rect(center=self.puzzle_back_button_rect.center))
        
        pygame.display.flip()
        
    def _draw_boss_battle_screen(self):
        """绘制BOSS战可视化界面"""
        self.screen.fill((40, 30, 50)) # 暗紫色背景
        
        # 1. 绘制BOSS区域
        num_bosses = len(self.boss_battle_data['B'])
        for i in range(num_bosses):
            img = self.boss_images[i % len(self.boss_images)]
            x_pos = 100 + i * 220
            y_pos = 50
            self.screen.blit(img, (x_pos, y_pos))
            
            # 绘制血条
            hp = self.battle_current_state['boss_healths'][i]
            max_hp = self.battle_current_state['initial_healths'][i]
            hp_ratio = hp / max_hp if max_hp > 0 else 0
            
            bg_rect = pygame.Rect(x_pos, y_pos + 140, 128, 25)
            hp_rect = pygame.Rect(x_pos, y_pos + 140, 128 * hp_ratio, 25)
            
            pygame.draw.rect(self.screen, (80, 20, 20), bg_rect)
            pygame.draw.rect(self.screen, (200, 40, 40), hp_rect)
            
            hp_text = self.button_font.render(f"{hp}/{max_hp}", True, (255, 255, 255))
            self.screen.blit(hp_text, hp_text.get_rect(center=bg_rect.center))

        # 2. 绘制技能区域
        num_skills = len(self.boss_battle_data['PlayerSkills'])
        skills_area_width = num_skills * 100
        start_skills_x = (self.screen.get_width() - skills_area_width - 250) // 2
        
        for i in range(num_skills):
            img = self.skill_images[i % len(self.skill_images)]
            x_pos = start_skills_x + i * 100
            y_pos = 400
            
            # # 高亮当前回合使用的技能
            # is_highlighted = (self.battle_animation_phase == 'highlight' and 
            #                   self.battle_turn_index < len(self.boss_battle_solution['actions']) and 
            #                   self.boss_battle_solution['actions'][self.battle_turn_index] == i)
            # --- 新的高亮逻辑 ---
            is_highlighted = (self.battle_turn_index < len(self.boss_battle_solution['actions']) and
                              self.boss_battle_solution['actions'][self.battle_turn_index] == i)
            
            if is_highlighted:
                highlight_rect = pygame.Rect(x_pos - 10, y_pos - 10, 100, 140)
                pygame.draw.rect(self.screen, (255, 255, 0, 100), highlight_rect, border_radius=10)

            self.screen.blit(img, (x_pos, y_pos))
            
            # 绘制技能信息
            dmg, cd = self.boss_battle_data['PlayerSkills'][i]
            dmg_text = self.button_font.render(f"伤害: {dmg}", True, (220, 220, 220))
            cd_text = self.button_font.render(f"冷却: {cd}", True, (220, 220, 220))
            self.screen.blit(dmg_text, (x_pos, y_pos + 85))
            self.screen.blit(cd_text, (x_pos, y_pos + 105))
            
            # 绘制当前冷却
            current_cd = self.battle_current_state['cooldowns'][i]
            if current_cd > 0:
                overlay = pygame.Surface((80, 80), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (x_pos, y_pos))
                cd_val_text = self.font.render(str(current_cd), True, (255, 255, 0))
                self.screen.blit(cd_val_text, cd_val_text.get_rect(center=(x_pos + 40, y_pos + 40)))

        # 3. 绘制右侧技能序列
        actions_panel = pygame.Rect(self.screen.get_width() - 220, 300, 200, self.screen.get_height() - 200)
        pygame.draw.rect(self.screen, (10, 20, 30), actions_panel)
        title = self.small_font.render("技能序列", True, (200, 200, 200))
        self.screen.blit(title, (actions_panel.x + 10, actions_panel.y + 10))
        
        if self.boss_battle_solution:
            for turn, skill_idx in enumerate(self.boss_battle_solution['actions']):
                 # --- 新的序列颜色逻辑 ---
                if turn == self.battle_turn_index:
                    color = (255, 255, 0) # 黄色高亮当前将要执行的动作
                elif turn < self.battle_turn_index:
                    color = (128, 128, 128) # 灰色表示已执行
                else:
                    color = (200, 200, 200) # 白色表示待执行
                
                action_text = f"回合 {turn + 1}: 使用技能 {skill_idx}"
                action_surf = self.button_font.render(action_text, True, color)
                self.screen.blit(action_surf, (actions_panel.x + 15, actions_panel.y + 50 + turn * 25))
                if turn * 25 > actions_panel.height - 80: break # 防止溢出
        
        # 4. 绘制退出按钮 (仅当动画播放完毕后)
        if self.battle_turn_index >= len(self.boss_battle_solution['actions']):
            pygame.draw.rect(self.screen, (150, 0, 0), self.battle_exit_button_rect, border_radius=8)
            exit_text = self.font.render("退出战斗", True, (255, 255, 255))
            self.screen.blit(exit_text, exit_text.get_rect(center=self.battle_exit_button_rect.center))
            
        pygame.display.flip()

    def _draw_menu(self):
        """绘制菜单界面"""
        
        if not hasattr(self, 'setting_bg'):
            try:
                self.setting_bg = pygame.image.load(r"D:\\MyMazeGame\\assets\setting.png").convert()
            except pygame.error as e:
                print(f"无法加载背景图片: {e}")
                # 设置默认纯色背景
                self.setting_bg = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
                self.setting_bg.fill((20, 20, 40))  # 绿色作为胜利背景
        
        # 调整背景图片大小以适应屏幕
        setting_bg = pygame.transform.scale(self.setting_bg, (self.screen.get_width(), self.screen.get_height()))
        # 绘制背景
        self.screen.blit(setting_bg, (0, 0))
        
        
        # --- 核心修复：在绘制前更新输入框的状态 ---
        self.input_rows.update()
        self.input_cols.update()
        # --- 修复结束 ---


        title_surf = self.font.render("SETING", True, (255, 255, 255))
        self.screen.blit(title_surf, (self.screen_width/2 - title_surf.get_width()/2, 100))

        rows_label = self.small_font.render("        Height", True, (200, 200, 200))
        self.screen.blit(rows_label, (self.input_rows.rect.x - 150, self.input_rows.rect.y + 5))
        self.input_rows.draw(self.screen)

        cols_label = self.small_font.render("         Width", True, (200, 200, 200))
        self.screen.blit(cols_label, (self.input_cols.rect.x - 150, self.input_cols.rect.y + 5))
        self.input_cols.draw(self.screen)
        
        
        # --- 新增：绘制难度选择按钮 ---
        diff_color = (180, 100, 0) if self.difficulty == '困难' else (0, 150, 150)
        pygame.draw.rect(self.screen, diff_color, self.difficulty_button_rect)
        diff_text_str = f"难度: {self.difficulty}"
        diff_text = self.small_font.render(diff_text_str, True, (255, 255, 255))
        self.screen.blit(diff_text, (self.difficulty_button_rect.centerx - diff_text.get_width()/2, self.difficulty_button_rect.centery - diff_text.get_height()/2))
        
        
        # --- 绘制调整了位置的“生成”和“加载”按钮 ---
        pygame.draw.rect(self.screen, (0, 150, 0), self.generate_button_rect)
        gen_text = self.font.render("生成", True, (255, 255, 255))
        self.screen.blit(gen_text, (self.generate_button_rect.centerx - gen_text.get_width()/2, self.generate_button_rect.centery - gen_text.get_height()/2))
        
        pygame.draw.rect(self.screen, (0, 100, 150), self.load_button_rect)
        load_text = self.font.render("加载", True, (255, 255, 255))
        self.screen.blit(load_text, (self.load_button_rect.centerx - load_text.get_width()/2, self.load_button_rect.centery - load_text.get_height()/2))
        if self.error_message:
            error_surf = self.small_font.render(self.error_message, True, (255, 100, 100))
            self.screen.blit(error_surf, (self.screen_width/2 - error_surf.get_width()/2, 450))

        # 新增：绘制文件选择按钮
        pygame.draw.rect(self.screen, (100, 0, 150), self.select_boss_button_rect)
        boss_text = self.font.render("选择BOSS", True, (255, 255, 255))
        self.screen.blit(boss_text, boss_text.get_rect(center=self.select_boss_button_rect.center))
        
        pygame.draw.rect(self.screen, (0, 100, 150), self.select_puzzle_button_rect)
        puzzle_text = self.font.render("选择谜题", True, (255, 255, 255))
        self.screen.blit(puzzle_text, puzzle_text.get_rect(center=self.select_puzzle_button_rect.center))
        
        # 显示已选择的文件
        if self.selected_boss_file:
            boss_file_text = self.small_font.render(f"BOSS: {os.path.basename(self.selected_boss_file)}", True, (200, 200, 200))
            self.screen.blit(boss_file_text, (320, 520))
        
        if self.selected_puzzle_file:
            puzzle_file_text = self.small_font.render(f"谜题: {os.path.basename(self.selected_puzzle_file)}", True, (200, 200, 200))
            self.screen.blit(puzzle_file_text, (320, 580))
            
        # 绘制继续游戏按钮
        pygame.draw.rect(self.screen, (180, 120, 30), self.continue_button_rect)
        continue_text = self.font.render("继续上次", True, (255, 255, 255))
        self.screen.blit(continue_text, continue_text.get_rect(center=self.continue_button_rect.center))


        pygame.display.flip()
 
    def _draw_hud(self):
        """在屏幕顶部绘制新的二分布局HUD。"""
        # 1. 绘制HUD背景和分割线
        hud_rect = pygame.Rect(0, 0, self.screen_width, self.hud_height)
        pygame.draw.rect(self.screen, (10, 10, 20), hud_rect)
        pygame.draw.line(self.screen, (80, 80, 120), (0, self.hud_height - 1), (self.screen_width, self.hud_height - 1), 2)

        # --- 左半部分：状态信息（两行显示） ---
        if self.agent and self.env:
            remaining_bosses = sum(1 for row in self.env.grid for cell in row if cell == Environment.BOSS)
            remaining_lockers = sum(1 for row in self.env.grid for cell in row if cell == Environment.LOCKER)
            
            
            # 第一行信息
            info_line1 = [
                f"体力: {self.agent.stamina}",
                f"金币: {self.agent.gold}",
                f"坐标: ({self.agent.x}, {self.agent.y})",
            ]
            # 第二行信息
            info_line2 = [
                f"剩余BOSS: {remaining_bosses}",
                f"剩余LOCKER: {remaining_lockers}",
                # f"麻醉针: {self.agent.inventory.get('麻醉针', 0)}",
                # f"腰带: {self.agent.inventory.get('腰带', 0)}",
                # f"增强鞋: {self.agent.inventory.get('增强鞋', 0)}"
                
            ]
            
            hud_font = self.small_font
            start_x, y1, y2 = 15, 10, 40 # 定义起始x和两行的y坐标
            
            # 绘制第一行
            current_x = start_x
            for text in info_line1:
                text_surf = hud_font.render(text, True, (200, 200, 220))
                self.screen.blit(text_surf, (current_x, y1))
                current_x += text_surf.get_width() + 25

            # 绘制第二行
            current_x = start_x
            for text in info_line2:
                text_surf = hud_font.render(text, True, (200, 200, 220))
                self.screen.blit(text_surf, (current_x, y2))
                current_x += text_surf.get_width() + 10
        
        # --- 右半部分：绘制按钮 ---
        # 绘制动态规划按钮
        pygame.draw.rect(self.screen, (0, 100, 150), self.dp_button_rect, border_radius=5)
        dp_text = self.button_font.render("动态规划", True, (255, 255, 255))
        self.screen.blit(dp_text, dp_text.get_rect(center=self.dp_button_rect.center))

        # 绘制贪心算法按钮
        pygame.draw.rect(self.screen, (0, 150, 100), self.greedy_button_rect, border_radius=5)
        greedy_text = self.button_font.render("贪心算法", True, (255, 255, 255))
        self.screen.blit(greedy_text, greedy_text.get_rect(center=self.greedy_button_rect.center))
             
    def _draw_end_screen(self, message: str, color: tuple):
        """绘制游戏结束或胜利的通用界面。"""
        # 加载背景图片（如果尚未加载）
        if not hasattr(self, 'victory_bg'):
            try:
                self.victory_bg = pygame.image.load(r"D:\MyMazeGame\assets\victory.png").convert()
                self.defeat_bg = pygame.image.load(r"D:\MyMazeGame\assets\defeat.png").convert()
            except pygame.error as e:
                print(f"无法加载背景图片: {e}")
                # 设置默认纯色背景
                self.victory_bg = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
                self.victory_bg.fill((0, 100, 0))  # 绿色作为胜利背景
                self.defeat_bg = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
                self.defeat_bg.fill((100, 0, 0))  # 红色作为失败背景
        
        # 调整背景图片大小以适应屏幕
        victory_bg = pygame.transform.scale(self.victory_bg, (self.screen.get_width(), self.screen.get_height()))
        defeat_bg = pygame.transform.scale(self.defeat_bg, (self.screen.get_width(), self.screen.get_height()))
        
        # 绘制背景
        if message == "游戏胜利！":
            self.screen.blit(victory_bg, (0, 0))
        else:
            self.screen.blit(defeat_bg, (0, 0))

        # 创建一个半透明的遮罩层
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))  # 黑色，半透明（降低透明度以增强背景可见性）
        self.screen.blit(overlay, (0, 0))

        # 绘制结束信息，使用传入的文字和颜色
        end_font = self.font
        text_surf = end_font.render(message, True, color)
        text_rect = text_surf.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() / 2 - 50))
        self.screen.blit(text_surf, text_rect)
        
        # 绘制提示信息
        prompt_font = self.small_font
        prompt_surf = prompt_font.render("按任意键返回主菜单", True, (200, 200, 200))
        prompt_rect = prompt_surf.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() / 2 + 50))
        self.screen.blit(prompt_surf, prompt_rect)

        pygame.display.flip()   
    
    def load_game_state(self,filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state = json.load(f)
            
            # --- 恢复环境 ---
            env = Environment(state["env"]["width"], state["env"]["height"])
            env.grid = state["env"]["grid"]
            
            # --- 恢复 Agent ---
            agent = Agent(state["agent"]["x"], state["agent"]["y"])
            agent.stamina = state["agent"]["stamina"]
            agent.gold = state["agent"]["gold"]
            agent.inventory = defaultdict(int, state["agent"]["inventory"])
            
            # --- 恢复 BOSS / 谜题路径 ---
            selected = state.get("selected_files", {})
            self.selected_boss_file = selected.get("boss", None)
            self.selected_puzzle_file = selected.get("puzzle", None)

            return env, agent
        except Exception as e:
            print(f"读取失败: {e}")
            return None, None

    def save_game_state(self, filepath, env, agent):
        try:
            state = {
                "env": {
                    "width": env.width,
                    "height": env.height,
                    "grid": env.grid
                },
                "agent": {
                    "x": agent.x,
                    "y": agent.y,
                    "stamina": agent.stamina,
                    "gold": agent.gold,
                    "inventory": dict(agent.inventory)
                },
                # --- 新增：记录当前选中的BOSS和谜题路径 ---
                "selected_files": {
                    "boss": self.selected_boss_file,
                    "puzzle": self.selected_puzzle_file
                }
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            # print("存档成功。")
        except Exception as e:
            pass
            # print(f"存档失败: {e}")
   
    def _load_game(self):
        save_path = "savegame.json"
        if not os.path.exists(save_path):
            print("没有找到存档文件。")
            return
        env, agent = self.load_game_state(save_path)
        if env and agent:
            self.env = env
            self.agent = agent
            # --- 恢复窗口等 ---
            self._setup_game_screen_and_camera(env.width, env.height)
            self.game_state = 'PLAYING'
            pygame.display.set_caption("Labyrinthos - 继续游戏")
        else:
            print("恢复失败。")
   
    def run(self):
        """主循环，现在包含自动寻路逻辑。"""
        clock = pygame.time.Clock() # 创建一个时钟来控制帧率和时间
        while self.running:
            # --- 计算时间增量 ---
            # dt 是自上一帧以来经过的秒数
            dt = clock.tick(60) / 1000.0

            if self.game_state == 'MENU':
                self._handle_menu_input()
                if self.game_state == 'MENU': self._draw_menu()
             # --- 新增对 PUZZLE 状态的处理 ---
            elif self.game_state == 'PUZZLE':
                self._handle_puzzle_input()
                if self.game_state == 'PUZZLE':
                    self._draw_puzzle_screen()
            elif self.game_state == 'BOSS_BATTLE':
                dt = clock.tick(60) / 1000.0 # 需要在这里也获取dt
                self._handle_boss_battle_input()
                if self.game_state == 'BOSS_BATTLE':
                    self._update_boss_battle_animation(dt) # 更新动画状态
                    self._draw_boss_battle_screen() # 绘制动画帧
            elif self.game_state == 'PLAYING':
                if not all((self.agent, self.renderer, self.camera)):
                    print("错误：游戏对象未初始化，强制返回主菜单。"); self.game_state = 'MENU'; self._init_menu(); continue
                self._handle_playing_input()
                if self.game_state != 'PLAYING': continue
                
                # # --- 新增：贪心算法的自动寻路 ---
                if self.autoplay_mode == "GREEDY":
                    self.autoplay_timer += dt
                    if self.autoplay_timer >= self.autoplay_speed:
                        self.autoplay_timer = 0
                        
                        vision = self.env.get_vision(self.agent.x, self.agent.y)
                        bosses_defeated = sum(1 for row in self.env.grid for c in row if c == Environment.BOSS) == 0
                        current_pos = self.agent.get_position()
                        
                        # 调用更智能的贪心算法，并传入禁忌列表
                        dx, dy = get_smarter_greedy_move(
                            vision, self.visited_map, current_pos, self.tabu_list, bosses_defeated
                        )
                        
                        if dx != 0 or dy != 0:
                            next_x, next_y = self.agent.x + dx, self.agent.y + dy
                            if self.env.is_walkable(next_x, next_y):
                                self.agent.move(dx, dy, self.visited_map) # agent.move 不再需要接收 visited_map
                                self.visited_map.add((self.agent.x, self.agent.y))
                                
                                # 更新禁忌列表
                                self.tabu_list.append((self.agent.x, self.agent.y))
                                if len(self.tabu_list) > self.tabu_list_size:
                                    self.tabu_list.pop(0)
                                    
                                self._update_game_state()
                            
                        else:
                            print("智能贪心AI决定不动，自动寻路停止。")
                            self.autoplay_mode = False
                        
                # --- 新增：自动寻路更新逻辑 ---
                elif self.autoplay_mode == "DP":
                    self.autoplay_timer += dt
                    # 如果计时器超过了设定的速度
                    if self.autoplay_timer >= self.autoplay_speed:
                        self.autoplay_timer = 0 # 重置计时器
                        
                        if self.autoplay_step < len(self.autoplay_path) - 1:
                            current_pos = self.autoplay_path[self.autoplay_step]
                            next_pos = self.autoplay_path[self.autoplay_step + 1]
                            dx = next_pos[0] - current_pos[0]
                            dy = next_pos[1] - current_pos[1]

                            next_x = self.agent.x + dx
                            next_y = self.agent.y + dy

                            # 检查是否能走，并调用与玩家一致的逻辑
                            if self.env.is_walkable(next_x, next_y):
                                self.agent.move(dx, dy, self.visited_map) # 移动后检查事件
                                self.autoplay_step += 1            # ✅ 前进路径
                                self._update_game_state()          # ✅ 吃金币、进机关
                            else:
                                print("自动寻路：遇到不可通行区域，停止。")
                                self.autoplay_mode = False
                        else:
                            print("自动寻路完成！")
                            self.autoplay_mode = False
                            
                
                self.screen.fill(self.renderer.colors['background'])
                agent_rect = pygame.Rect(self.agent.x * self.renderer.cell_size, self.agent.y * self.renderer.cell_size, self.renderer.cell_size, self.renderer.cell_size)
                self.camera.update(agent_rect, self.game_viewport_rect.width, self.game_viewport_rect.height)
                self.renderer.render_all(self.agent, self.camera)
                self._draw_hud()
                pygame.display.flip()
            elif self.game_state == 'GAME_OVER' or self.game_state == 'VICTORY':
                message, color = ("游戏胜利！", (50, 255, 50)) if self.game_state == 'VICTORY' else ("游戏失败。", (255, 50, 50))
                self._draw_end_screen(message, color)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: self.running = False
                    if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                        # --- 核心修改：返回菜单时，重置窗口大小 ---
                        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
                        self.game_state = 'MENU'; self._init_menu(); break
        pygame.quit(); sys.exit()

if __name__ == '__main__':
    game = GameEngine()
    game.run()
    