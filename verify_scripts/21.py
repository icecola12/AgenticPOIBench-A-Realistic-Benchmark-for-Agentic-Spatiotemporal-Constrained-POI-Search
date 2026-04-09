
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 用 maps_around_search(location=118.302894,33.958561, radius=2000, keywords=自习室) 验证 target_poi_id 在返回列表中（满足"附近2公里内的自习室"）
2) 用 maps_walking_by_coordinates(origin=118.302894,33.958561, destination=目标POI的location) 得到步行时长t_walk，验证 t_walk <= 15分钟
3) 用 maps_text_search(keywords=宿迁站, city=宿迁) 获取"宿迁站"的poi_id，并用 maps_search_detail 得到其location
4) 用 maps_driving_by_coordinates(origin=目标POI的location, destination=宿迁站location) 得到驾车时长t_drive_station，验证 t_drive_station <= 25分钟
5) 用 maps_search_detail(id=BV11659585) 获取"中央商场(公交站)"的location；再用 maps_distance(origins=公交站location, destination=目标POI的location) 得到距离d，验证 d <= 200米
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
    maps_text_search,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "118.302894,33.958561",
    max_walking_duration: int = 900,  # 15 minutes = 900 seconds
    search_radius: int = 2000,  # 2km
    keywords: str = "自习室",
    station_keywords: str = "宿迁站",
    station_city: str = "宿迁",
    max_driving_duration: int = 1500,  # 25 minutes = 1500 seconds
    bus_stop_id: str = "BV11659585",
    max_distance: int = 200  # 200 meters
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 用 maps_around_search 验证 target_poi_id 在返回列表中（满足"附近2公里内的自习室"）
    2) 用 maps_walking_by_coordinates 得到步行时长t_walk，验证 t_walk <= 15分钟
    3) 用 maps_text_search 获取"宿迁站"的poi_id，并用 maps_search_detail 得到其location
    4) 用 maps_driving_by_coordinates 得到驾车时长t_drive_station，验证 t_drive_station <= 25分钟
    5) 用 maps_search_detail 获取"中央商场(公交站)"的location；再用 maps_distance 得到距离d，验证 d <= 200米

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"118.302894,33.958561"
        max_walking_duration: 最大步行时长（秒），默认900（15分钟）
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"自习室"
        station_keywords: 车站搜索关键词，默认"宿迁站"
        station_city: 车站所在城市，默认"宿迁"
        max_driving_duration: 最大驾车时长（秒），默认1500（25分钟）
        bus_stop_id: 公交站ID，默认"BV11659585"
        max_distance: 最大距离（米），默认200

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（附近2公里内的自习室）
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

    # 步骤2: 获取目标POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 步行时间<=15分钟
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

    # 步骤4: 获取宿迁站坐标
    station_search_result = maps_text_search(keywords=station_keywords, city=station_city)
    if station_search_result.error:
        print(f"❌ 搜索{station_keywords}失败: {station_search_result.error}")
        return False

    if not station_search_result.pois or len(station_search_result.pois) == 0:
        print(f"❌ 未找到{station_keywords}")
        return False

    station_poi_id = station_search_result.pois[0].id
    print(f"✅ 找到{station_keywords}: {station_search_result.pois[0].name} (ID: {station_poi_id})")

    station_detail = maps_search_detail(id=station_poi_id)
    if station_detail.error:
        print(f"❌ 获取{station_keywords}详情失败: {station_detail.error}")
        return False

    if not station_detail.location:
        print(f"❌ {station_keywords}没有location信息")
        return False

    station_location = station_detail.location
    print(f"✅ 获取{station_keywords}坐标: {station_location}")

    # 步骤5: 驾车时间<=25分钟
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到{station_keywords}驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_keywords}驾车时长{driving_duration}秒���符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    # 步骤6: 公交站距离<=200米
    bus_stop_detail = maps_search_detail(id=bus_stop_id)
    if bus_stop_detail.error:
        print(f"❌ 获取公交站详情失败: {bus_stop_detail.error}")
        return False

    if not bus_stop_detail.location:
        print(f"❌ 公交站没有location信息")
        return False

    bus_stop_location = bus_stop_detail.location
    print(f"✅ 获取公交站坐标: {bus_stop_location} ({bus_stop_detail.name})")

    distance_result = maps_distance(origins=bus_stop_location, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取距离")
        return False

    distance = distance_result.results[0].distance_meters
    if distance > max_distance:
        print(f"❌ 到公交站距离{distance}米，超过{max_distance}米")
        return False
    print(f"✅ 到公交站距离{distance}米，符合要求（<= {max_distance}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 495.py 文件...\n")
    result = verify_poi(poi_id="B0JGU1INQO")
    print(f"\n验证结果: {result}")


