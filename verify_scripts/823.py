"""
修改任务指令：你要在附近2000米以内找一家展览馆。你希望从你这里走过去全程不超过20分钟，而且开车过去的路程不要超过3公里。展览馆附近300米内必须有公共厕所。你还希望展览馆附近800米内离最近的地铁站直线距离不超过500米，并且从展览馆走到最近的公交站不超过6分钟。最后，你计划参观完直接打车去合肥火车站，要求从展览馆开车到火车站不超过12分钟。你善于使用强制和协商的策略来达到目的。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2000米内：调用 maps_around_search(location='117.28356,31.877655', radius='2000', keywords='展览馆')，验证返回pois中包含 target_poi_id=B0IDRA7YGJ。
2) 从出发地步行≤20分钟：调用 maps_walking_by_coordinates(origin='117.28356,31.877655', destination='117.287844,31.865357')，验证 total_duration_seconds ≤ 1200。
3) 从出发地驾车距离≤3公里：调用 maps_driving_by_coordinates(origin='117.28356,31.877655', destination='117.287844,31.865357')，验证 total_distance_meters ≤ 3000。
4) 展览馆300米内有公共厕所：调用 maps_around_search(location='117.287844,31.865357', radius='300', keywords='公共厕所')，验证 pois 数量≥1。
5) 最近地铁站直线距离≤500米：调用 maps_around_search(location='117.287844,31.865357', radius='800', keywords='地铁站') 获取候选地铁站列表；对每个候选站用 maps_distance(origins=station.location, destination='117.287844,31.865357') 计算直线距离，取最小值，验证 ≤500。
6) 到最近公交站步行≤6分钟：调用 maps_around_search(location='117.287844,31.865357', radius='500', keywords='公交站') 获取候选公交站列表；对每个候选站调用 maps_walking_by_coordinates(origin='117.287844,31.865357', destination=station.location) 计算步行时间，取最小值，验证 total_duration_seconds ≤ 360。
7) 展览馆到合肥火车站驾车≤12分钟：调用 maps_text_search(keywords='合肥火车站', city='合肥') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 得到火车站坐标；再调用 maps_driving_by_coordinates(origin='117.287844,31.865357', destination=火车站坐标)，验证 total_duration_seconds ≤ 720。
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
    maps_distance,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "117.28356,31.877655",
    poi_location: str = "117.287844,31.865357",
    search_radius: int = 2000,
    keywords: str = "展览馆",
    max_walking_duration: int = 1200,  # 20 minutes = 1200 seconds
    max_driving_distance: int = 3000,  # 3 km = 3000 meters
    toilet_search_radius: int = 300,
    toilet_keywords: str = "公共厕所",
    subway_search_radius: int = 800,
    subway_keywords: str = "地铁站",
    max_subway_straight_distance: int = 500,  # 500 meters
    bus_stop_search_radius: int = 500,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_walking_duration: int = 360,  # 6 minutes = 360 seconds
    station_address: str = "合肥火车站",
    station_city: str = "合肥",
    max_station_driving_duration: int = 720  # 12 minutes = 720 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近2000米内：调用 maps_around_search，验证返回pois中包含target_poi_id。
    2) 从出发地步行≤20分钟：调用 maps_walking_by_coordinates，验证 total_duration_seconds ≤ 1200。
    3) 从出发地驾车距离≤3公里：调用 maps_driving_by_coordinates，验证 total_distance_meters ≤ 3000。
    4) 展览馆300米内有公共厕所：调用 maps_around_search，验证 pois 数量≥1。
    5) 最近地铁站直线距离≤500米：调用 maps_around_search 获取地铁站列表，用 maps_distance 计算直线距离，取最小值，验证 ≤500。
    6) 到最近公交站步行≤6分钟：调用 maps_around_search 获取公交站列表，调用 maps_walking_by_coordinates 计算步行时间，取最小值，验证 ≤ 360。
    7) 展览馆到合肥火车站驾车≤12分钟：调用 maps_text_search 获取 poi_id，再用 maps_search_detail 得到火车站坐标，再调用 maps_driving_by_coordinates，验证 total_duration_seconds ≤ 720。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"117.28356,31.877655"
        poi_location: POI坐标，格式为"经度,纬度"，默认"117.287844,31.865357"
        search_radius: 搜索半径（米），默认2000
        keywords: 搜索关键词，默认"展览馆"
        max_walking_duration: 最大步行时长（秒），默认1200（20分钟）
        max_driving_distance: 最大驾车距离（米），默认3000
        toilet_search_radius: 公共厕所搜索半径（米），默认300
        toilet_keywords: 公共厕所搜索关键词，默认"公共厕所"
        subway_search_radius: 地铁站搜索半径（米），默认800
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_subway_straight_distance: 到地铁站最大直线距离（米），默认500
        bus_stop_search_radius: 公交站搜索半径（米），默认500
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_walking_duration: 到公交站最大步行时长（秒），默认360（6分钟）
        station_address: 火车站地址，默认"合肥火车站"
        station_city: 火车站所在城市，默认"合肥"
        max_station_driving_duration: 到火车站最大驾车时长（秒），默认720（12分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近2000米内
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

    # 步骤2: 从出发地步行≤20分钟
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

    # 步骤3: 从出发地驾车距离≤3公里
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False

    driving_distance = driving_result.total_distance_meters
    if driving_distance > max_driving_distance:
        print(f"❌ 驾车距离{driving_distance}米，超过{max_driving_distance}米")
        return False
    print(f"✅ 驾车距离{driving_distance}米，符合要求（<= {max_driving_distance}米）")

    # 步骤4: 展览馆300米内有公共厕所
    toilet_search_result = maps_around_search(
        location=poi_location,
        radius=str(toilet_search_radius),
        keywords=toilet_keywords
    )
    if toilet_search_result.error:
        print(f"❌ 搜索公共厕所失败: {toilet_search_result.error}")
        return False

    if not toilet_search_result.pois or len(toilet_search_result.pois) == 0:
        print(f"❌ 未找到公共厕所")
        return False

    print(f"✅ 找到{len(toilet_search_result.pois)}个公共厕所")

    # 步骤5: 最近地铁站直线距离≤500米
    subway_search_result = maps_around_search(
        location=poi_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 未找到地铁站")
        return False

    print(f"✅ 找到{len(subway_search_result.pois)}个地铁站")

    # 将所有地铁站坐标拼成origins
    subway_locations = []
    for subway in subway_search_result.pois:
        if subway.location:
            subway_locations.append(subway.location)

    if len(subway_locations) == 0:
        print(f"❌ 没有地铁站有坐标信息")
        return False

    origins_str = "|".join(subway_locations)
    distance_result = maps_distance(origins=origins_str, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未获取到距离信息")
        return False

    # 找到最小直线距离
    min_subway_straight_distance = None
    for result in distance_result.results:
        if min_subway_straight_distance is None or result.distance_meters < min_subway_straight_distance:
            min_subway_straight_distance = result.distance_meters

    if min_subway_straight_distance is None:
        print(f"❌ 无法计算最小直线距离")
        return False

    if min_subway_straight_distance > max_subway_straight_distance:
        print(f"❌ 最近地铁站直线距离{min_subway_straight_distance}米，超过{max_subway_straight_distance}米")
        return False
    print(f"✅ 最近地铁站直线距离{min_subway_straight_distance}米，符合要求（<= {max_subway_straight_distance}米）")

    # 步骤6: 到最近公交站步行≤6分钟
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

    # 计算到每个公交站的步行时间，找到最小值
    min_bus_stop_walking_duration = None
    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        bus_stop_walking_result = maps_walking_by_coordinates(
            origin=poi_location,
            destination=bus_stop.location
        )
        if bus_stop_walking_result.error or bus_stop_walking_result.total_duration_seconds is None:
            continue

        duration = bus_stop_walking_result.total_duration_seconds
        if min_bus_stop_walking_duration is None or duration < min_bus_stop_walking_duration:
            min_bus_stop_walking_duration = duration

    if min_bus_stop_walking_duration is None:
        print(f"❌ 无法计算到公交站的步行时间")
        return False

    if min_bus_stop_walking_duration > max_bus_stop_walking_duration:
        print(f"❌ 到最近公交站步行时长{min_bus_stop_walking_duration}秒，超过{max_bus_stop_walking_duration}秒（{max_bus_stop_walking_duration // 60}分钟）")
        return False
    print(f"✅ 到最近公交站步行时长{min_bus_stop_walking_duration}秒，符合要求（<= {max_bus_stop_walking_duration}秒，即{max_bus_stop_walking_duration // 60}分钟）")

    # 步骤7: 展览馆到合肥火车站驾车≤12分钟
    text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if text_search_result.error:
        print(f"❌ 获取{station_address}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{station_address}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{station_address}坐标失败: {detail_result.error or '无location'}")
        return False

    station_location = detail_result.location
    print(f"✅ 获取{station_address}坐标: {station_location}")

    station_driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if station_driving_result.error:
        print(f"❌ 计算到{station_address}驾车路线失败: {station_driving_result.error}")
        return False

    if station_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{station_address}驾车时长")
        return False

    station_driving_duration = station_driving_result.total_duration_seconds
    if station_driving_duration > max_station_driving_duration:
        print(f"❌ 到{station_address}驾车时长{station_driving_duration}秒，超过{max_station_driving_duration}秒（{max_station_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_address}驾车时长{station_driving_duration}秒，符合要求（<= {max_station_driving_duration}秒，即{max_station_driving_duration // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 823.py 文件...\n")
    result = verify_poi(poi_id="B0IDRA7YGJ")
    print(f"\n验证结果: {result}")
