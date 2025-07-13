# labyrinthos/agent.py
from collections import defaultdict

class Agent:
    """
    代表在环境中行动的代理（玩家）。
    封装了代理的所有状态信息和行为接口。
    """
    def __init__(self, x: int, y: int):
        """
        初始化代理。
        """
        self.x = x
        self.y = y
        
        # --- 核心修改：定义 stamina 和 inventory ---
        self.stamina = 500  # 初始体力值，为0则失败
        self.gold = 0           # 金币：目标性资源，需要最大化
        self.inventory = defaultdict(int) # 使用defaultdict作为背包
        
    # def move(self, dx: int, dy: int):
    #     """
    #     根据给定的增量移动代理，并消耗体力。
    #     """
    #     self.x += dx
    #     self.y += dy
    #     self.stamina -= 1 # 走路消耗1点体力
    
    def move(self, dx: int, dy: int, visited_map: set): # 接收 visited_map
        self.x += dx
        self.y += dy
        self.stamina -= 1
        visited_map.add((self.x, self.y)) # 记录访问

    def add_item(self, item_name: str, quantity: int = 1):
        """
        向背包添加指定数量的道具。
        """
        self.inventory[item_name] += quantity
        print(f"获得了 {quantity} 个 '{item_name}'！当前拥有: {self.inventory[item_name]}")

    def use_item(self, item_name: str) -> bool:
        """
        尝试使用一个道具。如果成功，返回True；否则返回False。
        """
        if self.inventory.get(item_name, 0) > 0:
            self.inventory[item_name] -= 1
            print(f"使用了 '{item_name}'。剩余: {self.inventory[item_name]}")
            return True
        print(f"无法使用 '{item_name}'，数量不足。")
        return False

    def get_position(self) -> tuple[int, int]:
        """返回代理当前的(x, y)坐标。"""
        return (self.x, self.y)

    def __str__(self) -> str:
        """返回代理状态的字符串表示。"""
        # 使用 dict(self.inventory) 让打印输出更美观
        return f"Agent at ({self.x}, {self.y}) | Stamina: {self.stamina}, Gold: {self.gold}, Inventory: {dict(self.inventory)}"
        # return f"Agent at ({self.x}, {self.y}) with Stamina: {self.stamina}, Inventory: {dict(self.inventory)}"