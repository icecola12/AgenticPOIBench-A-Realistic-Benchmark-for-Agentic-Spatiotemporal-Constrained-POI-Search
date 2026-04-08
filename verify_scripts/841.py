"""
输入：B0KRUUZB1O
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边约束（附近1500米内网吧）：调用 maps_around_search(location='126.989287,46.637856', radius='1500', keywords='网吧')，验证返回pois里包含 target_poi_id=B0KRUUZB1O。
2) 网吧类型核对：同一步 maps_around_search 的 keywords 为“网吧”，且目标POI名称含“网咖/网吧”可作为类型一致性佐证；再调用 maps_search_detail('B0KRUUZB1O')获取名称与坐标用于后续计算。
3) 步行路线距离≤1000米：调用 maps_walking_by_coordinates(origin='126.989287,46.637856', destination='126.989167,46.640287')，验证 total_distance_meters=902 ≤ 1000。
4) 公交站直线距离≤150米（且公交站需在网吧800米范围内）：
a. 调用 maps_around_search(location='126.989167,46.640287', radius='800', keywords='公交站') 获取候选公交站列表。
b. 选取其中一个公交站点（例如“市建行(公交站)”坐标 126.988142,46.640903），调用 maps_distance(origins='126.989167,46.640287', destination='126.988142,46.640903')，验证 distance_meters=104 ≤ 150。
5) 西城客运站->网吧 驾车≤5分钟：调用 maps_geo(address='绥化西城客运站', city='绥化') 得到坐标 126.976021,46.633202；调用 maps_driving_by_coordinates(origin='126.976021,46.633202', destination='126.989167,46.640287')，验证 total_duration_seconds=213 ≤ 300。
6) 网吧->绥化站 驾车≤5分钟：调用 maps_geo(address='绥化站', city='绥化') 得到坐标 127.015969,46.645209；调用 maps_driving_by_coordinates(origin='126.989167,46.640287', destination='127.015969,46.645209')，验证 total_duration_seconds=195 ≤ 300。
7) 客运站->网吧->绥化站 总驾车时间≤9分钟：将步骤5与步骤6的时长相加 (213+195=408秒)，验证 408 ≤ 540。
8) 途径点附近400米有洗衣店：
a. 遍历步骤5（客运站->网吧）驾车路线中的途径点坐标
b. 调用 maps_around_search(location='126.982654,46.636745', radius='400', keywords='洗衣店')（以路线附近点位为中心），验证是否存在某一途径点对应返回的pois数量>0（例如包含“乾嘉衣坊干洗连锁总汇”等）。
"""
import sys
import os
from typing import List, Dict

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_distance,
    maps_driving_by_coordinates,
    maps_geo,
    maps_walking_by_coordinates,
    maps_text_search,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search

