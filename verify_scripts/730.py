
"""
修改任务指令：你要在附近2公里内找一家医院（或社区卫生服务中心）临时处理一个紧急小问题。你打算走过去，所以全程步行不要超过25分钟。为了之后换乘方便，这个地方附近800米要有一个公交站，直线距离不超过150米。另外你还想避开"青岛市市立医院东院"周边，目标地点离它的直线距离必须至少800米。最后，你还需要确认从"青岛火车站"走到这家医院的步行时间不超过110分钟，确保外地来的家人也能到。你有礼貌但很固执，坚持自己的要求不让步。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 半径约束：调用 maps_around_search(location="120.408301,36.05369", radius="2000", keywords="医院")，验证返回pois中包含 target_poi_id=B0FFKM9E65。
2) 步行时长约束（你到医院<=25分钟）：调用 maps_walking_by_coordinates(origin="120.408301,36.05369", destination=POI.location)，验证 total_duration_seconds<=1500。
3) 公交站距离约束（<=150米直线距离）：以 POI.location 为中心调用 maps_around_search(radius="800", keywords="公交站")，选取其中最近的公交站POI；再调用 maps_distance(origins=POI.location, destination=该公交站.location)，验证 distance_meters<=150。
4) 排除半径约束（远离青岛市市立医院东院>=800米）：调用 maps_text_search(keywords="青岛市市立医院东院", city="青岛") 取 poi_id，再 maps_search_detail(id=poi_id) 得到 location_h；调用 maps_distance(origins=location_h, destination=POI.location)，验证 distance_meters>=800。
5) 交通枢纽步行时长约束（青岛火车站到医院<=110分钟）：调用 maps_text_search(keywords="青岛火车站", city="青岛") 取 poi_id，再 maps_search_detail(id=poi_id) 得到 location_s；调用 maps_walking_by_coordinates(origin=location_s, destination=POI.location)，验证 total_duration_seconds<=6600。
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
    maps_search_detail,
    maps_walking_by_coordinates,
    maps_distance,
    maps_around_search,
)


def verify_poi(
    poi_id: str,
    user_location: str = "120.408301,36.05369",
    search_radius: int = 2000,  # 2km
    keywords: str = "医院",
    max_walking_duration: int = 1500,  # 25 minutes = 1500 seconds
    bus_stop_search_radius: int = 800,  # 800m
    bus_stop_keywords: str = "公交站",
    max_distance_to_bus_stop: int = 150,  # 150m
    exclude_hospital_address: str = "青岛市市立医院东院",
    exclude_hospital_city: str = "青岛",
    min_distance_to_exclude: int = 800,  # 800m
    station_address: str = "青岛火车站",
    station_city: str = "青岛",
    max_walking_duration_from_station: int = 6600  # 110 minutes = 6600 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 半径约束：调用 maps_around_search，验证返回pois中包含 target_poi_id。
    2) 步行时长约束（你到医院<=25分钟）：调用 maps_walking_by_coordinates，验证 total_duration_seconds<=1500。
    3) 公交站距离约束（<=150米直线距离）：以 POI.location 为中心调用 maps_around_search，选取其中最近的公交站POI；再调用 maps_distance，验证 distance_meters<=150。
    4) 排除半径约束（远离青岛市市立医院东院>=800米）：调用得到location_h；调用 maps_distance，验证 distance_meters>=800。
    5) 交通枢纽步行时长约束（青岛火车站到医院<=110分钟）：调用得到location_s；调用 maps_walking_by_coordinates，验证 total_duration_seconds<=6600。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"120.408301,36.05369"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"医院"
        max_walking_duration: 最大步行时长（秒），默认1500（25分钟）
        bus_stop_search_radius: 公交站搜索半径（米），默认800
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_distance_to_bus_stop: 到公交站的最大直线距离（米），默认150
        exclude_hospital_address: 需要排除的医院地址，默认"青岛市市立医院东院"
        exclude_hospital_city: 需要排除的医院所在城市，默认"青岛"
        min_distance_to_exclude: 到排除医院的最小直线距离（米），默认800
        station_address: 火车站地址，默认"青岛火车站"
        station_city: 火车站所在城市，默认"青岛"
        max_walking_duration_from_station: 从火车站到医院的最大步行时长（秒），默认6600（110分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 半径约束（2公里内的医院）
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

    # 步骤3: 步行时长约束（你到医院<=25分钟）
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

    # 步骤4: 搜索医院附近800米内的公交站
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 医院附近{bus_stop_search_radius}米内未找到公交站")
        return False

    print(f"✅ 医院附近{bus_stop_search_radius}米内找到{len(bus_stop_search_result.pois)}个公交站")

    # 步骤5: 找到直线距离最近的公交站，验证距离<=150米
    min_distance = float('inf')
    closest_bus_stop = None

    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        distance_result = maps_distance(origins=poi_location, destination=bus_stop.location)
        if distance_result.error:
            continue

        if not distance_result.results or len(distance_result.results) == 0:
            continue

        distance_meters = distance_result.results[0].distance_meters
        # print(f"  - {bus_stop.name}: 直线距离{distance_meters}米")

        if distance_meters < min_distance:
            min_distance = distance_meters
            closest_bus_stop = bus_stop

    if closest_bus_stop is None:
        print(f"❌ 无法计算到公交站的直线距离")
        return False

    print(f"✅ 找到最近的公交站: {closest_bus_stop.name}，直线距离{min_distance}米")

    if min_distance > max_distance_to_bus_stop:
        print(f"❌ 到最近公交站的直线距离{min_distance}米，超过{max_distance_to_bus_stop}米")
        return False

    print(f"✅ 到最近公交站的直线距离符合要求（<= {max_distance_to_bus_stop}米）")

    # 步骤6: 获取需要排除的医院坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
    exclude_hospital_text_result = maps_text_search(keywords=exclude_hospital_address, city=exclude_hospital_city)
    if exclude_hospital_text_result.error:
        print(f"❌ 获取排除医院坐标失败: {exclude_hospital_text_result.error}")
        return False

    if not exclude_hospital_text_result.pois or len(exclude_hospital_text_result.pois) == 0:
        print(f"❌ 未找到排除医院坐标")
        return False

    first_poi_id = exclude_hospital_text_result.pois[0].id
    exclude_hospital_detail_result = maps_search_detail(id=first_poi_id)
    if exclude_hospital_detail_result.error:
        print(f"❌ 获取坐标失败: {exclude_hospital_detail_result.error}")
        return False
    if not exclude_hospital_detail_result.location:
        print("❌ 未获取到坐标")
        return False

    exclude_hospital_location = exclude_hospital_detail_result.location
    print(f"✅ 获取排除医院坐标: {exclude_hospital_location} ({exclude_hospital_address})")

    # 步骤7: 验证目标医院距离排除医院>=800米
    distance_to_exclude = maps_distance(origins=exclude_hospital_location, destination=poi_location)
    if distance_to_exclude.error:
        print(f"❌ 计算到排除医院的直线距离失败: {distance_to_exclude.error}")
        return False

    if not distance_to_exclude.results or len(distance_to_exclude.results) == 0:
        print(f"❌ 无法获取到排除医院的直线距离")
        return False

    distance_to_exclude_meters = distance_to_exclude.results[0].distance_meters
    if distance_to_exclude_meters < min_distance_to_exclude:
        print(f"❌ 到排除医院的直线距离{distance_to_exclude_meters}米，小于{min_distance_to_exclude}米")
        return False

    print(f"✅ 到排除医院的直线距离{distance_to_exclude_meters}米，符合要求（>= {min_distance_to_exclude}米）")

    # 步骤8: 获取火车站坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"❌ 获取火车站坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到火车站坐标")
        return False

    first_poi_id = station_text_result.pois[0].id
    station_detail_result = maps_search_detail(id=first_poi_id)
    if station_detail_result.error:

        print(f"❌ 获取坐标失败: {station_detail_result.error}")

        return False

    if not station_detail_result.location:

        print("❌ 未获取到坐标")

        return False

    station_location = station_detail_result.location
    print(f"✅ 获取火车站坐标: {station_location} ({station_address})")

    # 步骤9: 从火车站步行到医院的时间<=110分钟
    walking_from_station = maps_walking_by_coordinates(origin=station_location, destination=poi_location)
    if walking_from_station.error:
        print(f"❌ 计算从火车站到医院的步行路线失败: {walking_from_station.error}")
        return False

    if walking_from_station.total_duration_seconds is None:
        print(f"❌ 无法获取从火车站到医院的步行时长")
        return False

    walking_duration_from_station = walking_from_station.total_duration_seconds
    if walking_duration_from_station > max_walking_duration_from_station:
        print(f"❌ 从火车站到医院的步行时长{walking_duration_from_station}秒，超过{max_walking_duration_from_station}秒（{max_walking_duration_from_station // 60}分钟）")
        return False
    print(f"✅ 从火车站到医院的步行时长{walking_duration_from_station}秒，符合要求（<= {max_walking_duration_from_station}秒，即{max_walking_duration_from_station // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 730.py 文件...\n")
    result = verify_poi(poi_id="B0FFKM9E65")
    print(f"\n验证结果: {result}")

