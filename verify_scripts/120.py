
"""
修改任务指令：你想在附近2.5公里内找一个停车场，走路过去不超过8分钟。停好车后，你希望从这个停车场走到附近800米内最近的地铁站不超过16分钟。你说话非常有条理和注重细节
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离与类型验证：调用 maps_around_search，以用户坐标108.907433,34.2286为中心、radius=2500、keywords=停车场，验证返回pois里包含目标poi_id=B0HAK7IU5P。
2) 到达时间验证（用户->停车场）：调用 maps_search_detail(B0HAK7IU5P) 获取停车场坐标destination=108.910734,34.227998；再调用 maps_walking_by_coordinates(origin=108.907433,34.2286, destination=108.910734,34.227998)，验证 total_duration_seconds <= 480（8分钟）。
3) 停车场到最近地铁站步行时间验证：以停车场坐标108.910734,34.227998为中心调用 maps_around_search(radius=800, keywords=地铁站) 获取候选地铁站列表；对每个候选地铁站分别调用 maps_walking_by_coordinates(起点=停车场坐标, 终点=地铁站坐标)，取最小的 total_duration_seconds，验证该最小值 <= 960（16分钟）。
"""

import os
import sys

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 导入高德地图工具函数
from tools.amap_tools import (
    maps_search_detail,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "108.907433,34.2286",
    search_radius: int = 2500,  # 2.5km
    keywords: str = "停车场",
    max_walking_duration: int = 480,  # 8 minutes = 480 seconds
    subway_search_radius: int = 800,  # 800m
    subway_keywords: str = "地铁站",
    max_walking_duration_to_subway: int = 960  # 16 minutes = 960 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离与类型验证：调用 maps_around_search，验证返回pois里包含目标poi_id。
    2) 到达时间验证（用户->停车场）：调用 maps_search_detail 获取停车场坐标；再调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 480。
    3) 停车场到最近地铁站步行时间验证：以停车场坐标为中心调用 maps_around_search 获取候选地铁站列表；对每个候选地铁站分别调用 maps_walking_by_coordinates，取最小的 total_duration_seconds，验证该最小值 <= 960。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"108.907433,34.2286"
        search_radius: 搜索半径（米），默认2500（2.5公里）
        keywords: 搜索关键词，默认"停车场"
        max_walking_duration: 最大步行时长（秒），默认480（8分钟）
        subway_search_radius: 地铁站搜索半径（米），默认800
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_walking_duration_to_subway: 到地铁站的最大步行时长（秒），默认960（16分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离与类型验证（2.5公里内的停车场）
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois or len(around_search_result.pois) == 0:
        print(f"❌ 未找到符合条件的POI")
        return False

    # 检查返回列表中是否包含目标POI ID
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break

    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False

    # 步骤2: 获取目标POI详情
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 到达时间验证（用户->停车场<=8分钟）
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    # 步骤4: 搜索停车场附近800米内的地铁站
    subway_search_result = maps_around_search(
        location=poi_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 停车场附近{subway_search_radius}米内未找到地铁站")
        return False

    print(f"✅ 停车场附近{subway_search_radius}米内找到{len(subway_search_result.pois)}个地铁站")

    # 步骤5: 找到步行时间最短的地铁站
    closest_subway = None
    min_walking_duration = float('inf')

    for subway in subway_search_result.pois:
        if not subway.location:
            continue

        walking_result_to_subway = maps_walking_by_coordinates(origin=poi_location, destination=subway.location)
        if walking_result_to_subway.error or walking_result_to_subway.total_duration_seconds is None:
            continue

        walking_duration = walking_result_to_subway.total_duration_seconds
        # print(f"  - {subway.name}: 步行时长{walking_duration}秒（{walking_duration // 60}分钟）")

        if walking_duration < min_walking_duration:
            min_walking_duration = walking_duration
            closest_subway = subway

    if closest_subway is None:
        print(f"❌ 无法找到可步行到达的地铁站")
        return False

    print(f"✅ 找到最近的地铁站: {closest_subway.name}，步行时长{min_walking_duration}秒（{min_walking_duration // 60}分钟）")

    if min_walking_duration > max_walking_duration_to_subway:
        print(f"❌ 到最近地铁站的步行时长{min_walking_duration}秒，超过{max_walking_duration_to_subway}秒（{max_walking_duration_to_subway // 60}分钟）")
        return False

    print(f"✅ 到最近地铁站的步行时长符合要求（<= {max_walking_duration_to_subway}秒，即{max_walking_duration_to_subway // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 733.py 文件...\n")
    result = verify_poi(poi_id="B0HAK7IU5P")
    print(f"\n验证结果: {result}")
