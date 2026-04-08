
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_around_search(location="106.086287,30.782757", radius="3000", keywords="百货商店")，验证返回pois数量>=8，且目标poi_id=B0FFGZ2ERL在pois列表中（满足"附近3公里内、百货商店"）。
2) 调用 maps_walking_by_coordinates(origin="106.086287,30.782757", destination=location_poi)，验证 total_duration_seconds<=720（12分钟） 且 total_distance_meters<=1200（1.2公里）。
3) 调用 maps_text_search(keywords="南充高坪机场", city="南充") 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取机场坐标location_airport；再调用 maps_driving_by_coordinates(origin=location_poi, destination=location_airport)，验证 total_duration_seconds<=900（15分钟）。
4) 调用 maps_text_search(keywords="南充站", city="南充", citylimit="true") 取返回列表中名为"南充站"的POI（id=B033100HZZ）；调用 maps_search_detail(id="B033100HZZ") 获取南充站坐标location_station；调用 maps_distance(origins=location_poi, destination=location_station)，验证 distance_meters<=3000（3公里）
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
    maps_walking_by_coordinates,
    maps_driving_by_coordinates,
    maps_text_search,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "106.086287,30.782757",
    search_radius: int = 3000,  # 3km
    keywords: str = "百货商店",
    min_poi_count: int = 8,
    max_walking_duration: int = 720,  # 12 minutes = 720 seconds
    max_walking_distance: int = 1200,  # 1.2km = 1200 meters
    airport_address: str = "南充高坪机场",
    airport_city: str = "南充",
    max_driving_duration: int = 900,  # 15 minutes = 900 seconds
    station_keywords: str = "南充站",
    station_city: str = "南充",
    station_id: str = "B033100HZZ",
    max_distance: int = 3000  # 3km = 3000 meters
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边搜索约束：验证返回pois数量>=8，且目标poi_id在pois列表中
    2) 步行时间和距离约束：验证步行时长<=12分钟 且 步行距离<=1.2公里
    3) 机场驾车时间约束：验证驾车时长<=15分钟
    4) 火车站距离约束：验证距离<=3公里

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"106.086287,30.782757"
        search_radius: 搜索半径（米），默认3000（3公里）
        keywords: 搜索关键词，默认"百货商店"
        min_poi_count: 最少POI数量，默认8
        max_walking_duration: 最大步行时长（秒），默认720（12分钟）
        max_walking_distance: 最大步行距离（米），默认1200（1.2公里）
        airport_address: 机场地址，默认"南充高坪机场"
        airport_city: 机场所在城市，默认"南充"
        max_driving_duration: 最大驾车时长（秒），默认900（15分钟）
        station_keywords: 火车站搜索关键词，默认"南充站"
        station_city: 火车站所在城市，默认"南充"
        station_id: 火车站POI ID，默认"B033100HZZ"
        max_distance: 最大距离（米），默认3000（3公里）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边搜索约束（附近3公里内的百货商店）
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

    # 获取目标POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤2: 步行时间和距离约束
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    if walking_result.total_distance_meters is None:
        print(f"❌ 无法获取步行距离")
        return False

    walking_duration = walking_result.total_duration_seconds
    walking_distance = walking_result.total_distance_meters

    # 验证步行时长（<= 12分钟）
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    # 验证步行距离（<= 1.2公里）
    if walking_distance > max_walking_distance:
        print(f"❌ 步行距离{walking_distance}米，超过{max_walking_distance}米（{max_walking_distance / 1000}公里）")
        return False
    print(f"✅ 步行距离{walking_distance}米，符合要求（<= {max_walking_distance}米，即{max_walking_distance / 1000}公里）")

    # 步骤3: 用 maps_text_search + maps_search_detail 获取机场坐标，机场驾车时间约束
    text_search_result = maps_text_search(keywords=airport_address, city=airport_city)
    if text_search_result.error:
        print(f"❌ 获取{airport_address}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{airport_address}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{airport_address}坐标失败: {detail_result.error or '无location'}")
        return False

    airport_location = detail_result.location
    print(f"✅ 获取{airport_address}坐标: {airport_location}")

    # 验证驾车时间（<= 15分钟）
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=airport_location)
    if driving_result.error:
        print(f"❌ 计算到{airport_address}驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{airport_address}驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到{airport_address}驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{airport_address}驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    # 步骤4: 火车站距离约束
    # 使用文本搜索获取火车站信息
    station_search_result = maps_text_search(keywords=station_keywords, city=station_city, citylimit="true")
    if station_search_result.error:
        print(f"❌ 搜索{station_keywords}失败: {station_search_result.error}")
        return False

    if not station_search_result.pois or len(station_search_result.pois) == 0:
        print(f"❌ 未找到{station_keywords}")
        return False

    # 查找名为"南充站"的POI
    station_poi = None
    for poi in station_search_result.pois:
        if poi.name == station_keywords or poi.id == station_id:
            station_poi = poi
            print(f"✅ 找到{station_keywords}: {poi.name} (ID: {poi.id})")
            break

    if not station_poi:
        print(f"❌ 未找到名为{station_keywords}的POI")
        return False

    # 获取火车站详细坐标
    station_detail = maps_search_detail(id=station_poi.id)
    if station_detail.error:
        print(f"❌ 获取{station_keywords}详情失败: {station_detail.error}")
        return False

    if not station_detail.location:
        print(f"❌ {station_keywords}没有location信息")
        return False

    station_location = station_detail.location
    print(f"✅ 获取{station_keywords}坐标: {station_location}")

    # 验证距离（<= 3公里）
    distance_result = maps_distance(origins=poi_location, destination=station_location)
    if distance_result.error:
        print(f"❌ 计算到{station_keywords}距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取到{station_keywords}距离")
        return False

    distance_meters = distance_result.results[0].distance_meters
    if distance_meters > max_distance:
        print(f"❌ 到{station_keywords}距离{distance_meters}米，超过{max_distance}米（{max_distance / 1000}公里）")
        return False
    print(f"✅ 到{station_keywords}距离{distance_meters}米，符合要求（<= {max_distance}米，即{max_distance / 1000}公里）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 571.py 文件...\n")
    result = verify_poi(poi_id="B0FFGZ2ERL")
    print(f"\n验证结果: {result}")
