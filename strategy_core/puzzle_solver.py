# labyrinthos/components/strategy_core/puzzle_solver.py
import hashlib
from typing import List, Tuple, Set, Dict
import random

# 固定的盐值 (与你的代码保持一致)
SALT = b'\xb2S"e}\xdf\xb0\xfe\x9c\xde\xde\xfe\xf3\x1d\xdc>'

def hash_password(password: str) -> str:
    """计算密码的SHA-256哈希值（带盐）"""
    password_bytes = password.encode('utf-8')
    hash_obj = hashlib.sha256(SALT + password_bytes)
    return hash_obj.hexdigest()

class PasswordSolver:
    """
    一个集成了多种回溯策略的密码求解器。
    这个版本被精简，以适用于游戏引擎的直接调用。
    """
    def __init__(self, C: List[List[int]], L: str):
        # ... (你提供的 __init__ 和 apply_clues 等方法保持不变) ...
        self.C = C
        self.L = L
        self.sets = [set(range(10)), set(range(10)), set(range(10))]
        self.prime_constraint = False
        self.apply_clues()
    
    def apply_clues(self):
        """应用所有线索到候选数字集合"""
        for clue in self.C:
            if clue == [-1, -1]:
                self.prime_constraint = True
            elif len(clue) == 2:
                self.apply_parity_constraint(clue)
            elif len(clue) == 3:
                self.apply_fixed_constraint(clue)
        
        if self.prime_constraint:
            primes = {2, 3, 5, 7}
            for i in range(3):
                self.sets[i] = self.sets[i] & primes
    
    def apply_parity_constraint(self, clue: List[int]):
        """应用奇偶性约束"""
        pos, parity = clue
        idx = pos - 1
        if parity == 0:
            self.sets[idx] = self.sets[idx] & {0, 2, 4, 6, 8}
        elif parity == 1:
            self.sets[idx] = self.sets[idx] & {1, 3, 5, 7, 9}
    
    def apply_fixed_constraint(self, clue: List[int]):
        """应用固定数字约束"""
        for i, val in enumerate(clue):
            if val != -1:
                self.sets[i] = {val}
    
    # 我们将所有solve_method合并，因为游戏只需要一个最优解
    def solve(self) -> Tuple[str, int]:
        """
        找到所有方法中尝试次数最少的结果。
        """
        methods = [
            self.backtrack_solve(1), self.backtrack_solve(2),
            self.backtrack_solve(3), self.backtrack_solve(4),
            self.backtrack_solve(5), self.solve_method6(),self.solve_method7()
        ]
        
        # 找到尝试次数最少的那个结果
        best_result = min(methods, key=lambda x: x[1])
        return best_result

    # ... (get_frequency_order, get_enum_order, get_position_order, backtrack_solve, solve_method6 保持不变) ...
    def solve_method1(self) -> Tuple[str, int]:
        """方法1：标准顺序"""
        return self.backtrack_solve(method_id=1)
    
    def solve_method2(self) -> Tuple[str, int]:
        """方法2：交换5和6"""
        return self.backtrack_solve(method_id=2)
    
    def solve_method3(self) -> Tuple[str, int]:
        """方法3：逆序"""
        return self.backtrack_solve(method_id=3)
    
    def solve_method4(self) -> Tuple[str, int]:
        """方法4：逆位置顺序"""
        return self.backtrack_solve(method_id=4)
    
    def solve_method5(self) -> Tuple[str, int]:
        """方法5：中间优先"""
        return self.backtrack_solve(method_id=5)
    
    # def solve_method6(self) -> Tuple[str, int]:
    #     """方法6：智能频率排序"""
    #     digit_freq = {
    #         0: 0.05, 1: 0.15, 2: 0.15, 3: 0.15, 4: 0.15,
    #         5: 0.10, 6: 0.10, 7: 0.10, 8: 0.05, 9: 0.10
    #     }
        
    #     orders = [
    #         self.get_frequency_order(self.sets[0], digit_freq),
    #         self.get_frequency_order(self.sets[1], digit_freq),
    #         self.get_frequency_order(self.sets[2], digit_freq)
    #     ]
        
    #     tries = 0
    #     for d0 in orders[0]:
    #         for d1 in orders[1]:
    #             for d2 in orders[2]:
    #                 candidate = [d0, d1, d2]
    #                 if self.prime_constraint:
    #                     primes = {2, 3, 5, 7}
    #                     if not (set(candidate).issubset(primes) and len(set(candidate)) == 3):
    #                         continue
                    
    #                 password_str = ''.join(str(d) for d in candidate)
    #                 tries += 1
    #                 if hash_password(password_str) == self.L:
    #                     return password_str, tries
        
    #     raise ValueError("No valid password found")
    
    
    def solve_method6(self) -> Tuple[str, int]:
        """方法6：智能频率排序（基于实际密码数据优化）"""
        # 基于100个密码数据的实际频率分布
        position_freq = [
            # 百位频率分布
            {1: 0.09, 2: 0.09, 3: 0.11, 4: 0.05, 5: 0.12, 
             7: 0.19, 8: 0.10, 9: 0.09, 0: 0.07, 6: 0.04},
            # 十位频率分布
            {3: 0.19, 5: 0.16, 7: 0.16, 2: 0.09, 9: 0.08,
             0: 0.07, 1: 0.07, 4: 0.06, 8: 0.06, 6: 0.03},
            # 个位频率分布
            {3: 0.22, 5: 0.17, 7: 0.15, 2: 0.10, 9: 0.07,
             1: 0.06, 8: 0.06, 0: 0.05, 4: 0.04, 6: 0.03}
        ]
        
        # 为每个位置生成智能排序列表
        orders = []
        for i in range(3):
            candidates = list(self.sets[i])
            # 按该位置的实际频率降序排序
            candidates.sort(key=lambda d: -position_freq[i].get(d, 0.01))
            orders.append(candidates)
        
        tries = 0
        for d0 in orders[0]:
            for d1 in orders[1]:
                for d2 in orders[2]:
                    candidate = [d0, d1, d2]
                    # 检查素数约束（如果存在）
                    if self.prime_constraint:
                        primes = {2, 3, 5, 7}
                        if not (set(candidate).issubset(primes) and len(set(candidate))) == 3:
                            continue
                    
                    password_str = ''.join(str(d) for d in candidate)
                    tries += 1
                    if hash_password(password_str) == self.L:
                        return password_str, tries
        
        raise ValueError("No valid password found")
     
    def solve_method7(self) -> Tuple[str, int]:
        """方法7：随机尝试"""
        all_candidates = []
        for d0 in self.sets[0]:
            for d1 in self.sets[1]:
                for d2 in self.sets[2]:
                    candidate = [d0, d1, d2]
                    if self.prime_constraint:
                        primes = {2, 3, 5, 7}
                        if not (set(candidate).issubset(primes) and len(set(candidate)) == 3):
                            continue
                    all_candidates.append(candidate)
        
        random.shuffle(all_candidates)
        tries = 0
        for candidate in all_candidates:
            password_str = ''.join(str(d) for d in candidate)
            tries += 1
            if hash_password(password_str) == self.L:
                return password_str, tries
        
        raise ValueError("No valid password found")
    
    def get_frequency_order(self, candidates: Set[int], freq: Dict[int, float]) -> List[int]:
        """根据数字频率生成智能排序"""
        candidate_freq = [(d, freq.get(d, 0.05)) for d in candidates]
        candidate_freq.sort(key=lambda x: x[1], reverse=True)
        return [d for d, _ in candidate_freq]
    
    def get_enum_order(self, method_id: int, candidates: Set[int]) -> List[int]:
        """根据方法ID生成枚举顺序"""
        if method_id == 1:
            return sorted(candidates)
        elif method_id == 2:
            lst = sorted(candidates)
            if 5 in lst and 6 in lst:
                idx5 = lst.index(5)
                idx6 = lst.index(6)
                lst[idx5], lst[idx6] = lst[idx6], lst[idx5]
            return lst
        elif method_id == 3:
            return sorted(candidates, reverse=True)
        elif method_id in (4, 5):
            return sorted(candidates)
    
    def get_position_order(self, method_id: int) -> List[int]:
        """根据方法ID获取位置顺序"""
        if method_id in (1, 2, 3):
            return [0, 1, 2]
        elif method_id == 4:
            return [2, 1, 0]
        elif method_id == 5:
            return [1, 0, 2]
    
    def backtrack_solve(self, method_id: int) -> Tuple[str, int]:
        """回溯法求解密码"""
        pos_order = self.get_position_order(method_id)
        
        orders = [
            self.get_enum_order(method_id, self.sets[pos_order[0]]),
            self.get_enum_order(method_id, self.sets[pos_order[1]]),
            self.get_enum_order(method_id, self.sets[pos_order[2]])
        ]
        
        tries = 0
        for d0 in orders[0]:
            for d1 in orders[1]:
                for d2 in orders[2]:
                    candidate = [0, 0, 0]
                    candidate[pos_order[0]] = d0
                    candidate[pos_order[1]] = d1
                    candidate[pos_order[2]] = d2
                    
                    if self.prime_constraint:
                        primes = {2, 3, 5, 7}
                        if not (set(candidate).issubset(primes) and len(set(candidate)) == 3):
                            continue
                    
                    password_str = ''.join(str(d) for d in candidate)
                    tries += 1
                    if hash_password(password_str) == self.L:
                        return password_str, tries
        
        raise ValueError("No valid password found")