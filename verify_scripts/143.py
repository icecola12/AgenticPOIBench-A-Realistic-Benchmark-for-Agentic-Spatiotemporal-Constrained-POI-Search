
"""
修改任务指令：你想在附近3000米以内找一家电影院。从你这里开车过去的距离不能超过2500米，而且骑行过去的距离不能超过2000米。看完电影你要去凯里站接人，所以从电影院开车到凯里站的时间不能超过9分钟。另外，你希望这家电影院附近1500米范围内能找到公交站，并且从电影院步行到这些公交站里最近的那个，步行时间不能超过10分钟。最后，你还需要从你出发去电影院的路上，存在一个沿途点附近300米范围内能找到ATM。你依赖心强，希望智能体能为自己处理和决定一切。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近3000米以内（周边搜点验证）：调用 maps_around_search(location='107.979899,26.566433', radius='3000', keywords='电影院')，验证返回pois列表中包含 target_poi_id=B0LU45WURL。
2) 驾车距离≤2500米：先调用 maps_search_detail('B0LU45WURL') 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 目标POI坐标destination；再调用 maps_driving_by_coordinates(origin='107.979899,26.566433', destination=destination)，验证 total_distance_meters ≤ 2500。
3) 骑行距离≤2000米：调用 maps_bicycling_by_coordinates(origin='107.979899,26.566433', destination=destination)，验证 total_distance_meters ≤ 2000。
4) 目标到凯里站驾车时间≤9分钟：调用 maps_text_search(keywords='凯里站', city='黔东南苗族侗族自治州') 取 poi_id，再 maps_search_detail(id=poi_id) 获取 凯里站坐标 station；再调用 maps_driving_by_coordinates(origin=destination, destination=station)，验证 total_duration_seconds ≤ 540。
5) 目标附近1500米内存在公交站：调用 maps_around_search(location=destination, radius='1500', keywords='公交站')，验证 pois 数量≥1。
6) 目标到上述公交站中最近一个的步行时间≤10分钟：对步骤5返回的每个公交站poi_i，调用 maps_walking_by_coordinates(origin=destination, destination=poi_i.location)，取最小步行时间t_min，验证 t_min ≤ 600秒。
7) 途径点附近300米内有ATM：对于步骤2中途径的所有途径点（包括起点和终点）坐标to_coordinates，调用 maps_around_search(location=to_coordinates, radius='300', keywords='ATM')，验证存在一个途径点返回pois的数量≥1。
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
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "107.979899,26.566433",
    search_radius: int = 3000,
    keywords: str = "电影院",
    max_driving_distance: int = 2500,  # 2500 meters
    max_bicycling_distance: int = 2000,  # 2000 meters
    station_address: str = "凯里站",
    station_city: str = "黔东南苗族侗族自治州",
    max_station_driving_duration: int = 540,  # 9 minutes = 540 seconds
    bus_stop_search_radius: int = 1500,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_walking_duration: int = 600,  # 10 minutes = 600 seconds
    waypoint_atm_radius: int = 300,
    atm_keywords: str = "ATM"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近3000米以内：调用 maps_around_search，验证返回pois列表中包含目标poi_id。
    2) 驾车距离≤2500米：调用 maps_search_detail 获取目标POI坐标，再调用 maps_driving_by_coordinates，验证 total_distance_meters ≤ 2500。
    3) 骑行距离≤2000米：调用 maps_bicycling_by_coordinates，验证 total_distance_meters ≤ 2000。
    4) 目标到凯里站驾车时间≤9分钟：调用获取凯里站坐标，再调用 maps_driving_by_coordinates，验证 total_duration_seconds ≤ 540。
    5) 目标附近1500米内存在公交站：调用 maps_around_search，验证 pois 数量≥1。
    6) 目标到上述公交站中最近一个的步行时间≤10分钟：对每个公交站调用 maps_walking_by_coordinates，取最小步行时间，验证 ≤ 600秒。
    7) 途径点附近300米内有ATM：对驾车路线中所有途径点坐标，调用 maps_around_search，验证存在一个途径点返回pois的数量≥1。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"107.979899,26.566433"
        search_radius: 搜索半径（米），默认3000
        keywords: 搜索关键词，默认"电影院"
        max_driving_distance: 最大驾车距离（米），默认2500
        max_bicycling_distance: 最大骑行距离（米），默认2000
        station_address: 车站地址，默认"凯里站"
        station_city: 车站所在城市，默认"黔东南苗族侗族自治州"
        max_station_driving_duration: 到车站最大驾车时长（秒），默认540（9分钟）
        bus_stop_search_radius: 公交站搜索半径（米），默认1500
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_walking_duration: 到公交站最大步行时长（秒），默认600（10分钟）
        waypoint_atm_radius: 途经点ATM搜索半径（米），默认300
        atm_keywords: ATM搜索关键词，默认"ATM"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近3000米以内（周边搜点验证）
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

    # 步骤3: 驾车距离≤2500米
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

    # 步骤4: 骑行距离≤2000米
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

    # 步骤5: 目标到凯里站驾车时间≤9分钟（用 maps_text_search + maps_search_detail 替代 maps_geo）
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

    # 步骤6: 目标附近1500米内存在公交站
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

    # 步骤7: 目标到上述公交站中最近一个的步行时间≤10分钟
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

    # 步骤8: 途径点附近300米内有ATM
    if not driving_result.steps or len(driving_result.steps) == 0:
        print(f"❌ 驾车路线没有步骤信息")
        return False

    print(f"✅ 驾车路线共有{len(driving_result.steps)}个步骤")

    # 检查每个��经点（包括终点）周围是否有ATM
    atm_found = False
    for i, step in enumerate(driving_result.steps):
        waypoint_location = step.to_coordinates
        atm_search_result = maps_around_search(
            location=waypoint_location,
            radius=str(waypoint_atm_radius),
            keywords=atm_keywords
        )

        if atm_search_result.error:
            continue

        if atm_search_result.pois and len(atm_search_result.pois) > 0:
            atm_found = True
            print(f"✅ 在途经点{i+1}（坐标: {waypoint_location}）周围{waypoint_atm_radius}米内找到{len(atm_search_result.pois)}个ATM")
            print(f"   示例ATM: {atm_search_result.pois[0].name} (ID: {atm_search_result.pois[0].id})")
            break

    if not atm_found:
        print(f"❌ 所有途经点周围{waypoint_atm_radius}米内都没有找到ATM")
        return False

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 791.py 文件...\\n")
    result = verify_poi(poi_id="B0LU45WURL")
    print(f"\n验证结果: {result}")
