
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_around_search(location=用户坐标124.883855,46.63491, radius=2500, keywords='医院')，验证返回结果中包含 poi_id=B01CB00XZY。
2) 调用 maps_bicycling_by_coordinates(origin=124.883855,46.63491, destination=目标POI的location) 获取骑行时长，验证 total_duration_seconds <= 360（6分钟）。
3) 调用 maps_search_detail(id=B01CB00XZY) 获取目标POI坐标location。
4) 调用 maps_around_search(location=目标POI的location, radius=500, keywords='公交站')，验证返回结果中存在名为"博瑞医院(公交站)"的POI（id=BV10478231）。
5) 调用 maps_distance(origins=目标POI的location, destination=公交站location=124.890761,46.636660)，验证 distance_meters <= 80。
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
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "124.883855,46.63491",
    search_radius: int = 2500,  # 2.5km
    keywords: str = "医院",
    max_bicycling_duration: int = 360,  # 6 minutes = 360 seconds
    bus_stop_search_radius: int = 500,  # 500 meters
    bus_stop_keywords: str = "公交站",
    expected_bus_stop_name: str = "博瑞医院(公交站)",
    expected_bus_stop_id: str = "BV10478231",
    bus_stop_location: str = "124.890761,46.636660",
    max_bus_stop_distance: int = 80  # 80 meters
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边验证：调用 maps_around_search，验证返回结果中包含 poi_id
    2) 骑行时间验证：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds <= 360
    3) 获取目标POI坐标：调用 maps_search_detail
    4) 公交站验证：调用 maps_around_search，验证返回结果中存在指定公交站
    5) 距离验证：调用 maps_distance，验证 distance_meters <= 80

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"124.883855,46.63491"
        search_radius: 搜索半径（米），默认2500（2.5公里）
        keywords: 搜索���键词，默认"医院"
        max_bicycling_duration: 最大骑行时长（秒），默认360（6分钟）
        bus_stop_search_radius: 公交站搜索半径（米），默认500
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        expected_bus_stop_name: 期望的公交站名称，默认"博瑞医院(公交站)"
        expected_bus_stop_id: 期望的公交站ID，默认"BV10478231"
        bus_stop_location: 公交站坐标，默认"124.890761,46.636660"
        max_bus_stop_distance: 到公交站最大距离（米），默认80

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边验证（2.5公里内的医院）
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

    # 步骤3: 获取目标POI详情（注意：虽然注释中步骤3在步骤2之后，但实际需要先获取坐标才能计算骑行时间）
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤2: 骑行时间验证（<= 6分钟）
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取骑行时长")
        return False

    bicycling_duration = bicycling_result.total_duration_seconds
    if bicycling_duration > max_bicycling_duration:
        print(f"❌ 骑行时长{bicycling_duration}秒，超过{max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 骑行时长{bicycling_duration}秒，符合要求（<= {max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")

    # 步骤4: 公交站验证（500米范围内）
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索周边公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ {bus_stop_search_radius}米范围内未找到公交站")
        return False

    # 检查是否存在指定的公交站
    bus_stop_found = False
    for poi in bus_stop_search_result.pois:
        if poi.id == expected_bus_stop_id or poi.name == expected_bus_stop_name:
            bus_stop_found = True
            print(f"✅ {bus_stop_search_radius}米范围内找到指定公交站: {poi.name} (ID: {poi.id})")
            break

    if not bus_stop_found:
        print(f"❌ {bus_stop_search_radius}米范围内未找到指定公交站 {expected_bus_stop_name}")
        return False

    # 步骤5: 距离验证（<= 80米）
    distance_result = maps_distance(origins=poi_location, destination=bus_stop_location)
    if distance_result.error:
        print(f"❌ 计算到公交站距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取到公交站距离")
        return False

    bus_stop_distance = distance_result.results[0].distance_meters
    if bus_stop_distance > max_bus_stop_distance:
        print(f"❌ 到公交站距离{bus_stop_distance}米，超过{max_bus_stop_distance}米")
        return False
    print(f"✅ 到公交站距离{bus_stop_distance}米，符合要求（<= {max_bus_stop_distance}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 581.py 文件...\n")
    result = verify_poi(poi_id="B01CB00XZY")
    print(f"\n验证结果: {result}")
