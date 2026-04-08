
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围：调用 maps_around_search(location='110.289321,37.501208', radius='3000', keywords='酒店')，验证返回pois中包含 target_poi_id=B0LUPR24CB。同时获取酒店坐标 destination_loc=110.288712,37.504401
2) 出发地到酒店最大驾车距离：调用 maps_driving_by_coordinates(origin='110.289321,37.501208', destination=destination_loc)，验证 total_distance_meters ≤ 2000。
3) 出发地到酒店最大骑行距离：调用 maps_bicycling_by_coordinates(origin='110.289321,37.501208', destination=destination_loc)，验证 total_distance_meters ≤ 1800。
4) 获取指定公交站点“绥德客运站”坐标：调用 maps_text_search(keywords='绥德客运站 北门街8号', city='榆林市') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 得到 bus_station_loc。
5) 酒店到指定公交站点直线距离：调用 maps_distance(origins=destination_loc, destination=bus_station_loc)，验证 distance ≤ 2800。
6) 酒店到绥德客运站驾车时间：调用 maps_driving_by_coordinates(origin=destination_loc, destination=bus_station_loc)，验证 total_duration_seconds < 240。
7) 酒店附近1200米内有公交站 & 最近公交站步行距离：调用 maps_around_search(location=destination_loc, radius='1200', keywords='公交站')，验证 pois 非空；对返回的每个公交站poi，调用 maps_walking_by_coordinates(origin=destination_loc, destination=poi.location)，取最小 total_distance_meters，验证 min_distance ≤ 1500。
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
    maps_driving_by_coordinates,
    maps_walking_by_coordinates,
    maps_distance,
    maps_bicycling_by_coordinates,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "110.289321,37.501208",
    target_poi_id: str = "B0LUPR24CB",
    around_radius: int = 3000,
    around_keywords: str = "酒店",
    destination_loc: str = "110.288712,37.504401",
    max_driving_distance_to_hotel: int = 2000,   # 步骤2：最大驾车距离（米）
    max_bicycling_distance_to_hotel: int = 1800,  # 步骤3：最大骑行距离（米）
    bus_station_address: str = "绥德客运站 北门街8号",
    bus_station_city: str = "榆林市",
    bus_station_loc: str = "110.262681,37.508296",
    max_straight_distance_to_bus_station: int = 2800,  # 步骤5：直线距离（米）
    max_driving_duration_to_bus_station: int = 240,    # 步骤6：驾车时间（秒）
    nearby_bus_radius: int = 1200,
    nearby_bus_keywords: str = "公交站",
    max_nearest_bus_walking_distance: int = 1500,      # 步骤7：最近公交站步行距离（米）
) -> bool:
    """
    根据给定的验证方法验证POI是否符合要求。

    验证步骤严格对应说明文档：
    1) 周边范围内酒店包含目标POI，记录酒店坐标；
    2) 出发地到酒店驾车距离 ≤ 2000 米；
    3) 出发地到酒店骑行距离 ≤ 1800 米；
    4) 获取指定公交站“绥德客运站”的坐标；
    5) 酒店到该公交站直线距离 ≤ 2800 米；
    6) 酒店到该公交站驾车时间 < 240 秒；
    7) 酒店附近 1200 米内有公交站，且到最近公交站的步行距离 ≤ 1500 米。

    Args:
        poi_id: 目标POI ID（应与 target_poi_id 一致）
        其余参数为步骤中涉及的固定坐标与阈值。

    Returns:
        bool: True 表示全部验证通过，False 表示任一步骤失败。
    """
    # 步骤1) 周边范围：周边搜索酒店，验证包含目标POI，并确认酒店坐标
    around_result = maps_around_search(
        location=user_location,
        radius=str(around_radius),
        keywords=around_keywords,
    )
    if around_result.error:
        print(f"❌ 周边酒店搜索失败: {around_result.error}")
        return False

    if not around_result.pois or len(around_result.pois) == 0:
        print("❌ 在指定范围内未找到任何酒店")
        return False

    poi_found = False
    for p in around_result.pois:
        if p.id == target_poi_id:
            poi_found = True
            print(
                f"✅ 在{around_radius}米范围内找到目标酒店: {p.name} (ID: {p.id})，共返回 {len(around_result.pois)} 个POI"
            )
            break

    if not poi_found:
        print(
            f"❌ 目标POI {target_poi_id} 未出现在 {around_radius} 米范围内的“{around_keywords}”搜索结果中"
        )
        return False

    hotel_location = destination_loc
    print(f"✅ 使用酒店坐标 destination_loc: {hotel_location}")

    # 步骤2) 出发地到酒店最大驾车距离
    driving_to_hotel = maps_driving_by_coordinates(
        origin=user_location,
        destination=hotel_location,
    )
    if driving_to_hotel.error:
        print(f"❌ 计算出发地到酒店的驾车路线失败: {driving_to_hotel.error}")
        return False
    if driving_to_hotel.total_distance_meters is None:
        print("❌ 驾车结果中无总距离信息")
        return False

    driving_distance = driving_to_hotel.total_distance_meters
    if driving_distance > max_driving_distance_to_hotel:
        print(
            f"❌ 出发地到酒店的驾车距离为 {driving_distance} 米，超过 {max_driving_distance_to_hotel} 米"
        )
        return False
    print(
        f"✅ 出发地到酒店的驾车距离为 {driving_distance} 米，满足 ≤ {max_driving_distance_to_hotel} 米"
    )

    # 步骤3) 出发地到酒店最大骑行距离
    bicycling_to_hotel = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=hotel_location,
    )
    if bicycling_to_hotel.error:
        print(f"❌ 计算出发地到酒店的骑行路线失败: {bicycling_to_hotel.error}")
        return False
    if bicycling_to_hotel.total_distance_meters is None:
        print("❌ 骑行结果中无总距离信息")
        return False

    bicycling_distance = bicycling_to_hotel.total_distance_meters
    if bicycling_distance > max_bicycling_distance_to_hotel:
        print(
            f"❌ 出发地到酒店的骑行距离为 {bicycling_distance} 米，超过 {max_bicycling_distance_to_hotel} 米"
        )
        return False
    print(
        f"✅ 出发地到酒店的骑行距离为 {bicycling_distance} 米，满足 ≤ {max_bicycling_distance_to_hotel} 米"
    )

    # 步骤4) 用 maps_text_search + maps_search_detail 获取指定公交站点“绥德客运站”坐标
    text_search_result = maps_text_search(keywords=bus_station_address, city=bus_station_city)
    if text_search_result.error:
        print(f"❌ 获取绥德客运站坐标失败: {text_search_result.error}")
        return False
    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print("❌ 未找到绥德客运站的POI结果")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取绥德客运站坐标失败: {detail_result.error or '无location'}")
        return False

    resolved_bus_station_loc = detail_result.location
    print(f"✅ 使用公交站坐标 bus_station_loc: {resolved_bus_station_loc}")

    # 步骤5) 酒店到指定公交站点直线距离
    distance_result = maps_distance(
        origins=hotel_location,
        destination=resolved_bus_station_loc,
    )
    if distance_result.error:
        print(f"❌ 计算酒店到公交站直线距离失败: {distance_result.error}")
        return False
    if not distance_result.results or len(distance_result.results) == 0:
        print("❌ 未获得直线距离计算结果")
        return False

    straight_distance = distance_result.results[0].distance_meters
    if straight_distance > max_straight_distance_to_bus_station:
        print(
            f"❌ 酒店到绥德客运站的直线距离为 {straight_distance} 米，超过 {max_straight_distance_to_bus_station} 米"
        )
        return False
    print(
        f"✅ 酒店到绥德客运站的直线距离为 {straight_distance} 米，满足 ≤ {max_straight_distance_to_bus_station} 米"
    )

    # 步骤6) 酒店到绥德客运站驾车时间
    driving_to_bus_station = maps_driving_by_coordinates(
        origin=hotel_location,
        destination=resolved_bus_station_loc,
    )
    if driving_to_bus_station.error:
        print(f"❌ 计算酒店到绥德客运站的驾车路线失败: {driving_to_bus_station.error}")
        return False
    if driving_to_bus_station.total_duration_seconds is None:
        print("❌ 驾车结果中无总时间信息")
        return False

    driving_duration_bus = driving_to_bus_station.total_duration_seconds
    if driving_duration_bus >= max_driving_duration_to_bus_station:
        print(
            f"❌ 酒店到绥德客运站驾车时间为 {driving_duration_bus} 秒，不满足 < {max_driving_duration_to_bus_station} 秒"
        )
        return False
    print(
        f"✅ 酒店到绥德客运站驾车时间为 {driving_duration_bus} 秒，满足 < {max_driving_duration_to_bus_station} 秒"
    )

    # 步骤7) 酒店附近1200米内有公交站 & 最近公交站步行距离
    nearby_bus_result = maps_around_search(
        location=hotel_location,
        radius=str(nearby_bus_radius),
        keywords=nearby_bus_keywords,
    )
    if nearby_bus_result.error:
        print(f"❌ 搜索酒店附近公交站失败: {nearby_bus_result.error}")
        return False
    if not nearby_bus_result.pois or len(nearby_bus_result.pois) == 0:
        print(
            f"❌ 在酒店 {nearby_bus_radius} 米范围内未找到任何公交站"
        )
        return False

    min_walking_distance = None
    for bus_poi in nearby_bus_result.pois:
        if not bus_poi.location:
            continue
        walk_res = maps_walking_by_coordinates(
            origin=hotel_location,
            destination=bus_poi.location,
        )
        if walk_res.error:
            print(
                f"⚠️ 计算到公交站 {bus_poi.name} 的步行路线失败: {walk_res.error}"
            )
            continue
        if walk_res.total_distance_meters is None:
            print(
                f"⚠️ 到公交站 {bus_poi.name} 的步行结果无距离信息"
            )
            continue

        dist = walk_res.total_distance_meters
        if min_walking_distance is None or dist < min_walking_distance:
            min_walking_distance = dist

    if min_walking_distance is None:
        print("❌ 无法获得任何公交站的步行距离")
        return False

    if min_walking_distance > max_nearest_bus_walking_distance:
        print(
            f"❌ 到最近公交站的最小步行距离为 {min_walking_distance} 米，超过 {max_nearest_bus_walking_distance} 米"
        )
        return False

    print(
        f"✅ 到最近公交站的最小步行距离为 {min_walking_distance} 米，满足 ≤ {max_nearest_bus_walking_distance} 米"
    )

    print("✅ 所有验证步骤均通过！")
    return True


if __name__ == "__main__":
    print("开始验证 782.py 文件...\n")
    result = verify_poi(poi_id="B0LUPR24CB")
    print(f"\n验证结果: {result}")