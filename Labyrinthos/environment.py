# labyrinthos/environment.py

class Environment:
    """
    代表游戏世界，包括迷宫布局和其中的所有元素。

    这个类作为迷宫的数据模型，为访问和修改世界状态提供了清晰的API。
    """
    # 为迷宫元素定义常量，以提高代码清晰度和可维护性
    WALL = '#'      # 墙壁
    PATH = ' '      # 通路
    START = 'S'     # 起点
    EXIT = 'E'      # 终点
    GOLD = 'G'      # 资源（金币）
    TRAP = 'T'      # 陷阱
    LOCKER = 'L'    # 机关（谜题）
    BOSS = 'B'      # 最终BOSS

    def __init__(self, width: int, height: int):
        """
        初始化环境。
        
        Args:
            width (int): 迷宫的宽度。
            height (int): 迷宫的高度。
        """
        if width % 2 == 0 or height % 2 == 0:
            print(f"警告: 迷宫尺寸 ({width}x{height}) 最好是奇数，"
                  "这样分治算法的效果最佳。当前偶数尺寸可能导致生成结果不完美。")
            
        self.width = width
        self.height = height
        
        # 将网格初始化为一整块墙壁。
        # 后续的生成器算法会在这上面“雕刻”出路径。
        self.grid = [[self.WALL for _ in range(width)] for _ in range(height)]

    def get_vision(self, x: int, y: int) -> list[list[str]]:
        """获取以(x, y)为中心的3x3视野。"""
        vision = [['#' for _ in range(3)] for _ in range(3)]
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                world_x, world_y = x + dx, y + dy
                if self.is_in_bounds(world_x, world_y):
                    vision[1 + dy][1 + dx] = self.get_cell(world_x, world_y)
        return vision
    
    def get_cell(self, x: int, y: int) -> str:
        """安全地获取指定坐标的元素。"""
        if self.is_in_bounds(x, y):
            return self.grid[y][x]
        return self.WALL  # 将边界外的区域视为墙壁

    def set_cell(self, x: int, y: int, value: str):
        """安全地设置指定坐标的元素。"""
        if self.is_in_bounds(x, y):
            self.grid[y][x] = value

    def is_in_bounds(self, x: int, y: int) -> bool:
        """检查一个坐标是否在迷宫边界内。"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def is_walkable(self, x: int, y: int) -> bool:
        """检查一个单元格是否不是墙壁，即可行走。"""
        cell = self.get_cell(x, y)
        # 在这里可以扩展，比如陷阱也可以走上去，但墙壁不行
        return cell != self.WALL

    def get_all_paths(self) -> list[tuple[int, int]]:
        """返回所有通路格子的(x, y)坐标列表。"""
        paths = []
        for y in range(self.height):
            for x in range(self.width):
                # 注意：这里我们只找初始的通路格，因为元素会被放置在上面
                # 为了简化，我们直接找非墙壁的格子，因为元素放置后也算通路
                if self.grid[y][x] == self.PATH:
                    paths.append((x, y))
        return paths

    def __str__(self) -> str:
        """
        返回迷宫的字符串表示形式，方便在控制台打印。
        """
        # 添加列标题，方便调试
        header = '   ' + ''.join([f'{i%10}' for i in range(self.width)]) + '\n'
        border = '  ' + '+' + '-' * self.width + '+\n'
        
        maze_str = ''
        for i, row in enumerate(self.grid):
            # 添加行标题
            maze_str += f'{i%100:2d}|' + ''.join(row) + '|\n'
            
        return header + border + maze_str + border