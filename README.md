# Conan-Maze-Algorithm-Driven-Design

### 多重算法驱动的柯南主题迷宫游戏的设计与开发

代码结构如下：
<img width="256" height="200" alt="image" src="https://github.com/user-attachments/assets/b13f8e44-ed8d-4b5c-afa0-73e81f07b8f8" />

#### 1、Labyrinthos

代码文件，里面存放着项目所有代码：
<img width="220" height="310" alt="image" src="https://github.com/user-attachments/assets/d54c63c2-a9ed-4960-abfc-143033a8adb6" />

agent.py：玩家/AI角色

camera.py：游戏移动视野

environment.py：迷宫地图的信息

gameengine.py：游戏总引擎，运行此文件即可启动游戏

iohandler.py:各种文件的载入与保存（BOSS、解密、地图）

renderer：项目所需的所有用于可视化的函数

components:五大算法的文件夹：
<img width="250" height="346" alt="image" src="https://github.com/user-attachments/assets/2c32f34c-eb4b-4197-b6f0-3905b7a4d408" />

world_generator.py：分治法生成迷宫

strategy_core:

    combat_optimizer.py：分支限界法BOSS战

    dp_planner.py：动态规划走迷宫

    greedy_heuristic.py：贪心算法走迷宫

    puzzle_solver.py：回溯法解密

    huisu.py：与puzzle_solver.py算法一致，但是独立出来便于输出excel文件

#### 2、generated_maps

存放着项目自动生成的地图json文件

#### 3、assets

存放着项目需要的图片

#### 4、TEST

存放着地图连通性、动态规划求解、BOSS战、解密等测试内容的json文件
