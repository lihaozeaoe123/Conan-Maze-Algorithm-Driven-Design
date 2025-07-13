# labyrinthos/io_handler.py

import json
import os
from datetime import datetime
from environment import Environment

# --- 新增：一个自定义的JSON编码器 ---
class CompactListEncoder(json.JSONEncoder):
    """
    一个特殊的JSON编码器，它会把列表（如果列表内不含复杂对象）编码在一行内。
    """
    def iterencode(self, o, _one_shot=False):
        # 如果是列表类型
        if isinstance(o, list):
            # 检查列表内是否包含字典或列表等复杂类型
            # 如果只包含字符串、数字等简单类型，就使用紧凑格式
            if not any(isinstance(el, (dict, list)) for el in o):
                # 返回一个不带换行和缩进的列表表示
                return (f"[{', '.join(json.dumps(el) for el in o)}]")
        
        # 对于所有其他类型（包括外层的字典和包含复杂对象的列表），使用默认的编码方式
        return super().iterencode(o, _one_shot)

# ----------------------------------------

# 定义存放地图文件的目录名
MAPS_DIR = "generated_maps"

def save_maze_to_json(env: Environment):
    """
    将当前环境的迷宫数据保存为JSON文件。
    使用自定义编码器来让迷宫网格横向显示。

    Args:
        env (Environment): 要保存的环境对象。

    Returns:
        str | None: 成功则返回保存的文件路径，失败则返回None。
    """
    if not os.path.exists(MAPS_DIR):
        try:
            os.makedirs(MAPS_DIR)
        except OSError as e:
            print(f"错误: 无法创建目录 {MAPS_DIR}. 原因: {e}")
            return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"map_{env.height}x{env.width}_{timestamp}.json"
    filepath = os.path.join(MAPS_DIR, filename)

    data_to_save = {
        "metadata": {
            "width": env.width,
            "height": env.height,
            "generated_at": str(datetime.now())
        },
        "maze": env.grid
    }

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # --- 核心修改：使用自定义的编码器 ---
            # 我们不再直接使用 json.dump，而是手动构建字符串
            # 以便对不同部分应用不同的格式化规则
            
            output = "{\n"
            # 1. 格式化 metadata部分 (使用默认的 indent=4)
            metadata_str = json.dumps(data_to_save["metadata"], indent=4)
            # 去掉外层的花括号，并增加缩进
            metadata_str_inner = ",\n".join([f"    {line}" for line in metadata_str.strip("{\n}").split(",\n")])
            output += f'    "metadata": {{\n{metadata_str_inner}\n    }},\n'

            # 2. 格式化 grid 部分 (使用我们的自定义编码器)
            output += '    "maze": [\n'
            grid_rows = []
            for row in data_to_save["maze"]:
                # 对每一行使用 CompactListEncoder
                grid_rows.append("        " + CompactListEncoder().encode(row))
            output += ",\n".join(grid_rows)
            output += "\n    ]\n"
            
            output += "}\n"
            f.write(output)

        print(f"迷宫已成功保存到: {filepath}")
        return filepath
    except IOError as e:
        print(f"错误: 无法保存迷宫到文件 {filepath}. 原因: {e}")
        return None
    
    
def get_saved_maps() -> list[str]:
    """
    扫描地图目录，返回所有有效的.json地图文件名列表。
    """
    if not os.path.exists(MAPS_DIR):
        return []
    
    try:
        # 筛选出所有以.json结尾的文件，并按修改时间降序排列
        files = [f for f in os.listdir(MAPS_DIR) if f.endswith('.json')]
        files.sort(key=lambda f: os.path.getmtime(os.path.join(MAPS_DIR, f)), reverse=True)
        return files
    except OSError as e:
        print(f"错误: 无法读取地图目录 {MAPS_DIR}. 原因: {e}")
        return []

def load_maze_from_json(filename: str) -> dict | None:
    """
    从给定的文件名加载迷宫数据。

    Args:
        filename (str): 要加载的地图文件名。

    Returns:
        dict | None: 成功则返回包含'metadata'和'grid'的字典，失败则返回None。
    """
    filepath = os.path.join(MAPS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"错误: 地图文件不存在 {filepath}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"地图已从 {filepath} 加载。")
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"错误: 加载或解析地图文件失败 {filepath}. 原因: {e}")
        return None

