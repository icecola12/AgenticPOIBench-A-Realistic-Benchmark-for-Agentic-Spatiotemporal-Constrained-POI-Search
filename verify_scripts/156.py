
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近10公里以内（周边搜索直接验证）：调用 maps_around_search(location='101.596714,25.024495', radius='10000', keywords='电影院')，检查返回pois列表中包含 target_poi_id='B0FFH8I6QU'。
2) 电影院类型与坐标：调用 maps_search_detail(id='B0FFH8I6QU') 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 目标POI坐标 destination='101.545687,25.028171'（以entr_location优先，其次location）。
3) 电影院到"附近1500米内的公交站"步行时间≤18分钟：
a. 调用 maps_around_search(location=destination, radius='1500', keywords='公交站') 获取公交站列表（应≥1）。
b. 对每个公交站poi.location，调用 maps_walking_by_coordinates(origin=destination, destination=bus_stop_location) 得到步行时长，取最小值 t_bus_min。
c. 验证 t_bus_min ≤ 18*60 秒。
4) 电影院到楚雄客运北站驾车时间≤12分钟：
a. 调用 maps_text_search(keywords='楚雄客运北站', city='楚雄彝族自治州') 取 poi_id，再 maps_search_detail(id=poi_id) 得到 north_station='101.545916,25.045892'。
b. 调用 maps_driving_by_coordinates(origin=destination, destination=north_station) 得到 t_drive。
c. 验证 t_drive ≤ 12*60 秒。
5) 当前位置到电影院步行距离≤6公里：调用 maps_walking_by_coordinates(origin='101.596714,25.024495', destination=destination) 获取 total_distance_meters，验证 ≤ 6000。
6) 途径点附近300米内有ATM：
a. 复用第5步返回的 steps 列表，取每个 step 的 from_coordinates 与 to_coordinates 去重，形成途径点集合 P。
b. 对集合P中的每个点 p，调用 maps_around_search(location=p, radius='300', keywords='ATM')。
c. 若任意一次返回pois数量>0，则满足；否则不满足。
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
    user_location: str = "101.596714,25.024495",
    search_radius: int = 10000,
    keywords: str = "电影院",
    bus_stop_search_radius: int = 1500,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_walking_duration: int = 1080,  # 18 minutes = 1080 seconds
    station_name: str = "楚雄客运北站",
    city: str = "楚雄彝族自治州",
    max_station_driving_duration: int = 720,  # 12 minutes = 720 seconds
    max_walking_distance: int = 6000,  # 6 km = 6000 meters
    atm_search_radius: int = 300,
    atm_keywords: str = "ATM"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近10公里以内：调用 maps_around_search，检查返回pois列表中包含目标POI。
    2) 电影院类型与坐标：调用 maps_search_detail 获取目标POI坐标（以entr_location优先，其次location）。
    3) 电影院到"附近1500米内的公交站"步行时间≤18分钟：调用 maps_around_search 获取公交站列表，对每个公交站调用 maps_walking_by_coordinates，取最小值，验证 ≤ 18*60 秒。
    4) 电影院到楚雄客运北站驾车时间≤12分钟：调用得到客运站坐标，调用 maps_driving_by_coordinates，验证 ≤ 12*60 秒。
    5) 当前位置到电影院步行距离≤6公里：调用 maps_walking_by_coordinates，验证 ≤ 6000。
    6) 途径点附近300米内有ATM：复用第5步返回的 steps 列表，取每个 step 的 from_coordinates 与 to_coordinates 去重，对每个点调用 maps_around_search，若任意一次返回pois数量>0，则满足。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"101.596714,25.024495"
        search_radius: 搜索半径（米），默认10000
        keywords: 搜索关键词，默认"电影院"
        bus_stop_search_radius: 公交站搜索半径（米），默认1500
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_walking_duration: 到公交站最大步行时长（秒），默认1080（18分钟）
        station_name: 客运站名称，默认"楚雄客运北站"
        city: 城市名称，默认"楚雄彝族自治州"
        max_station_driving_duration: 到客运站最大驾车时长（秒），默认720（12分钟）
        max_walking_distance: 最大步行距离（米），默认6000
        atm_search_radius: ATM搜索半径（米），默认300
        atm_keywords: ATM搜索关键词，默认"ATM"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近10公里以内
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

    # 步骤2: 获取目标POI坐标（以entr_location优先，其次location）
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    # 优先使用entr_location，如果没有则使用location
    poi_location = None
    if poi_detail.entr_location:
        poi_location = poi_detail.entr_location
        print(f"✅ 获取POI入口坐标(entr_location): {poi_location}")
    elif poi_detail.location:
        poi_location = poi_detail.location
        print(f"✅ 获取POI坐标(location): {poi_location}")
    else:
        print(f"❌ POI没有location或entr_location信息")
        return False

    # 步骤3: 电影院到"附近1500米内的公交站"步行时间≤18分钟
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

    # 步骤4: 电影院到楚雄客运北站驾车时间≤12分钟
    station_text_result = maps_text_search(keywords=station_name, city=city)
    if station_text_result.error:
        print(f"❌ 获取{station_name}坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到{station_name}坐标")
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
    print(f"✅ 获取{station_name}坐标: {station_location}")

    station_driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if station_driving_result.error:
        print(f"❌ 计算到{station_name}驾车路线失败: {station_driving_result.error}")
        return False

    if station_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{station_name}驾车时长")
        return False

    station_driving_duration = station_driving_result.total_duration_seconds
    if station_driving_duration > max_station_driving_duration:
        print(f"❌ 到{station_name}驾车时长{station_driving_duration}秒，超过{max_station_driving_duration}秒（{max_station_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_name}驾车时长{station_driving_duration}秒，符合要求（<= {max_station_driving_duration}秒，即{max_station_driving_duration // 60}分钟）")

    # 步骤5: 当前位置到电影院步行距离≤6公里
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_distance_meters is None:
        print(f"❌ 无法获取步行距离")
        return False

    walking_distance = walking_result.total_distance_meters
    if walking_distance > max_walking_distance:
        print(f"❌ 步行距离{walking_distance}米，超过{max_walking_distance}米")
        return False
    print(f"✅ 步行距离{walking_distance}米，符合要求（<= {max_walking_distance}米）")

    # 步骤6: 途径点附近300米内有ATM
    if not walking_result.steps or len(walking_result.steps) == 0:
        print(f"❌ 步行路线没有步骤信息")
        return False

    print(f"✅ 步行路线共有{len(walking_result.steps)}个步骤")

    # 收集所有途径点坐标（from_coordinates 和 to_coordinates）并去重
    waypoint_set = set()
    for step in walking_result.steps:
        if step.from_coordinates:
            waypoint_set.add(step.from_coordinates)
        if step.to_coordinates:
            waypoint_set.add(step.to_coordinates)

    waypoints = list(waypoint_set)
    print(f"✅ 共有{len(waypoints)}个去重后的途径点")

    # 检查每个途径点周围是否有ATM
    atm_found = False
    for i, waypoint in enumerate(waypoints):
        atm_search_result = maps_around_search(
            location=waypoint,
            radius=str(atm_search_radius),
            keywords=atm_keywords
        )

        if atm_search_result.error:
            continue

        if atm_search_result.pois and len(atm_search_result.pois) > 0:
            atm_found = True
            print(f"✅ 在途径点{i+1}（坐标: {waypoint}）周围{atm_search_radius}米内找到{len(atm_search_result.pois)}个ATM")
            print(f"   示例ATM: {atm_search_result.pois[0].name} (ID: {atm_search_result.pois[0].id})")
            break

    if not atm_found:
        print(f"❌ 所有途径点周围{atm_search_radius}米内都没有找到ATM")
        return False

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 812.py 文件...\n")
    result = verify_poi(poi_id="B0FFH8I6QU")
    print(f"\n验证结果: {result}")


