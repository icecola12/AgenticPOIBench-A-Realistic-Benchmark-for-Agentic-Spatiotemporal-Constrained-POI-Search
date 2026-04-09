
"""
修改任务指令：你想在附近2000米以内找一家洗衣店。洗衣店评分至少4.0分。这家洗衣店不能在田洁干洗店直线距离500米以内。你去洗衣店的路上，会经过一个离涿州博物馆直线距离不到200米的地方。洗衣店到双塔路口公交站的步行时间不能超过15分钟。你洗完衣服后要去涿州站赶火车，所以从你家到洗衣店再到涿州站的总步行时间不能超过35分钟，而且这样绕一下比你直接去涿州站最多只能多花5分钟。另外，你朋友从涿州汽车站过去，你步行到洗衣店的时间要比朋友少至少5分钟。你情绪化，时而冷静时而愤怒，态度变化快。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_search_detail('B0K0AUYCBT')获取洗衣店评分，验证≥4.0
2. 调用maps_around_search('115.972129,39.494747','洗衣店',2000)验证目标洗衣店在搜索范围内
3. 调用maps_distance('115.976214,39.500802','115.976606,39.494632')计算目标洗衣店与田洁干洗的距离，验证>500米
4. 调用maps_walking_by_coordinates('115.972129,39.494747','115.976214,39.500802')获取步行路线步骤，对每个步骤点调用maps_distance计算其到涿州博物馆(115.973477,39.494006)的直线距离，验证至少有一个步骤点距离<200米
5. 调用maps_walking_by_coordinates('115.976214,39.500802','115.970123,39.501209')计算洗衣店到双塔路口公交站的步行时间，验证≤900秒(15分钟)
6. 调用maps_walking_by_coordinates计算从家到洗衣店再到涿州站的总步行时间：t1 = maps_walking_by_coordinates('115.972129,39.494747','115.976214,39.500802').total_duration_seconds；t2 = maps_walking_by_coordinates('115.976214,39.500802','115.985022,39.481591').total_duration_seconds；验证t1 + t2 ≤ 2100秒(35分钟)
7. 调用maps_walking_by_coordinates('115.972129,39.494747','115.985022,39.481591')获取直接从家到涿州站的步行时间t3，验证(t1 + t2) - t3 ≤ 300秒(5分钟)
8. 调用maps_walking_by_coordinates('115.966407,39.494702','115.976214,39.500802')获取从涿州汽车站到洗衣店的步行时间t4，验证t4 - t1 ≥ 300秒(5分钟)
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
    maps_geo,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.972129,39.494747",
    search_radius: int = 2000,
    keywords: str = "洗衣店",
    min_rating: float = 4.0,
    avoid_shop_name: str = "田洁干洗店",
    min_distance_from_avoid: int = 500,  # meters
    museum_name: str = "涿州博物馆",
    max_distance_to_museum: int = 200,  # meters
    bus_stop_name: str = "双塔路口",
    max_walking_to_bus: int = 900,  # 15 minutes = 900 seconds
    station_name: str = "涿州站",
    max_total_walking: int = 2100,  # 35 minutes = 2100 seconds
    max_detour_increase: int = 300,  # 5 minutes = 300 seconds
    bus_terminal_name: str = "涿州汽车站",
    min_time_difference: int = 300,  # 5 minutes = 300 seconds
    city: str = "涿州"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1. 获取洗衣店评分，验证≥4.0
    2. 验证目标洗衣店在搜索范围内
    3. 计算目标���衣店与田洁干洗的距离，验证>500米
    4. 获取步行路线步骤，验证至少有一个步骤点距离涿州博物馆<200米
    5. 计算洗衣店到双塔路口公交站的步行时间，验证≤900秒
    6. 计算从家到洗衣店再到涿州站的总步行时间，验证≤2100秒
    7. 验证绕行增加时间≤300秒
    8. 验证朋友从涿州汽车站到洗衣店的时间比你多至少300秒

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"115.972129,39.494747"
        search_radius: 搜索半径（米），默认2000
        keywords: 搜索关键词，默认"洗衣店"
        min_rating: 最低评分，默认4.0
        avoid_shop_name: 需要避开的店铺名称，默认"田洁干洗店"
        min_distance_from_avoid: 与需要避开的店铺的最小距离（米），默认500
        museum_name: 博物馆名称，默认"涿州博物馆"
        max_distance_to_museum: 到博物馆的最大距离（米），默认200
        bus_stop_name: 公交站名称，默认"双塔路口"
        max_walking_to_bus: 最大步行到公交站时间（秒），默认900（15分钟）
        station_name: 火车站名称，默认"涿州站"
        max_total_walking: 最大总步行时间（秒），默认2100（35分钟）
        max_detour_increase: 最大绕行增加时间（秒），默认300（5分钟）
        bus_terminal_name: 汽车站名称，默认"涿州汽车站"
        min_time_difference: 最小时间差（秒），默认300（5分钟）
        city: 城市名称，默认"涿州"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 查询各个地点的坐标
    # 查询田洁干洗店坐标（使用around_search在用户附近搜索）
    avoid_shop_search = maps_around_search(location=user_location, radius="5000", keywords=avoid_shop_name)
    if avoid_shop_search.error or not avoid_shop_search.pois or len(avoid_shop_search.pois) == 0:
        print(f"❌ 无法获取{avoid_shop_name}的坐标")
        return False
    avoid_shop_location = avoid_shop_search.pois[0].location
    print(f"✅ 获取{avoid_shop_name}坐标: {avoid_shop_location}")

    # 查询博物馆坐标（使用around_search）
    museum_search = maps_around_search(location=user_location, radius="5000", keywords=museum_name)
    if museum_search.error or not museum_search.pois or len(museum_search.pois) == 0:
        print(f"❌ 无法获取{museum_name}的坐标")
        return False
    museum_location = museum_search.pois[0].location
    print(f"✅ 获取{museum_name}坐标: {museum_location}")

    # 查询公交站坐标（使用around_search）
    bus_stop_search = maps_around_search(location=user_location, radius="5000", keywords=bus_stop_name)
    if bus_stop_search.error or not bus_stop_search.pois or len(bus_stop_search.pois) == 0:
        print(f"❌ 无法获取{bus_stop_name}的坐标")
        return False
    bus_stop_location = bus_stop_search.pois[0].location
    print(f"✅ 获取{bus_stop_name}坐标: {bus_stop_location}")

    # 查询火车站坐标（使用geo）
    station_geo = maps_geo(address=station_name, city=city)
    if station_geo.error or not station_geo.results or len(station_geo.results) == 0:
        print(f"❌ 无法获取{station_name}的坐标")
        return False
    station_location = station_geo.results[0].location
    print(f"✅ 获取{station_name}坐标: {station_location}")

    # 查询汽车站坐标（使用geo）
    bus_terminal_geo = maps_geo(address=bus_terminal_name, city=city)
    if bus_terminal_geo.error or not bus_terminal_geo.results or len(bus_terminal_geo.results) == 0:
        print(f"❌ 无法获取{bus_terminal_name}的坐标")
        return False
    bus_terminal_location = bus_terminal_geo.results[0].location
    print(f"✅ 获取{bus_terminal_name}坐标: {bus_terminal_location}")

    # 步骤1: 获取洗衣店评分
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分
    if poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        try:
            rating = float(poi_detail.biz_ext['rating'])
            if rating < min_rating:
                print(f"❌ POI评分{rating}分，低于要求的{min_rating}分")
                return False
            print(f"✅ POI评分{rating}分，符合要求（>= {min_rating}分）")
        except (ValueError, TypeError):
            print(f"❌ 无法解析POI评分")
            return False
    else:
        print(f"❌ POI没有评分信息")
        return False

    # 步骤2: 验证目标洗衣店在搜索范围内
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

    # 步骤3: 计算目标洗衣店与田洁干洗的距离
    distance_result = maps_distance(origins=poi_location, destination=avoid_shop_location)
    if distance_result.error:
        print(f"❌ 计算距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到距离信息")
        return False

    distance_to_avoid = distance_result.results[0].distance_meters
    if distance_to_avoid <= min_distance_from_avoid:
        print(f"❌ 与田洁干洗店的距离{distance_to_avoid}米，小于或等于要求的{min_distance_from_avoid}米")
        return False
    print(f"✅ 与田洁干洗店的距离{distance_to_avoid}米，符合要求（> {min_distance_from_avoid}米）")

    # 步骤4: 获取步行路线步骤，验证至少有一个步骤点距离涿州博物馆<200米
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    t1 = walking_result.total_duration_seconds
    print(f"✅ 从家到洗衣店步行时长{t1}秒")

    # 检查步行路线中是否有步骤点距离博物馆<200米
    has_close_point = False
    if walking_result.steps:
        for step in walking_result.steps:
            # 检查起点坐标
            if step.from_coordinates:
                dist_result = maps_distance(origins=step.from_coordinates, destination=museum_location)
                if not dist_result.error and dist_result.results and len(dist_result.results) > 0:
                    dist = dist_result.results[0].distance_meters
                    if dist < max_distance_to_museum:
                        has_close_point = True
                        print(f"✅ 找到距离博物馆{dist}米的步骤点，符合要求（< {max_distance_to_museum}米）")
                        break

    if not has_close_point:
        print(f"❌ 步行路线中没有距离博物馆小于{max_distance_to_museum}米的步骤点")
        return False

    # 步骤5: 计算洗衣店到双塔路口公交站的步行时间
    walking_to_bus_result = maps_walking_by_coordinates(origin=poi_location, destination=bus_stop_location)
    if walking_to_bus_result.error:
        print(f"❌ 计算到公交站步行路线失败: {walking_to_bus_result.error}")
        return False

    if walking_to_bus_result.total_duration_seconds is None:
        print(f"❌ 无法获取到公交站步行时长")
        return False

    walking_to_bus_duration = walking_to_bus_result.total_duration_seconds
    if walking_to_bus_duration > max_walking_to_bus:
        print(f"❌ 到公交站步行时长{walking_to_bus_duration}秒（{walking_to_bus_duration / 60:.2f}分钟），超过{max_walking_to_bus}秒（{max_walking_to_bus // 60}分钟）")
        return False
    print(f"✅ 到公交站步行时长{walking_to_bus_duration}秒（{walking_to_bus_duration / 60:.2f}分钟），符合要求（<= {max_walking_to_bus}秒，即{max_walking_to_bus // 60}分钟）")

    # 步骤6: 计算从家到洗衣店再到涿州站的总步行时间
    walking_to_station_result = maps_walking_by_coordinates(origin=poi_location, destination=station_location)
    if walking_to_station_result.error:
        print(f"❌ 计算从洗衣店到火车站步行路线失败: {walking_to_station_result.error}")
        return False

    if walking_to_station_result.total_duration_seconds is None:
        print(f"❌ 无法获取从洗衣店到火车站步行时长")
        return False

    t2 = walking_to_station_result.total_duration_seconds
    print(f"✅ 从洗衣店到火车站步行时长{t2}秒")

    total_walking_time = t1 + t2
    if total_walking_time > max_total_walking:
        print(f"❌ 总步行时间{total_walking_time}秒（{total_walking_time / 60:.2f}分钟），超过{max_total_walking}秒（{max_total_walking // 60}分钟）")
        return False
    print(f"✅ 总步行时间{total_walking_time}秒（{total_walking_time / 60:.2f}分钟），符合要求（<= {max_total_walking}秒，即{max_total_walking // 60}分钟）")

    # 步骤7: 验证绕行增加时间≤300秒
    direct_walking_result = maps_walking_by_coordinates(origin=user_location, destination=station_location)
    if direct_walking_result.error:
        print(f"❌ 计算直接到火车站步行路线失败: {direct_walking_result.error}")
        return False

    if direct_walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取直接到火车站步行时长")
        return False

    t3 = direct_walking_result.total_duration_seconds
    print(f"✅ 直接从家到火车站步行时长{t3}秒")

    detour_increase = total_walking_time - t3
    if detour_increase > max_detour_increase:
        print(f"❌ 绕行增加时间{detour_increase}秒（{detour_increase / 60:.2f}分钟），超过{max_detour_increase}秒（{max_detour_increase // 60}分钟）")
        return False
    print(f"✅ 绕行增加时间{detour_increase}秒（{detour_increase / 60:.2f}分钟），符合要求（<= {max_detour_increase}秒，即{max_detour_increase // 60}分钟）")

    # 步骤8: 验证朋友从涿州汽车站到洗衣店的时间比你多至少300秒
    friend_walking_result = maps_walking_by_coordinates(origin=bus_terminal_location, destination=poi_location)
    if friend_walking_result.error:
        print(f"❌ 计算从汽车站到洗衣店步行路线失败: {friend_walking_result.error}")
        return False

    if friend_walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取从汽车站到洗衣店步行时长")
        return False

    t4 = friend_walking_result.total_duration_seconds
    print(f"✅ 朋友从汽车站到洗衣店步行时长{t4}秒")

    time_difference = t4 - t1
    if time_difference < min_time_difference:
        print(f"❌ 朋友比你多花{time_difference}秒（{time_difference / 60:.2f}分钟），少于要求的{min_time_difference}秒（{min_time_difference // 60}分钟）")
        return False
    print(f"✅ 朋友比你多花{time_difference}秒（{time_difference / 60:.2f}分钟），符合要求（>= {min_time_difference}秒，即{min_time_difference // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 894.py 文件...\n")
    result = verify_poi(poi_id="B0K0AUYCBT")
    print(f"\n验证结果: {result}")
