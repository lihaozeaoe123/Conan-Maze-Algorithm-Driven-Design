# labyrinthos/renderer.py

import pygame
import os
from environment import Environment
from agent import Agent
from camera import Camera

class Renderer:
    """
    负责将游戏世界可视化。
    它只在被指定的 viewport 矩形区域内进行绘制。
    """
  
    def __init__(self, screen: pygame.Surface, env: Environment, cell_size: int, viewport: pygame.Rect):
        """
        初始化渲染器。

        Args:
            screen (pygame.Surface): 主显示窗口。
            env (Environment): 要渲染的环境对象。
            cell_size (int): 单元格像素大小。
            viewport (pygame.Rect): 迷宫应该被绘制在屏幕上的区域。
        """
        self.screen = screen
        self.env = env
        self.cell_size = cell_size
        self.viewport = viewport  # <-- 确保接收并保存了 viewport
        
        self.colors = {
            'background': (20, 20, 40),
            Environment.WALL: (80, 80, 120),
            Environment.PATH: (200, 200, 200)
        }
        self.resources = self._load_resources()

    def _load_resources(self) -> dict:
        """
        加载并缩放游戏元素的图像。如果任何图像加载失败，则完全回退到使用颜色方块。
        """
        resources = {}
        assets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')

        image_files = {
            Environment.START: 'start.png', Environment.EXIT: 'exit.png',
            Environment.GOLD: 'GOLD.png', Environment.TRAP: 'TRAP.png',
            Environment.LOCKER: 'LOCKER.png', Environment.BOSS: 'BOSS.png',
            'AGENT': 'agent.png'
        }

        try:
            print(f"正在从 '{assets_path}' 加载图像资源...")
            for key, filename in image_files.items():
                full_path = os.path.join(assets_path, filename)
                if not os.path.exists(full_path):
                    raise FileNotFoundError(f"资源文件缺失: {filename}")
                image = pygame.image.load(full_path).convert_alpha()
                resources[key] = pygame.transform.scale(image, (self.cell_size, self.cell_size))
            print("图像资源加载成功！")
            return resources
        except (pygame.error, FileNotFoundError) as e:
            print(f"警告: 资源加载失败 ({e})。将完全回退到使用颜色方块。")
            return {
                'colors': {
                    Environment.START: (0, 255, 0), Environment.EXIT: (255, 0, 0),
                    Environment.GOLD: (255, 215, 0), Environment.TRAP: (139, 0, 255),
                    Environment.LOCKER: (0, 191, 255), Environment.BOSS: (178, 34, 34),
                    'AGENT': (66, 135, 245)
                }
            }

    def draw_environment(self, camera: Camera):
        """绘制相机视野内的迷宫网格和静态元素到指定的视口中。"""
        # 计算相机视野内的单元格范围 (使用视口宽高)
        start_col = -camera.camera_rect.x // self.cell_size
        end_col = start_col + (self.viewport.width // self.cell_size) + 2
        start_row = -camera.camera_rect.y // self.cell_size
        end_row = start_row + (self.viewport.height // self.cell_size) + 2

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if self.env.is_in_bounds(x, y):
                    # 1. 计算物体在世界中的绝对位置
                    world_rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                    
                    # 2. 使用相机转换得到在相机内的相对坐标
                    pos_in_camera = camera.apply(world_rect).topleft
                    
                    # 3. 计算最终在屏幕上的绘制位置（相机坐标 + 视口偏移）
                    final_rect = pygame.Rect(
                        pos_in_camera[0] + self.viewport.x,
                        pos_in_camera[1] + self.viewport.y,
                        self.cell_size, self.cell_size
                    )

                    # 优化：只绘制实际在视口内的物体
                    if self.viewport.colliderect(final_rect):
                        cell_char = self.env.get_cell(x, y)
                        
                        # 绘制地形
                        if cell_char == Environment.WALL:
                            pygame.draw.rect(self.screen, self.colors[Environment.WALL], final_rect)
                        else:
                            pygame.draw.rect(self.screen, self.colors[Environment.PATH], final_rect)
                        
                        # 绘制元素
                        if cell_char != Environment.PATH:
                            if 'colors' in self.resources:
                                color = self.resources['colors'].get(cell_char)
                                if color:
                                    inner_rect = final_rect.inflate(-self.cell_size * 0.2, -self.cell_size * 0.2)
                                    pygame.draw.rect(self.screen, color, inner_rect, border_radius=5)
                            else:
                                image = self.resources.get(cell_char)
                                if image:
                                    self.screen.blit(image, final_rect)

    def draw_agent(self, agent: Agent, camera: Camera):
        """在屏幕上绘制代理，同样考虑视口偏移。"""
        agent_world_rect = pygame.Rect(agent.x * self.cell_size, agent.y * self.cell_size, self.cell_size, self.cell_size)
        pos_in_camera = camera.apply(agent_world_rect).topleft
        
        final_agent_rect = pygame.Rect(
            pos_in_camera[0] + self.viewport.x,
            pos_in_camera[1] + self.viewport.y,
            self.cell_size, self.cell_size
        )

        if 'colors' in self.resources:
            color = self.resources['colors'].get('AGENT')
            if color:
                pygame.draw.circle(self.screen, color, final_agent_rect.center, self.cell_size // 2 * 0.8)
        else:
            image = self.resources.get('AGENT')
            if image:
                self.screen.blit(image, final_agent_rect)
            else:
                pygame.draw.circle(self.screen, (255, 255, 255), final_agent_rect.center, self.cell_size // 2 * 0.8)

    def render_all(self, agent: Agent, camera: Camera):
        """
        执行游戏世界的渲染，但不清空也不刷新屏幕。
        这是渲染流水线中的一步，由GameEngine调用。
        """
        self.draw_environment(camera)
        self.draw_agent(agent, camera)