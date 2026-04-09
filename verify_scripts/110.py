
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 用 maps_around_search(location=103.745681,29.599325; radius=2000; keywords=便利店) 验证 target_poi_id 在返回列表中（满足"附近2km内的便利店"）。
2) 用 maps_search_detail(id=target_poi_id) 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 便利店坐标 destination。
3) 用(address=乐山站, city=乐山) 获取乐山站坐标 station_loc。
4) 用 maps_walking_by_coordinates(origin=103.745681,29.599325; destination=destination) 得到步行时长 t_walk，验证 t_walk <= 12*60。
5) 用 maps_driving_by_coordinates(origin=103.745681,29.599325; destination=destination) 得到驾车时长 t_drive_to_store，验证 t_walk - t_drive_to_store >= 8*60。
6) 用 maps_driving_by_coordinates(origin=destination; destination=station_loc) 得到 poi_id，再 maps_search_detail(id=poi_id) 得到 驾车时长 t_drive_to_station，验证 t_drive_to_station <= 10*60。
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
    maps_text_search,
    maps_search_detail ,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "103.745681,29.599325",
    search_radius: int = 2000,  # 2km
    keywords: str = "便利店",
    max_walking_duration: int = 720,  # 12 minutes = 720 seconds
    min_time_diff: int = 480,  # 8 minutes = 480 seconds
    station_address: str = "乐山站",
    station_city: str = "乐山",
    max_driving_to_station: int = 600  # 10 minutes = 600 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 用 maps_around_search 验证 target_poi_id 在返回列表中（满足"附近2km内的便利店"）。
    2) 用 maps_search_detail 获取便利店坐标 destination。
    3) 用获取乐山站坐标 station_loc。
    4) 用 maps_walking_by_coordinates 得到步行时长 t_walk，验证 t_walk <= 12*60。
    5) 用 maps_driving_by_coordinates 得到驾车时长 t_drive_to_store，验证 t_walk - t_drive_to_store >= 8*60。
    6) 用 maps_driving_by_coordinates 得到驾车时长 t_drive_to_station，验证 t_drive_to_station <= 10*60。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"103.745681,29.599325"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"便利店"
        max_walking_duration: 最大步行时长（秒），默认720（12分钟）
        min_time_diff: 步行与驾车时长最小差值（秒），默认480（8分钟）
        station_address: 车站地址，默认"乐山站"
        station_city: 车站所在城市，默认"乐山"
        max_driving_to_station: 到车站最大驾车时长（秒），默认600（10分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近2km内的便利店
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

    # 步骤2: 获取便利店坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    destination = poi_detail.location
    print(f"✅ 获取便利店坐标: {destination}")

    # 步骤3: 获取乐山站坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"❌ 获取车站坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到车站坐标")
        return False

    first_poi_id = station_text_result.pois[0].id
    station_detail_result = maps_search_detail(id=first_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取坐标失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print("❌ 未获取到坐标")
        return False

    station_loc = station_detail_result.location
    print(f"✅ 获取车站坐标: {station_loc} ({station_address})")

    # 步骤4: 步行时长验证
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=destination)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    t_walk = walking_result.total_duration_seconds
    if t_walk > max_walking_duration:
        print(f"❌ 步行时长{t_walk}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{t_walk}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    # 步骤5: 驾车时长验证（步行与驾车时长差值）
    driving_to_store_result = maps_driving_by_coordinates(origin=user_location, destination=destination)
    if driving_to_store_result.error:
        print(f"❌ 计算驾车路线失败: {driving_to_store_result.error}")
        return False

    if driving_to_store_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    t_drive_to_store = driving_to_store_result.total_duration_seconds
    time_diff = t_walk - t_drive_to_store
    if time_diff < min_time_diff:
        print(f"❌ 步行与驾车时长差值{time_diff}秒，小于{min_time_diff}秒（{min_time_diff // 60}分钟）")
        return False
    print(f"✅ 步行与驾车时长差值{time_diff}秒，符合要求（>= {min_time_diff}秒，即{min_time_diff // 60}分钟）")

    # 步骤6: 到车站驾车时长验证
    driving_to_station_result = maps_driving_by_coordinates(origin=destination, destination=station_loc)
    if driving_to_station_result.error:
        print(f"❌ 计算到车站驾车路线失败: {driving_to_station_result.error}")
        return False

    if driving_to_station_result.total_duration_seconds is None:
        print(f"❌ 无法获取到车站驾车时长")
        return False

    t_drive_to_station = driving_to_station_result.total_duration_seconds
    if t_drive_to_station > max_driving_to_station:
        print(f"❌ 到车站驾车时长{t_drive_to_station}秒，超过{max_driving_to_station}秒（{max_driving_to_station // 60}分钟）")
        return False
    print(f"✅ 到车站驾车时长{t_drive_to_station}秒，符合要求（<= {max_driving_to_station}秒，即{max_driving_to_station // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 719.py 文件...\n")
    result = verify_poi(poi_id="B0FFGSD8UW")
    print(f"\n验证结果: {result}")
