
"""
修改任务指令：你想在附近5000米以内找一家酒吧。你打算骑车过去，所以从你这里骑行到酒吧的距离不能超过1500米。为了方便散场坐车回家，酒吧到附近1200米范围内的公交站里，步行距离最近那个公交站的步行距离不能超过800米，而且直线距离最近那个公交站到酒吧的直线距离也不能超过120米。最后，你希望这个酒吧评分至少4.5分。你逻辑性强但没有耐心，希望高效沟通，讨厌废话。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边与类型：调用 maps_around_search(location='115.971478,39.493826', radius='5000', keywords='酒吧')，验证返回pois数量≥8，且包含poi_id='B0L2VA7PYB'。
2) 评分：调用 maps_search_detail(id='B0L2VA7PYB')，从 biz_ext.rating 读取评分，验证 rating ≥ 4.5。
3) 骑行距离（出发地→目标）：用 maps_search_detail 获取目标坐标destination=location；调用 maps_bicycling_by_coordinates(origin='115.971478,39.493826', destination=destination)，验证 total_distance_meters ≤ 1500。
4) 公交站集合（以目标为中心1200米）：调用 maps_around_search(location=目标坐标, radius='1200', keywords='公交站') 获取候选公交站列表。
5) 最近公交站的步行距离：对第4步返回的每个公交站，调用 maps_walking_by_coordinates(origin=目标坐标, destination=公交站坐标) 计算步行距离，取最小步行距离d_walk_min，验证 d_walk_min ≤ 800。
6) 最近公交站的直线距离：对第4步返回的每个公交站，调用 maps_distance(origins=目标坐标, destination=公交站坐标) 得到直线距离，取最小直线距离d_line_min，验证 d_line_min ≤ 120。
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
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.971478,39.493826",
    search_radius: int = 5000,
    keywords: str = "酒吧",
    min_pois_count: int = 8,
    min_rating: float = 4.5,
    max_bicycling_distance: int = 1500,
    bus_stop_search_radius: int = 1200,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_walking_distance: int = 800,
    max_bus_stop_straight_distance: int = 120
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边与类型：调用 maps_around_search，验证返回pois数量≥8，且包含poi_id。
    2) 评分：调用 maps_search_detail，从 biz_ext.rating 读取评分，验证 rating ≥ 4.5。
    3) 骑行距离（出发地→目标）：用 maps_search_detail 获取目标坐标；调用 maps_bicycling_by_coordinates，验证 total_distance_meters ≤ 1500。
    4) 公交站集合（以目标为中心1200米）：调用 maps_around_search 获取候选公交站列表。
    5) 最近公交站的步行距离：对每个公交站，调用 maps_walking_by_coordinates 计算步行距离，取最小步行距离，验证 ≤ 800。
    6) 最近公交站的直线距离：对每个公交站，调用 maps_distance 得到直线距离，取最小直线距离，验证 ≤ 120。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"115.971478,39.493826"
        search_radius: 搜索半径（米），默认5000
        keywords: 搜索关键词，默认"酒吧"
        min_pois_count: 最小POI数量，默认8
        min_rating: 最小评分，默认4.5
        max_bicycling_distance: 最大骑行距离（米），默认1500
        bus_stop_search_radius: 公交站搜索半径（米），默认1200
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_walking_distance: 到公交站的最大步行距离（米），默认800
        max_bus_stop_straight_distance: 到公交站的最大直线距离（米），默认120

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边与类型（附近5000米内的酒吧）
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois or len(around_search_result.pois) < min_pois_count:
        print(f"❌ 周边{keywords}数量不足{min_pois_count}个，实际找到{len(around_search_result.pois) if around_search_result.pois else 0}个")
        return False

    print(f"✅ 找到{len(around_search_result.pois)}个{keywords}，满足最小数量要求（>= {min_pois_count}）")

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

    # 步骤2: 获取目标POI详情并验证评分
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分
    if not poi_detail.biz_ext or 'rating' not in poi_detail.biz_ext:
        print(f"❌ POI没有评分信息")
        return False

    rating = float(poi_detail.biz_ext['rating'])
    if rating < min_rating:
        print(f"❌ POI评分{rating}分，低于要求的{min_rating}分")
        return False
    print(f"✅ POI评分{rating}分，符合要求（>= {min_rating}分）")

    # 步骤3: 骑行距离（出发地→目标）
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取骑行距离")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米，超过{max_bicycling_distance}米")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米，符合要求（<= {max_bicycling_distance}米）")

    # 步骤4: 公交站集合（以目标为中心1200米）
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到公交站")
        return False

    print(f"✅ 找到{len(bus_stop_search_result.pois)}个公交站")

    # 步骤5: 最近公交站的步行距离
    min_walking_distance = float('inf')
    min_walking_bus_stop = None

    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        walking_result = maps_walking_by_coordinates(origin=poi_location, destination=bus_stop.location)
        if walking_result.error or walking_result.total_distance_meters is None:
            continue

        walking_distance = walking_result.total_distance_meters
        if walking_distance < min_walking_distance:
            min_walking_distance = walking_distance
            min_walking_bus_stop = bus_stop

    if min_walking_distance == float('inf'):
        print(f"❌ 无法计算到公交站的步行距离")
        return False

    if min_walking_distance > max_bus_stop_walking_distance:
        print(f"❌ 到最近公交站的步行距离{min_walking_distance}米，超过{max_bus_stop_walking_distance}米")
        return False
    print(f"✅ 到最近公交站({min_walking_bus_stop.name})的步行距离{min_walking_distance}米，符合要求（<= {max_bus_stop_walking_distance}米）")

    # 步骤6: 最近公交站的直线距离
    min_straight_distance = float('inf')
    min_straight_bus_stop = None

    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        distance_result = maps_distance(origins=poi_location, destination=bus_stop.location)
        if distance_result.error or not distance_result.results or len(distance_result.results) == 0:
            continue

        straight_distance = distance_result.results[0].distance_meters
        if straight_distance < min_straight_distance:
            min_straight_distance = straight_distance
            min_straight_bus_stop = bus_stop

    if min_straight_distance == float('inf'):
        print(f"❌ 无法计算到公交站的直线距离")
        return False

    if min_straight_distance > max_bus_stop_straight_distance:
        print(f"❌ 到最近公交站的直线距离{min_straight_distance}米，超过{max_bus_stop_straight_distance}米")
        return False
    print(f"✅ 到最近公交站({min_straight_bus_stop.name})的直线距离{min_straight_distance}米，符合要求（<= {max_bus_stop_straight_distance}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 776.py 文件...\n")
    result = verify_poi(poi_id="B0L2VA7PYB")
    print(f"\n验证结果: {result}")
