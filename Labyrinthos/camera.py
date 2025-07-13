# labyrinthos/camera.py
import pygame

class Camera:
    def __init__(self, width, height):
        """
        初始化相机。

        Args:
            width (int): 游戏世界的总宽度（以像素为单位）。
            height (int): 游戏世界的总高度（以像素为单位）。
        """
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, target_rect):
        """
        将目标矩形（世界坐标）转换为相机坐标。

        Args:
            target_rect (pygame.Rect): 目标对象在世界中的矩形。

        Returns:
            pygame.Rect: 目标对象在屏幕上应该被绘制的矩形。
        """
        return target_rect.move(self.camera_rect.topleft)

    def update(self, target_rect, screen_width, screen_height):
        """
        更新相机的位置，使其以目标为中心。

        Args:
            target_rect (pygame.Rect): 要跟随的目标（通常是玩家）的矩形。
            screen_width (int): 屏幕的宽度。
            screen_height (int): 屏幕的高度。
        """
        # 计算为了让目标居中，相机需要移动到的理想x, y坐标
        x = -target_rect.centerx + screen_width // 2
        y = -target_rect.centery + screen_height // 2

        # 限制相机移动范围，防止看到地图外的黑色区域
        x = min(0, x)  # 不允许相机向右移出左边界
        y = min(0, y)  # 不允许相机向下移出上边界
        x = max(-(self.width - screen_width), x)  # 不允许相机向左移出右边界
        y = max(-(self.height - screen_height), y)  # 不允许相机向上移出下边界

        self.camera_rect = pygame.Rect(x, y, self.width, self.height)