"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(
    target_poi_id: str = "B0KRUUZB1O",
    user_location: str = "126.989287,46.637856",
    radius: str = "1500",
    keywords: str = "网吧",
    max_walking_distance: int = 1000,
    bus_search_radius: str = "800",
    bus_keywords: str = "公交站",
    max_distance_to_bus: int = 150,
    bus_station_address: str = "绥化西城客运站",
    bus_station_city: str = "绥化",
    max_driving_time_from_bus_station: int = 300,  # 5分钟
    station_address: str = "绥化站",
    station_city: str = "绥化",
    max_driving_time_to_station: int = 300,  # 5分钟
    max_total_driving_time: int = 540,  # 9分钟
    laundry_search_radius: str = "400",
    laundry_keywords: str = "洗衣店"
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        max_walking_distance: 最大步行距离（米）
        bus_search_radius: 公交站搜索半径（米）
        bus_keywords: 公交站搜索关键词
        max_distance_to_bus: 到公交站的最大直线距离（米）
        bus_station_address: 客运站地址
        bus_station_city: 客运站所在城市
        max_driving_time_from_bus_station: 从客运站到网吧的最大驾车时间（秒）
        station_address: 火车站地址
        station_city: 火车站所在城市
        max_driving_time_to_station: 从网吧到火车站的最大驾车时间（秒）
        max_total_driving_time: 客运站->网吧->火车站 总最大驾车时间（秒）
        laundry_search_radius: 洗衣店搜索半径（米）
        laundry_keywords: 洗衣店搜索关键词

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 周边约束（附近1500米内网吧）
    print(f"步骤1: 验证附近{radius}米内的周边搜索约束 - 查询POI ID: {target_poi_id}")
    around_result = maps_around_search(
        location=user_location,
        radius=radius,
        keywords=keywords
    )

    if around_result.error:
        print(f"步骤1失败: {around_result.error}")
        return False

    if not around_result.pois:
        print("步骤1失败: 未找到任何POI")
        return False

    # 检查是否包含目标POI
    poi_ids = [poi.id for poi in around_result.pois]
    if target_poi_id not in poi_ids:
        print(f"步骤1失败: POI列表不包含目标POI ID '{target_poi_id}'")
        all_passed = False
    else:
        print(f"步骤1通过: POI列表中包含目标POI ID '{target_poi_id}'")

    # 步骤2: 网吧类型核对
    print(f"\n步骤2: 验证网吧类型核对 - 查询POI ID: {target_poi_id}")
    poi_detail = maps_search_detail(id=target_poi_id)

    if poi_detail.error:
        print(f"步骤2失败: {poi_detail.error}")
        return False

    if not poi_detail.name:
        print("步骤2失败: 未获取到POI名称")
        return False

    # 获取POI坐标（后续步骤需要）
    if not poi_detail.location:
        print("步骤2失败: 未获取到POI坐标")
        return False

    poi_location = poi_detail.location
    poi_name = poi_detail.name
    print(f"POI坐标: {poi_location}, 名称: {poi_name}")

    # 检查名称是否包含"网吧"或"网咖"
    if "网吧" not in poi_name and "网咖" not in poi_name:
        print(f"步骤2失败: POI名称'{poi_name}'不包含'网吧'或'网咖'")
        all_passed = False
    else:
        print(f"步骤2通过: POI名称'{poi_name}'包含'网吧'或'网咖'")

    # 步骤3: 步行路线距离≤1000米
    print(f"\n步骤3: 验证步行距离不超过{max_walking_distance}米")
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if walking_result.error:
        print(f"步骤3失败: {walking_result.error}")
        all_passed = False
    else:
        if walking_result.total_distance_meters is None:
            print("步骤3失败: 未获取到步行距离")
            all_passed = False
        else:
            walking_distance = walking_result.total_distance_meters
            if walking_distance > max_walking_distance:
                print(f"步骤3失败: 步行距离{walking_distance}米超过要求{max_walking_distance}米")
                all_passed = False
            else:
                print(f"步骤3通过: 步行距离{walking_distance}米，满足要求（<={max_walking_distance}米）")

    # 步骤4: 公交站直线距离≤150米
    print(f"\n步骤4: 验证到公交站的直线距离不超过{max_distance_to_bus}米")
    bus_around_result = maps_around_search(
        location=poi_location,
        radius=bus_search_radius,
        keywords=bus_keywords
    )

    if bus_around_result.error:
        print(f"步骤4失败: {bus_around_result.error}")
        all_passed = False
    else:
        if not bus_around_result.pois or len(bus_around_result.pois) == 0:
            print(f"步骤4失败: 未找到任何{bus_keywords}")
            all_passed = False
        else:
            # 找到最近的公交站
            min_distance = float('inf')
            for bus_poi in bus_around_result.pois:
                bus_detail = maps_search_detail(id=bus_poi.id)
                if bus_detail.error or not bus_detail.location:
                    continue

                bus_location = bus_detail.location
                distance_result = maps_distance(
                    origins=poi_location,
                    destination=bus_location
                )

                if distance_result.error or not distance_result.results or len(distance_result.results) == 0:
                    continue

                distance = distance_result.results[0].distance_meters
                if distance < min_distance:
                    min_distance = distance

            if min_distance == float('inf'):
                print("步骤4失败: 无法计算到任何公交站的距离")
                all_passed = False
            elif min_distance > max_distance_to_bus:
                print(f"步骤4失败: 到最近公交站的距离{min_distance}米超过要求{max_distance_to_bus}米")
                all_passed = False
            else:
                print(f"步骤4通过: 到最近公交站的距离{min_distance}米，满足要求（<={max_distance_to_bus}米）")

    # 步骤5: 西城客运站->网吧 驾车≤5分钟
    print(f"\n步骤5: 验证从{bus_station_address}到网吧的驾车时间不超过{max_driving_time_from_bus_station}秒（{max_driving_time_from_bus_station//60}分钟）")
    geo_result_bus_station = maps_geo(address=bus_station_address, city=bus_station_city)

    if geo_result_bus_station.error:
        print(f"步骤5失败: 获取{bus_station_address}坐标失败 - {geo_result_bus_station.error}")
        all_passed = False
    else:
        if not geo_result_bus_station.results or len(geo_result_bus_station.results) == 0:
            print(f"步骤5失败: 未找到{bus_station_address}坐标")
            all_passed = False
        else:
            bus_station_location = geo_result_bus_station.results[0].location
            driving_result_from_bus_station = maps_driving_by_coordinates(
                origin=bus_station_location,
                destination=poi_location
            )

            if driving_result_from_bus_station.error:
                print(f"步骤5失败: 计算驾车时间失败 - {driving_result_from_bus_station.error}")
                all_passed = False
            else:
                if driving_result_from_bus_station.total_duration_seconds is None:
                    print("步骤5失败: 未获取到驾车时间")
                    all_passed = False
                else:
                    driving_time_from_bus_station = driving_result_from_bus_station.total_duration_seconds
                    if driving_time_from_bus_station > max_driving_time_from_bus_station:
                        print(f"步骤5失败: 驾车时间{driving_time_from_bus_station}秒超过要求{max_driving_time_from_bus_station}秒")
                        all_passed = False
                    else:
                        print(f"步骤5通过: 驾车时间{driving_time_from_bus_station}秒，满足要求（<={max_driving_time_from_bus_station}秒）")

    # 步骤6: 网吧->绥化站 驾车≤5分钟
    print(f"\n步骤6: 验证从网吧到{station_address}的驾车时间不超过{max_driving_time_to_station}秒（{max_driving_time_to_station//60}分钟）")
    geo_result_station = maps_geo(address=station_address, city=station_city)

    if geo_result_station.error:
        print(f"步骤6失败: 获取{station_address}坐标失败 - {geo_result_station.error}")
        all_passed = False
    else:
        if not geo_result_station.results or len(geo_result_station.results) == 0:
            print(f"步骤6失败: 未找到{station_address}坐标")
            all_passed = False
        else:
            station_location = geo_result_station.results[0].location
            driving_result_to_station = maps_driving_by_coordinates(
                origin=poi_location,
                destination=station_location
            )

            if driving_result_to_station.error:
                print(f"步骤6失败: 计算驾车时间失败 - {driving_result_to_station.error}")
                all_passed = False
            else:
                if driving_result_to_station.total_duration_seconds is None:
                    print("步骤6失败: 未获取到驾车时间")
                    all_passed = False
                else:
                    driving_time_to_station = driving_result_to_station.total_duration_seconds
                    if driving_time_to_station > max_driving_time_to_station:
                        print(f"步骤6失败: 驾车时间{driving_time_to_station}秒超过要求{max_driving_time_to_station}秒")
                        all_passed = False
                    else:
                        print(f"步骤6通过: 驾车时间{driving_time_to_station}秒，满足要求（<={max_driving_time_to_station}秒）")

    # 步骤7: 客运站->网吧->绥化站 总驾车时间≤9分钟
    print(f"\n步骤7: 验证{bus_station_address}->{station_address}途经网吧总驾车时间不超过{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")
    if 'driving_time_from_bus_station' not in locals() or 'driving_time_to_station' not in locals():
        print("步骤7失败: 未获取到各段驾车时间")
        all_passed = False
    else:
        total_driving_time = driving_time_from_bus_station + driving_time_to_station
        if total_driving_time > max_total_driving_time:
            print(f"步骤7失败: 总驾车时间{total_driving_time}秒超过要求{max_total_driving_time}秒")
            all_passed = False
        else:
            print(f"步骤7通过: 总驾车时间{total_driving_time}秒，满足要求（<={max_total_driving_time}秒）")

    # 步骤8: 途径点附近400米有洗衣店
    print(f"\n步骤8: 验证途径点附近{laundry_search_radius}米有{laundry_keywords}")
    if 'driving_result_from_bus_station' not in locals() or not hasattr(driving_result_from_bus_station, 'steps') or not driving_result_from_bus_station.steps:
        print("步骤8失败: 未获取到驾车路线步骤信息")
        all_passed = False
    else:
        found_laundry = False
        for i, step in enumerate(driving_result_from_bus_station.steps):
            waypoint_location = step.to_coordinates
            laundry_result = maps_around_search(
                location=waypoint_location,
                radius=laundry_search_radius,
                keywords=laundry_keywords
            )

            if not laundry_result.error and laundry_result.pois and len(laundry_result.pois) > 0:
                laundry_count = len(laundry_result.pois)
                print(f"步骤8通过: 途径点{i+1}（{waypoint_location}）附近找到{laundry_count}个{laundry_keywords}")
                found_laundry = True
                break

        if not found_laundry:
            print(f"步骤8失败: 所有途径点附近均未找到{laundry_keywords}")
            all_passed = False

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed

def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
