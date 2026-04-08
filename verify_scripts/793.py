
"""
修改任务指令：你想在附近2500米以内找一家网吧。你打算一会儿打车过去，所以从你这里到网吧的驾车距离不能超过3公里，而且骑行过去的距离也要控制在2500米以内。你还希望网吧离公交出行方便：网吧到附近1200米范围内公交站的最短直线距离不要超过120米，并且网吧走到这些公交站里最近的一个，步行距离不要超过1500米、步行时间不要超过18分钟。最后，你从你这边走路过去到网吧的时间，要比你一个朋友从同一个出发点开车过去的时间至少多12分钟（他会比你晚出发）。你情绪化，时而冷静时而愤怒，态度变化快。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近约束：调用maps_around_search(location='116.568129,35.40811', radius='2500', keywords='网吧')，验证返回结果包含poi_id='B0JU59DEVD'。
2) 驾车距离≤3公里：调用maps_driving_by_coordinates(origin='116.568129,35.40811', destination=目标POI坐标)，验证total_distance_meters ≤ 3000。
3) 骑行距离≤2500米：调用maps_bicycling_by_coordinates(origin='116.568129,35.40811', destination=目标POI坐标)，验证total_distance_meters ≤ 2500。
4) 公交站直线距离约束：
4.1 调用maps_search_detail('B0JU59DEVD')获取目标POI坐标。
4.2 调用maps_around_search(location=目标POI坐标, radius='1200', keywords='公交站')获取候选公交站集合。
4.3 对这些公交站坐标调用maps_distance(origins=公交站坐标串, destination=目标POI坐标)，取最小distance_meters，验证≤120。
5) 最近公交站步行距离≤1000米且步行时间≤18分钟：对步骤4得到的公交站集合逐个调用maps_walking_by_coordinates(origin=目标POI坐标, destination=公交站坐标)，取total_distance_meters最小的一条路线，验证最小步行距离≤1000且对应total_duration_seconds≤1080。
6) 你步行到网吧时间比朋友开车时间至少多12分钟：
6.1 调用maps_walking_by_coordinates(origin='116.568129,35.40811', destination=目标POI坐标)得t_walk。
6.2 调用maps_driving_by_coordinates(origin='116.568129,35.40811', destination=目标POI坐标)得t_drive。
6.3 验证 t_walk - t_drive ≥ 720秒。
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
    maps_distance,
    maps_driving_by_coordinates,
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "116.568129,35.40811",
    search_radius: int = 2500,
    keywords: str = "网吧",
    max_driving_distance: int = 3000,  # 3 km = 3000 meters
    max_bicycling_distance: int = 2500,  # 2500 meters
    bus_stop_search_radius: int = 1200,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_straight_distance: int = 120,  # 120 meters
    max_bus_stop_walking_distance: int = 1000,  # 1000 meters
    max_bus_stop_walking_duration: int = 1080,  # 18 minutes = 1080 seconds
    min_time_difference: int = 720  # 12 minutes = 720 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近约束：调用 maps_around_search，验证返回结果包含poi_id。
    2) 驾车距离≤3公里：调用 maps_driving_by_coordinates，验证 total_distance_meters ≤ 3000。
    3) 骑行距离≤2500米：调用 maps_bicycling_by_coordinates，验证 total_distance_meters ≤ 2500。
    4) 公交站直线距离约束：获取POI坐标，搜索公交站，使用 maps_distance 计算最小直线距离，验证≤120。
    5) 最近公交站步行距离≤1000米且步行时间≤18分钟：对公交站集合调用 maps_walking_by_coordinates，取最小步行距离，验证≤1000且对应时间≤1080。
    6) 步行到网吧时间比开车时间至少多12分钟：验证 t_walk - t_drive ≥ 720秒。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.568129,35.40811"
        search_radius: 搜索半径（米），默认2500
        keywords: 搜索关键词，默认"网吧"
        max_driving_distance: 最大驾车距离（米），默认3000
        max_bicycling_distance: 最大骑行距离（米），默认2500
        bus_stop_search_radius: 公交站搜索半径（米），默认1200
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_straight_distance: 到公交站最大直线距离（米），默认120
        max_bus_stop_walking_distance: 到公交站最大步行距离（米），默认1000
        max_bus_stop_walking_duration: 到公交站最大步行时长（秒），默认1080（18分钟）
        min_time_difference: 步行与驾车时间最小差值（秒），默认720（12分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近约束
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

    # 步骤3: 驾车距离≤3公里
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

    # 步骤4: 骑行距离≤2500米
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

    # 步骤5: 公交站直线距离约束
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

    # 找到最小直线距离及对应的公交站
    min_straight_distance = None
    min_straight_distance_bus_stop_index = None
    for result in distance_result.results:
        if min_straight_distance is None or result.distance_meters < min_straight_distance:
            min_straight_distance = result.distance_meters
            # origin_id 从1开始，对应 bus_stop_locations 的索引从0开始
            min_straight_distance_bus_stop_index = result.origin_id - 1

    if min_straight_distance is None:
        print(f"❌ 无法计算最小直线距离")
        return False

    if min_straight_distance > max_bus_stop_straight_distance:
        print(f"❌ 最近公交站直线距离{min_straight_distance}米，超过{max_bus_stop_straight_distance}米")
        return False
    print(f"✅ 最近公交站直线距离{min_straight_distance}米，符合要求（<= {max_bus_stop_straight_distance}米）")

    # 步骤6: 最近公交站步行距离≤1000米且步行时间≤18分钟
    min_walking_distance = None
    min_walking_duration = None
    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        walking_result = maps_walking_by_coordinates(
            origin=poi_location,
            destination=bus_stop.location
        )
        if walking_result.error or walking_result.total_distance_meters is None:
            continue

        distance = walking_result.total_distance_meters
        duration = walking_result.total_duration_seconds

        if min_walking_distance is None or distance < min_walking_distance:
            min_walking_distance = distance
            min_walking_duration = duration

    if min_walking_distance is None:
        print(f"❌ 无法计算到公交站的步行距离")
        return False

    if min_walking_distance > max_bus_stop_walking_distance:
        print(f"❌ 到最近公交站步行距离{min_walking_distance}米，超过{max_bus_stop_walking_distance}米")
        return False

    if min_walking_duration is None or min_walking_duration > max_bus_stop_walking_duration:
        print(f"❌ 到最近公交站步行时长{min_walking_duration}秒，超过{max_bus_stop_walking_duration}秒（{max_bus_stop_walking_duration // 60}分钟）")
        return False

    print(f"✅ 到最近公交站步行距离{min_walking_distance}米，步行时长{min_walking_duration}秒，符合要求（距离<= {max_bus_stop_walking_distance}米，时长<= {max_bus_stop_walking_duration}秒，即{max_bus_stop_walking_duration // 60}分钟）")

    # 步骤7: 步行到网吧时间比开车时间至少多12分钟
    user_walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if user_walking_result.error:
        print(f"❌ 计算用户步行路线失败: {user_walking_result.error}")
        return False

    if user_walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取用户步行时长")
        return False

    user_walking_duration = user_walking_result.total_duration_seconds

    # 驾车时长已经在步骤3中获取
    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds

    time_difference = user_walking_duration - driving_duration
    if time_difference < min_time_difference:
        print(f"❌ 步行时长{user_walking_duration}秒与驾车时长{driving_duration}秒的差值为{time_difference}秒，小于{min_time_difference}秒（{min_time_difference // 60}分钟）")
        return False
    print(f"✅ 步行时长{user_walking_duration}秒与驾车时长{driving_duration}秒的差值为{time_difference}秒，符合要求（>= {min_time_difference}秒，即{min_time_difference // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 793.py 文件...\\n")
    result = verify_poi(poi_id="B0JU59DEVD")
    print(f"\n验证结果: {result}")
