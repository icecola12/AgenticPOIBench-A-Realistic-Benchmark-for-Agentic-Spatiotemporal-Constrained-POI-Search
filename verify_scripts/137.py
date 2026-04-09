
"""
修改任务指令：你要在附近2000米以内找一家酒店。你希望这家酒店的评分至少有4.8分。另外你打算退房后直接去赶火车，所以从酒店开车到涿州站的时间不能超过5分钟。你还想出门坐公交，要求酒店在1500米范围内能找到公交站，并且从酒店走到这些公交站里最近的那个，步行距离不要超过2000米；同时酒店到这个步行最近公交站的直线距离也要在500米以内。最后，你想确认即使走路也能到，要求从你这里步行到酒店的距离不超过1000米，同时从你这里开车过去不超过2公里。你情绪化，时而冷静时而愤怒，态度变化快。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边约束：调用 maps_around_search(location='115.975038,39.4803', radius='2000', keywords='酒店')，验证返回列表中包含 target_poi_id='B0LUDM8OZZ'。
2) 评分约束：调用 maps_search_detail(id='B0LUDM8OZZ')，读取 biz_ext.rating，验证 rating >= 4.8。
3) 出发地到酒店最大步行距离：从步骤1或步骤2获取酒店坐标destination='115.980631,39.481042'，调用 maps_walking_by_coordinates(origin='115.975038,39.4803', destination=destination)，验证 total_distance_meters <= 1000。
4) 出发地到酒店最大驾车距离：调用 maps_driving_by_coordinates(origin='115.975038,39.4803', destination=destination)，验证 total_distance_meters <= 2000。
5) 酒店到涿州站最大驾车时间：调用 maps_text_search(keywords='涿州站', city='保定') 取 poi_id，再 maps_search_detail(id=poi_id) 获取 涿州站坐标 station；再调用 maps_driving_by_coordinates(origin=destination, destination=station)，验证 total_duration_seconds <= 300。
6) 酒店附近1500米内公交站集合：调用 maps_around_search(location=destination, radius='1500', keywords='公交站')，得到公交站列表S。
7) 最近公交站步行距离上限：对S中每个公交站p，调用 maps_walking_by_coordinates(origin=destination, destination=p.location)，取最小步行距离 d_walk_min，验证 d_walk_min <= 2000。并获取这个最近公交站的坐标 nearest_bus_location。
8) 验证步行距离最小的公交站的直线距离在500米内：对步骤7中获取的不行最近公交车站，调用 maps_distance(origins=destination, destination=nearest_bus_location。)，验证 d_line <= 500。
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
    maps_walking_by_coordinates,
    maps_distance,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.975038,39.4803",
    target_poi_id: str = "B0LUDM8OZZ",
    around_radius: int = 2000,
    around_keywords: str = "酒店",
    destination: str = "115.980631,39.481042",
    min_rating: float = 4.8,
    max_walking_distance_to_hotel: int = 1000,  # 米
    max_driving_distance_to_hotel: int = 2000,  # 米
    station_address: str = "涿州站",
    station_city: str = "保定",
    station_location: str = "115.985022,39.481591",
    max_driving_duration_to_station: int = 300,  # 秒
    nearby_bus_radius: int = 1500,
    nearby_bus_keywords: str = "公交站",
    max_nearest_bus_walking_distance: int = 2000,  # 米
    max_nearest_bus_line_distance: int = 500,  # 米
) -> bool:
    """
    验证POI是否符合要求（严格按照注释步骤）.
    """
    # 步骤1) 周边约束：周边搜索酒店，验证包含目标POI
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

    hotel_location = destination
    print(f"✅ 使用酒店坐标 destination: {hotel_location}")

    # 步骤2) 评分约束：评分 >= 4.8
    detail = maps_search_detail(id=target_poi_id)
    if detail.error:
        print(f"❌ 获取酒店详情失败: {detail.error}")
        return False

    rating = None
    if detail.biz_ext and isinstance(detail.biz_ext, dict):
        rating_raw = detail.biz_ext.get("rating")
        try:
            rating = float(rating_raw) if rating_raw not in (None, "") else None
        except (TypeError, ValueError):
            rating = None

    if rating is None:
        print("❌ 无法获取酒店评分 biz_ext.rating")
        return False

    if rating < min_rating:
        print(f"❌ 酒店评分 {rating} < {min_rating}")
        return False

    print(f"✅ 酒店评分 {rating} ≥ {min_rating}")

    # 步骤3) 出发地到酒店最大步行距离
    walking_to_hotel = maps_walking_by_coordinates(
        origin=user_location,
        destination=hotel_location,
    )
    if walking_to_hotel.error:
        print(f"❌ 计算出发地到酒店的步行路线失败: {walking_to_hotel.error}")
        return False
    if walking_to_hotel.total_distance_meters is None:
        print("❌ 步行结果中无总距离信息")
        return False

    walk_distance = walking_to_hotel.total_distance_meters
    if walk_distance > max_walking_distance_to_hotel:
        print(
            f"❌ 出发地到酒店的步行距离为 {walk_distance} 米，超过 {max_walking_distance_to_hotel} 米"
        )
        return False
    print(
        f"✅ 出发地到酒店的步行距离为 {walk_distance} 米，满足 ≤ {max_walking_distance_to_hotel} 米"
    )

    # 步骤4) 出发地到酒店最大驾车距离
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

    # 步骤5) 酒店到涿州站最大驾车时间（用 maps_text_search + maps_search_detail 替代 maps_geo）
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"❌ 获取涿州站坐标失败: {station_text_result.error}")
        return False
    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print("❌ 未找到涿州站的地理编码结果")
        return False

    first_poi_id = station_text_result.pois[0].id
    station_detail_result = maps_search_detail(id=first_poi_id)
    if station_detail_result.error or not station_detail_result.location:
        print("❌ 获取涿州站坐标失败")
        return False
    station_loc = station_detail_result.location
    print(f"✅ 使用涿州站坐标 station: {station_loc}")

    driving_to_station = maps_driving_by_coordinates(
        origin=hotel_location,
        destination=station_loc,
    )
    if driving_to_station.error:
        print(f"❌ 计算酒店到涿州站的驾车路线失败: {driving_to_station.error}")
        return False
    if driving_to_station.total_duration_seconds is None:
        print("❌ 驾车结果中无总时间信息")
        return False

    duration_to_station = driving_to_station.total_duration_seconds
    if duration_to_station > max_driving_duration_to_station:
        print(
            f"❌ 酒店到涿州站驾车时间为 {duration_to_station} 秒，超过 {max_driving_duration_to_station} 秒"
        )
        return False
    print(
        f"✅ 酒店到涿州站驾车时间为 {duration_to_station} 秒，满足 ≤ {max_driving_duration_to_station} 秒"
    )

    # 步骤6) 酒店附近1500米内公交站集合
    around_bus = maps_around_search(
        location=hotel_location,
        radius=str(nearby_bus_radius),
        keywords=nearby_bus_keywords,
    )
    if around_bus.error:
        print(f"❌ 搜索酒店附近公交站失败: {around_bus.error}")
        return False
    if not around_bus.pois or len(around_bus.pois) == 0:
        print(
            f"❌ 在酒店 {nearby_bus_radius} 米范围内未找到任何公交站"
        )
        return False

    bus_pois = [p for p in around_bus.pois if p.location is not None]
    if len(bus_pois) == 0:
        print("❌ 公交站结果中均缺少坐标信息")
        return False
    print(f"✅ 在酒店附近找到 {len(bus_pois)} 个带坐标的公交站")

    # 步骤7) 最近公交站步行距离上限：记录最近公交站坐标
    min_walking_distance = None
    nearest_bus_location = None

    for p in bus_pois:
        walk_res = maps_walking_by_coordinates(
            origin=hotel_location,
            destination=p.location,
        )
        if walk_res.error:
            print(
                f"⚠️ 计算到公交站 {p.name} 的步行路线失败: {walk_res.error}"
            )
            continue
        if walk_res.total_distance_meters is None:
            print(
                f"⚠️ 到公交站 {p.name} 的步行结果无距离信息"
            )
            continue

        dist = walk_res.total_distance_meters
        if min_walking_distance is None or dist < min_walking_distance:
            min_walking_distance = dist
            nearest_bus_location = p.location

    if min_walking_distance is None or nearest_bus_location is None:
        print("❌ 无法获得最近公交站的步行距离或坐标")
        return False

    if min_walking_distance > max_nearest_bus_walking_distance:
        print(
            f"❌ 最近公交站的步行距离为 {min_walking_distance} 米，超过 {max_nearest_bus_walking_distance} 米"
        )
        return False
    print(
        f"✅ 最近公交站的步行距离为 {min_walking_distance} 米，满足 ≤ {max_nearest_bus_walking_distance} 米；最近公交站坐标: {nearest_bus_location}"
    )

    # 步骤8) 验证该公交站直线距离在300米内
    distance_bus_line = maps_distance(
        origins=hotel_location,
        destination=nearest_bus_location,
    )
    if distance_bus_line.error:
        print(f"❌ 计算酒店与最近公交站直线距离失败: {distance_bus_line.error}")
        return False
    if not distance_bus_line.results or len(distance_bus_line.results) == 0:
        print("❌ 未获得直线距离计算结果")
        return False

    d_line = distance_bus_line.results[0].distance_meters
    if d_line > max_nearest_bus_line_distance:
        print(
            f"❌ 酒店到最近公交站的直线距离为 {d_line} 米，超过 {max_nearest_bus_line_distance} 米"
        )
        return False
    print(
        f"✅ 酒店到最近公交站的直线距离为 {d_line} 米，满足 ≤ {max_nearest_bus_line_distance} 米"
    )

    print("✅ 所有验证步骤均通过！")
    return True


if __name__ == "__main__":
    print("开始验证 783.py 文件...\n")
    result = verify_poi(poi_id="B0LUDM8OZZ")
    print(f"\n验证结果: {result}")