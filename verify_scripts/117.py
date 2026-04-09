
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_around_search(location=用户坐标116.579578,35.409123, radius=2000, keywords=医院)，验证返回pois中包含目标poi_id=B02190ACFF。
2) 调用 maps_search_detail(id=B02190ACFF) 获取目标POI坐标 destination。
3) 调用 maps_driving_by_coordinates(origin=116.579578,35.409123, destination=destination)，验证 total_duration_seconds <= 300（5分钟）。
4) 调用 maps_walking_by_coordinates(origin=116.579578,35.409123, destination=destination)，验证 total_duration_seconds <= 720（12分钟）。
5) 调用 maps_text_search(keywords=济宁汽车总站, city=济宁, citylimit=true) 获取总站poi_id=B0219057F8；再调用 maps_search_detail(id=B0219057F8) 获取总站坐标 station_loc。
6) 调用 maps_distance(origins=destination, destination=station_loc)，验证 distance_meters <= 2200。
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
    maps_driving_by_coordinates,
    maps_walking_by_coordinates,
    maps_text_search,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "116.579578,35.409123",
    search_radius: int = 2000,  # 2km
    keywords: str = "医院",
    max_driving_duration: int = 300,  # 5 minutes = 300 seconds
    max_walking_duration: int = 720,  # 12 minutes = 720 seconds
    station_keywords: str = "济宁汽车总站",
    station_city: str = "济宁",
    max_distance_to_station: int = 2200  # 2200m
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 调用 maps_search_detail 获取目标POI坐标 destination。
    3) 调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 300。
    4) 调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 720。
    5) 调用 maps_text_search 获取总站poi_id；再调用 maps_search_detail 获取总站坐标 station_loc。
    6) 调用 maps_distance，验证 distance_meters <= 2200。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.579578,35.409123"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"医院"
        max_driving_duration: 最大驾车时长（秒），默认300（5分钟）
        max_walking_duration: 最大步行时长（秒），默认720（12分钟）
        station_keywords: 汽车站搜索关键词，默认"济宁汽车总站"
        station_city: 汽车站所在城市，默认"济宁"
        max_distance_to_station: 到汽车站的最大直线距离（米），默认2200

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（2公里内的医院）
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

    # 步骤3: 驾车时间<=5分钟
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    # 步骤4: 步行时间<=12分钟
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

    # 步骤5: 搜索济宁汽车总站
    text_search_result = maps_text_search(keywords=station_keywords, city=station_city, citylimit=True)
    if text_search_result.error:
        print(f"❌ 搜索汽车站失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{station_keywords}")
        return False

    # 获取第一个结果作为汽车站
    station_poi = text_search_result.pois[0]
    print(f"✅ 找到汽车站: {station_poi.name} (ID: {station_poi.id})")

    # 步骤6: 获取汽车站详情
    station_detail = maps_search_detail(id=station_poi.id)
    if station_detail.error:
        print(f"❌ 获取汽车站详情失败: {station_detail.error}")
        return False

    if not station_detail.location:
        print(f"❌ 汽车站没有location信息")
        return False

    station_location = station_detail.location
    print(f"✅ 获取汽车站坐标: {station_location}")

    # 步骤7: 计算到汽车站的直线距离
    distance_result = maps_distance(origins=poi_location, destination=station_location)
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取直线距离")
        return False

    distance_meters = distance_result.results[0].distance_meters
    if distance_meters > max_distance_to_station:
        print(f"❌ 到汽车站的直线距离{distance_meters}米，超过{max_distance_to_station}米")
        return False

    print(f"✅ 到汽车站的直线距离{distance_meters}米，符合要求（<= {max_distance_to_station}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 729.py 文件...\n")
    result = verify_poi(poi_id="B02190ACFF")
    print(f"\n验证结果: {result}")
