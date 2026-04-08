
"""
修改任务指令：你想在附近3000米以内找一家自习室。你希望这家自习室走路去最近的公交站不超过6分钟，而且这个最近的公交站必须在自习室1200米范围内。你还要求自习室到这些公交站里直线距离最近的那个，直线距离不超过250米。你计划从自习室再打车去恩施站，开车过去不超过12分钟。另外，你从现在位置走去自习室的路上，路线中间希望能存在一个途经点，在它周围300米内能找到药店。你对服务和解决方案持怀疑态度。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近约束（3000米内）：调用maps_around_search(location='109.485312,30.297849', radius='3000', keywords='自习室')，验证返回pois中包含target_poi_id='B0LR0AM566'。
2) 自习室详情（取坐标用于后续计算）：调用maps_search_detail(id='B0LR0AM566')，获取自习室坐标location='109.498166,30.292300'。
3) 公交站集合（1200米范围内）：调用maps_around_search(location='109.498166,30.292300', radius='1200', keywords='公交站')，得到公交站POI列表S。
4) 最近公交站直线距离≤250米：将S中所有公交站坐标拼成origins，调用maps_distance(origins=..., destination='109.498166,30.292300')，取最小distance_meters，验证≤250。
5) 走路到最近公交站≤6分钟：取步骤4中直线距离最小对应的公交站坐标bs_loc，调用maps_walking_by_coordinates(origin='109.498166,30.292300', destination=bs_loc)，验证total_duration_seconds≤360。
6) 自习室到恩施站驾车≤12分钟：调用 maps_text_search(keywords='恩施站', city='恩施') 取 poi_id，再 maps_search_detail(id=poi_id) 获取 恩施站坐标 es_loc；再调用 maps_driving_by_coordinates(origin=自习室坐标, destination=es_loc)，验证 total_duration_seconds≤720。
7) 途经点300米内有药店：为可验证，取步骤6驾车路线steps中的每一个途径点包括终点坐标to_coordinates='109.492867,30.308993'；调用maps_around_search(location='109.492867,30.308993', radius='300', keywords='药店')，验证存在一个途径点附近返回的pois数量≥1（例如包含POI：B0LKHAQ7D4 元昌医药(时代家居广场分店)）。"""

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
    maps_distance,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "109.485312,30.297849",
    search_radius: int = 3000,
    keywords: str = "自习室",
    bus_stop_search_radius: int = 1200,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_straight_distance: int = 250,  # 250 meters
    max_bus_stop_walking_duration: int = 360,  # 6 minutes = 360 seconds
    station_address: str = "恩施站",
    station_city: str = "恩施",
    max_driving_duration: int = 720,  # 12 minutes = 720 seconds
    waypoint_pharmacy_radius: int = 300,
    pharmacy_keywords: str = "药店"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近约束（3000米内）：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 自习室详情：调用 maps_search_detail 获取自习室坐标。
    3) 公交站集合（1200米范围内）：调用 maps_around_search 得到公交站POI列表。
    4) 最近公交站直线距离≤250米：调用 maps_distance，取最小distance_meters，验证≤250。
    5) 走路到最近公交站≤6分钟：调用 maps_walking_by_coordinates，验证total_duration_seconds≤360。
    6) 自习室到恩施站驾车≤12分钟：调用获取恩施站坐标，再调用 maps_driving_by_coordinates，验证total_duration_seconds≤720。
    7) 途经点300米内有药店：取驾车路线steps中的每一个途径点坐标，调用 maps_around_search，验证存在一个途径点附近返回的pois数量≥1。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"109.485312,30.297849"
        search_radius: 搜索半径（米），默认3000
        keywords: 搜索关键词，默认"自习室"
        bus_stop_search_radius: 公交站搜索半径（米），默认1200
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_straight_distance: 到公交站最大直线距离（米），默认250
        max_bus_stop_walking_duration: 到公交站最大步行时长（秒），默认360（6分钟）
        station_address: 车站地址，默认"恩施站"
        station_city: 车站所在城市，默认"恩施"
        max_driving_duration: 最大驾车时长（秒），默认720（12分钟）
        waypoint_pharmacy_radius: 途经点药店搜索半径（米），默认300
        pharmacy_keywords: 药店搜索关键词，默认"药店"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近约束（3000米内）
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

    # 步骤2: 获取自习室详情（取坐标用于后续计算）
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 公交站集合（1200米范围内）
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

    # 步骤4: 最近公交站直线距离≤250米
    # 将所有公交站坐标拼成origins
    bus_stop_locations = []
    for bus_stop in bus_stop_search_result.pois:
        if bus_stop.location:
            bus_stop_locations.append(bus_stop.location)

    if len(bus_stop_locations) == 0:
        print(f"❌ 没有公交站有坐标信息")
        return False

    origins_str = "|".join(bus_stop_locations)
    distance_result = maps_distance(origins=origins_str, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未获取到距离信息")
        return False

    # 找到最小距离及对应的公交站
    min_distance = None
    min_distance_bus_stop_index = None
    for result in distance_result.results:
        if min_distance is None or result.distance_meters < min_distance:
            min_distance = result.distance_meters
            # origin_id 从1开始，对应 bus_stop_locations 的索引从0开始
            min_distance_bus_stop_index = result.origin_id - 1

    if min_distance is None:
        print(f"❌ 无法计算最小距离")
        return False

    if min_distance > max_bus_stop_straight_distance:
        print(f"❌ 最近公交站直线距离{min_distance}米，超过{max_bus_stop_straight_distance}米")
        return False
    print(f"✅ 最近公交站直线距离{min_distance}米，符合要求（<= {max_bus_stop_straight_distance}米）")

    # 步骤5: 走路到最近公交站≤6分钟
    nearest_bus_stop_location = bus_stop_locations[min_distance_bus_stop_index]
    walking_result = maps_walking_by_coordinates(
        origin=poi_location,
        destination=nearest_bus_stop_location
    )
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_bus_stop_walking_duration:
        print(f"❌ 到最近公交站步行时长{walking_duration}秒，超过{max_bus_stop_walking_duration}秒（{max_bus_stop_walking_duration // 60}分钟）")
        return False
    print(f"✅ 到最近公交站步行时长{walking_duration}秒，符合要求（<= {max_bus_stop_walking_duration}秒，即{max_bus_stop_walking_duration // 60}分钟）")

    # 步骤6: 自习室到恩施站驾车≤12分钟（用 maps_text_search + maps_search_detail 替代 maps_geo）
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"❌ 获取{station_address}坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到{station_address}坐标")
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
    print(f"✅ 获取{station_address}坐标: {station_location}")

    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到{station_address}驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_address}驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    # 步骤7: 途经点300米内有药店
    if not driving_result.steps or len(driving_result.steps) == 0:
        print(f"❌ 驾车路线没有步骤信息")
        return False

    print(f"✅ 驾车路线共有{len(driving_result.steps)}个步骤")

    # 检查每个途经点（包括终点）周围是否有药店
    pharmacy_found = False
    for i, step in enumerate(driving_result.steps):
        waypoint_location = step.to_coordinates
        pharmacy_search_result = maps_around_search(
            location=waypoint_location,
            radius=str(waypoint_pharmacy_radius),
            keywords=pharmacy_keywords
        )

        if pharmacy_search_result.error:
            continue

        if pharmacy_search_result.pois and len(pharmacy_search_result.pois) > 0:
            pharmacy_found = True
            print(f"✅ 在途经点{i+1}（坐标: {waypoint_location}）周围{waypoint_pharmacy_radius}米内找到{len(pharmacy_search_result.pois)}个药店")
            print(f"   示例药店: {pharmacy_search_result.pois[0].name} (ID: {pharmacy_search_result.pois[0].id})")
            break

    if not pharmacy_found:
        print(f"❌ 所有途经点周围{waypoint_pharmacy_radius}米内都没有找到药店")
        return False

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 790.py 文件...\\n")
    result = verify_poi(poi_id="B0LR0AM566")
    print(f"\n验证结果: {result}")
