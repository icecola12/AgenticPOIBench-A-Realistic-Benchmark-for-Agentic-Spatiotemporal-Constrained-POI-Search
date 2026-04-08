
"""
修改任务指令：你要在附近8000米以内找一家图书馆。你希望这家图书馆离海口东站和美兰国际机场这条开车路线不要绕太远：从海口东站先到图书馆再到美兰国际机场的总开车时间不能超过45分钟，而且相比直接从海口东站开到美兰国际机场，总耗时增加不能超过5分钟。另外，你不想去离海口市美术馆太近的图书馆，至少要离它直线距离1公里以上。最后，这家图书馆周围400米内要有公交站，方便你从图书馆出来就能坐车。你虽然心情不好，但仍然保持礼貌和独立的姿态。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近范围：调用 maps_around_search(location='110.344456,20.072794', radius='8000', keywords='图书馆')，验证返回pois数量≥8，且其中包含目标POI id='B038202LX3'。
2) 目标POI信息：调用 maps_search_detail(id='B038202LX3') 获取目标POI坐标 destination_loc。
3) 获取A/B坐标：调用 maps_text_search(keywords='海口东站', city='海口') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取A坐标A_loc=110.342865,19.983409；调用 maps_text_search(keywords='美兰国际机场', city='海口') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取B坐标B_loc=110.461334,19.941988。
4) 行程总时长约束（A→目标→B）：调用 maps_driving_by_coordinates(origin=A_loc, destination=destination_loc) 得到tA；调用 maps_driving_by_coordinates(origin=destination_loc, destination=B_loc) 得到tB；验证 (tA+tB) ≤ 45分钟（即≤2700秒）。
5) 绕行增加时长约束：调用 maps_driving_by_coordinates(origin=A_loc, destination=B_loc) 得到tDirect；验证 (tA+tB - tDirect) ≤ 5分钟（即≤300秒）。
6) 不在某地附近：调用 maps_around_search(location=destination_loc, radius='1000', keywords='海口市美术馆')，验证返回pois为空（或返回pois中不包含"海口市美术馆"）。等价验证也可：用 maps_text_search + maps_search_detail 获取"海口市美术馆"坐标M_loc=110.360851,20.007323，再调用 maps_distance(origins=M_loc, destination=destination_loc)，验证直线距离>1000米。
7) 途径点附近有指定POI类型A（公交站）：调用 maps_around_search(location=destination_loc, radius='400', keywords='公交站')，验证返回pois非空。
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
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "110.344456,20.072794",
    search_radius: int = 8000,
    keywords: str = "图书馆",
    min_pois_count: int = 8,
    station_a_address: str = "海口东站",
    station_a_city: str = "海口",
    station_b_address: str = "美兰国际机场",
    station_b_city: str = "海口",
    max_total_detour_time: int = 2700,  # 45 minutes = 2700 seconds
    max_detour_increase: int = 300,  # 5 minutes = 300 seconds
    avoid_location_address: str = "海口市美术馆",
    avoid_location_city: str = "海口",
    min_distance_from_avoid: int = 1000,  # meters
    bus_stop_search_radius: int = 400,
    bus_stop_keywords: str = "公交站"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近范围：调用 maps_around_search，验证返回pois数量≥8，且其中包含目标POI。
    2) 目标POI信息：调用 maps_search_detail 获取目标POI坐标。
    3) 获取A/B坐标：获取海口东站和美兰国际机场坐标。
    4) 行程总时长约束（A→目标→B）：验证总时长≤45分钟。
    5) 绕行增加时长约束：验证绕行增加时长≤5分钟。
    6) 不在某地附近：验证与海口市美术馆的距离>1000米。
    7) 途径点附近有指定POI类型A（公交站）：验证周围400米内有公交站。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"110.344456,20.072794"
        search_radius: 搜索半径（米），默认8000
        keywords: 搜索关键词，默认"图书馆"
        min_pois_count: 最少POI数量，默认8
        station_a_address: 起点站地址，默认"海口东站"
        station_a_city: 起点站所在城市，默认"海口"
        station_b_address: 终点站地址，默认"美兰国际机场"
        station_b_city: 终点站所在城市，默认"海口"
        max_total_detour_time: 最大绕行总时间（秒），默认2700（45分钟）
        max_detour_increase: 最大绕行增加时间（秒），默认300（5分钟）
        avoid_location_address: 需要避开的地点地址，默认"海口市美术馆"
        avoid_location_city: 需要避开的地点所在城市，默认"海口"
        min_distance_from_avoid: 与需要避开的地点的最小距离（米），默认1000
        bus_stop_search_radius: 公交站搜索半径（米），默认400
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近范围
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

    # 检查POI数量是否满足要求
    pois_count = len(around_search_result.pois)
    if pois_count < min_pois_count:
        print(f"❌ 找到的POI数量{pois_count}个，少于要求的{min_pois_count}个")
        return False
    print(f"✅ 找到{pois_count}个POI，符合要求（>= {min_pois_count}个）")

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

    # 步骤3: 获取A/B坐标
    station_a_text_search_result = maps_text_search(keywords=station_a_address, city=station_a_city)
    if station_a_text_search_result.error:
        print(f"❌ 获取起点站坐标失败: {station_a_text_search_result.error}")
        return False

    if not station_a_text_search_result.pois or len(station_a_text_search_result.pois) == 0:
        print(f"❌ 未找到起点站坐标")
        return False

    station_a_poi_id = station_a_text_search_result.pois[0].id
    station_a_detail_result = maps_search_detail(id=station_a_poi_id)
    if station_a_detail_result.error:
        print(f"❌ 获取起点站详情失败: {station_a_detail_result.error}")
        return False
    if not station_a_detail_result.location:
        print(f"❌ 起点站没有location信息")
        return False
    station_a_location = station_a_detail_result.location
    print(f"✅ 获取起点站坐标: {station_a_location} ({station_a_address})")

    station_b_text_search_result = maps_text_search(keywords=station_b_address, city=station_b_city)
    if station_b_text_search_result.error:
        print(f"❌ 获取终点站坐标失败: {station_b_text_search_result.error}")
        return False

    if not station_b_text_search_result.pois or len(station_b_text_search_result.pois) == 0:
        print(f"❌ 未找到终点站坐标")
        return False

    station_b_poi_id = station_b_text_search_result.pois[0].id
    station_b_detail_result = maps_search_detail(id=station_b_poi_id)
    if station_b_detail_result.error:
        print(f"❌ 获取终点站详情失败: {station_b_detail_result.error}")
        return False
    if not station_b_detail_result.location:
        print(f"❌ 终点站没有location信息")
        return False
    station_b_location = station_b_detail_result.location
    print(f"✅ 获取终点站坐标: {station_b_location} ({station_b_address})")

    # 步骤4: 行程总时长约束（A→目标→B）
    # 计算从起点站到POI的驾车时间
    a_to_poi_result = maps_driving_by_coordinates(origin=station_a_location, destination=poi_location)
    if a_to_poi_result.error:
        print(f"❌ 计算从起点站到POI驾车路线失败: {a_to_poi_result.error}")
        return False

    if a_to_poi_result.total_duration_seconds is None:
        print(f"❌ 无法获取从起点站到POI驾车时长")
        return False

    t_a_to_poi = a_to_poi_result.total_duration_seconds
    print(f"✅ 从起点站到POI驾车时长{t_a_to_poi}秒")

    # 计算从POI到终点站的驾车时间
    poi_to_b_result = maps_driving_by_coordinates(origin=poi_location, destination=station_b_location)
    if poi_to_b_result.error:
        print(f"❌ 计算从POI到终点站驾车路线失败: {poi_to_b_result.error}")
        return False

    if poi_to_b_result.total_duration_seconds is None:
        print(f"❌ 无法获取从POI到终点站驾车时长")
        return False

    t_poi_to_b = poi_to_b_result.total_duration_seconds
    print(f"✅ 从POI到终点站驾车时长{t_poi_to_b}秒")

    # 计算总绕行时间
    total_detour_time = t_a_to_poi + t_poi_to_b
    if total_detour_time > max_total_detour_time:
        print(f"❌ 绕行总时间{total_detour_time}秒（{total_detour_time / 60:.2f}分钟），超过{max_total_detour_time}秒（{max_total_detour_time // 60}分钟）")
        return False
    print(f"✅ 绕行总时间{total_detour_time}秒（{total_detour_time / 60:.2f}分钟），符合要求（<= {max_total_detour_time}秒，即{max_total_detour_time // 60}分钟）")

    # 步骤5: 绕行增加时长约束
    # 计算从起点站直接到终点站的驾车时间
    a_to_b_result = maps_driving_by_coordinates(origin=station_a_location, destination=station_b_location)
    if a_to_b_result.error:
        print(f"❌ 计算从起点站到终点站驾车路线失败: {a_to_b_result.error}")
        return False

    if a_to_b_result.total_duration_seconds is None:
        print(f"❌ 无法获取从起点站到终点站驾车时长")
        return False

    t_a_to_b = a_to_b_result.total_duration_seconds
    print(f"✅ 从起点站直接到终点站驾车时长{t_a_to_b}秒")

    # 计算绕行增加的时间
    detour_increase = total_detour_time - t_a_to_b
    if detour_increase > max_detour_increase:
        print(f"❌ 绕行增加时间{detour_increase}秒（{detour_increase / 60:.2f}分钟），超过{max_detour_increase}秒（{max_detour_increase // 60}分钟）")
        return False
    print(f"✅ 绕行增加时间{detour_increase}秒（{detour_increase / 60:.2f}分钟），符合要求（<= {max_detour_increase}秒，即{max_detour_increase // 60}分钟）")

    # 步骤6: 不在某地附近
    avoid_text_search_result = maps_text_search(keywords=avoid_location_address, city=avoid_location_city)
    if avoid_text_search_result.error:
        print(f"❌ 获取避开地点坐标失败: {avoid_text_search_result.error}")
        return False

    if not avoid_text_search_result.pois or len(avoid_text_search_result.pois) == 0:
        print(f"❌ 未找到避开地点坐标")
        return False

    avoid_poi_id = avoid_text_search_result.pois[0].id
    avoid_detail_result = maps_search_detail(id=avoid_poi_id)
    if avoid_detail_result.error:
        print(f"❌ 获取避开地点详情失败: {avoid_detail_result.error}")
        return False
    if not avoid_detail_result.location:
        print(f"❌ 避开地点没有location信息")
        return False
    avoid_location = avoid_detail_result.location
    print(f"✅ 获取避开地点坐标: {avoid_location} ({avoid_location_address})")

    distance_result = maps_distance(origins=avoid_location, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到距离信息")
        return False

    distance_to_avoid = distance_result.results[0].distance_meters
    if distance_to_avoid <= min_distance_from_avoid:
        print(f"❌ 与{avoid_location_address}的距离{distance_to_avoid}米，小于或等于要求的{min_distance_from_avoid}米")
        return False
    print(f"✅ 与{avoid_location_address}的距离{distance_to_avoid}米，符合要求（> {min_distance_from_avoid}米）")

    # 步骤7: 途径点附近有指定POI类型A（公交站）
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

    print(f"✅ 找到公交站: {bus_stop_search_result.pois[0].name} (共{len(bus_stop_search_result.pois)}个)")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 857.py 文件...\\n")
    result = verify_poi(poi_id="B038202LX3")
    print(f"\n验证结果: {result}")
