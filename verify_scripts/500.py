
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围验证：调用 maps_around_search(location="94.355729,29.652914", radius="5000", keywords="银行")，确认返回POI数量>=8，且目标poi_id=B037E004DQ在返回列表中。
2) POI详情验证：对poi_id=B037E004DQ调用 maps_search_detail(id="B037E004DQ") 获取其location=94.358891,29.649315。
3) 步行时间验证：调用 maps_walking_by_coordinates(origin="94.355729,29.652914", destination="94.358891,29.649315")，得到步行时长t_walk=414秒，验证 t_walk <= 12*60 秒。
4) 公交站距离与到火车站打车时间验证：
4.1 调用 maps_text_search(keywords="八一大街公交站", city="林芝") 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取公交站坐标bs_loc；再调用 maps_distance(origins="94.358891,29.649315", destination=bs_loc) 得到距离d_bus，验证 d_bus<=1000米。
4.2 调用 maps_text_search(keywords="林芝火车站", city="林芝", citylimit="true") 获取林芝站poi_id=B0GUNZHGLQ；再调用 maps_search_detail(id="B0GUNZHGLQ") 获取其location=94.437555,29.527414。
4.3 调用 maps_driving_by_coordinates(origin="94.358891,29.649315", destination="94.437555,29.527414") 得到驾车时长t_drive=1849秒，验证 t_drive <= 35*60 秒。
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
    maps_walking_by_coordinates,
    maps_driving_by_coordinates,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "94.355729,29.652914",
    search_radius: int = 5000,  # 5km
    keywords: str = "银行",
    min_poi_count: int = 8,
    max_walking_duration: int = 720,  # 12 minutes = 720 seconds
    bus_stop_address: str = "八一大街公交站",
    bus_stop_city: str = "林芝",
    max_bus_stop_distance: int = 1000,  # 1000 meters
    station_keywords: str = "林芝火车站",
    station_city: str = "林芝",
    max_driving_duration: int = 2100  # 35 minutes = 2100 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边范围验证：调用 maps_around_search，确认返回POI数量>=8，且目标poi_id在返回列表中
    2) POI详情验证：调用 maps_search_detail 获取其location
    3) 步行时间验证：调用 maps_walking_by_coordinates，验证 t_walk <= 12*60 秒
    4) 公交站距离与到火车站打车时间验证：
       4.1 调用 maps_text_search 获取 poi_id，再用 maps_search_detail 获取公交站坐标，调用 maps_distance 验证 d_bus<=1000米
       4.2 调用 maps_text_search 获取林芝站poi_id，调用 maps_search_detail 获取其location
       4.3 调用 maps_driving_by_coordinates 验证 t_drive <= 35*60 秒

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"94.355729,29.652914"
        search_radius: 搜索半径（米），默认5000（5公里）
        keywords: 搜索关键词，默认"银行"
        min_poi_count: 最少POI数量，默认8
        max_walking_duration: 最大步行时长（秒），默认720（12分钟）
        bus_stop_address: 公交站地址，默认"八一大街公交站"
        bus_stop_city: 公交站所在城市，默认"林芝"
        max_bus_stop_distance: 到公交站最大距离（米），默认1000
        station_keywords: 火车站搜索关键词，默认"林芝火车站"
        station_city: 火车站所在城市，默认"林芝"
        max_driving_duration: 最大驾车时长（秒），默认2100（35分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围验证（附近5公里内的银行）
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

    # 检查返回POI数量是否>=8
    poi_count = len(around_search_result.pois)
    if poi_count < min_poi_count:
        print(f"❌ 返回POI数量{poi_count}个，少于{min_poi_count}个")
        return False
    print(f"✅ 返回POI数量{poi_count}个，符合要求（>= {min_poi_count}个）")

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

    # 步骤3: 步行时间验证（<= 12分钟）
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

    # 步骤4.1: 用 maps_text_search + maps_search_detail 获取公交站坐标并验证距离
    text_search_result = maps_text_search(keywords=bus_stop_address, city=bus_stop_city)
    if text_search_result.error:
        print(f"❌ 获取公交站坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到公交站坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取公交站坐标失败: {detail_result.error or '无location'}")
        return False

    bus_stop_location = detail_result.location
    print(f"✅ 获取公交站坐标: {bus_stop_location} ({bus_stop_address})")

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

    # 步骤4.2: 获取火车站坐标
    station_search_result = maps_text_search(keywords=station_keywords, city=station_city, citylimit="true")
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

    # 步骤4.3: 驾车时间验证（<= 35分钟）
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
    print(f"✅ 到{station_keywords}驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 500.py 文件...\n")
    result = verify_poi(poi_id="B037E004DQ")
    print(f"\n验证结果: {result}")
