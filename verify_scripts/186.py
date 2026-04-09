
"""
修改任务指令：你想在附近2500米以内找一家博物馆。你不想去那种离"济宁市任城区党史陈列馆"太近的地方，所以这家博物馆要离它直线距离至少800米。你打算从济宁站出发开车，先到这家博物馆停一下再回到你这里；这个总的开车时间不能超过12分钟，而且相比直接从济宁站开车到你这里，绕去博物馆增加的开车时间不能超过2分钟。另外你还希望这家博物馆走路去附近500米最近的公交站不超过8分钟。你逻辑性强但没有耐心，希望高效沟通，讨厌废话。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近范围：调用 maps_around_search(location='116.569338,35.422161', radius='2500', keywords='博物馆')，验证返回pois中包含 target_poi_id=B021905525。
2) POI类型与评分：调用 maps_search_detail(id='B021905525')，验证 biz_ext.rating≥4.6（该POI返回rating=4.6）。
3) 不在其他地点附近：调用 maps_text_search(keywords='济宁市任城区党史陈列馆', city='济宁') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取其坐标；再调用 maps_distance(origins='116.581734,35.410706', destination=党史陈列馆坐标) 验证直线距离≥800米。
4) 绕行总行程时间上限：调用 maps_text_search(keywords='济宁站', city='济宁') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取济宁站坐标；调用 maps_driving_by_coordinates(origin=济宁站坐标, destination='116.581734,35.410706') 得到t_A_to_P；调用 maps_driving_by_coordinates(origin='116.581734,35.410706', destination='116.569338,35.422161') 得到t_P_to_B；验证 (t_A_to_P + t_P_to_B) ≤ 12分钟。
5) 绕行相对增量：调用 maps_driving_by_coordinates(origin=济宁站坐标, destination='116.569338,35.422161') 得到t_A_to_B；验证 (t_A_to_P + t_P_to_B - t_A_to_B) ≤ 2分钟。（本数据下约(254+? -369)秒；其中A->P=254秒，A->B=369秒，P->B可再算，需满足约束）
6) 交通枢纽步行时间：调用 maps_around_search(location='116.581734,35.410706', radius='500', keywords='公交站') 获取附近公交站列表；对每个公交站调用 maps_walking_by_coordinates(origin='116.581734,35.410706', destination=该公交站location)，取最小步行时长t_min；验证 t_min ≤ 8分钟。
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
    user_location: str = "116.569338,35.422161",
    search_radius: int = 2500,
    keywords: str = "博物馆",
    min_rating: float = 4.6,
    avoid_location_address: str = "济宁市任城区党史陈列馆",
    avoid_location_city: str = "济宁",
    min_distance_from_avoid: int = 800,  # meters
    station_address: str = "济宁站",
    station_city: str = "济宁",
    max_total_detour_time: int = 720,  # 12 minutes = 720 seconds
    max_detour_increase: int = 120,  # 2 minutes = 120 seconds
    bus_stop_search_radius: int = 500,
    bus_stop_keywords: str = "公交站",
    max_walking_to_bus: int = 480  # 8 minutes = 480 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近范围：调用 maps_around_search，验证返回pois中包含 target_poi_id。
    2) POI类型与评分：调用 maps_search_detail，验证 biz_ext.rating≥4.6。
    3) 不在其他地点附近：获取党史陈列馆坐标，验证直线距离≥800米。
    4) 绕行总行程时间上限：计算从济宁站到POI再到用户位置的总时间，验证≤12分钟。
    5) 绕行相对增量：计算绕行增加的时间，验证≤2分钟。
    6) 交通枢纽步行时间：搜索附近公交站，计算到最近公交站的步行时间，验证≤8分钟。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.569338,35.422161"
        search_radius: 搜索半径（米），默认2500
        keywords: 搜索关键词，默认"博物馆"
        min_rating: 最低评分，默认4.6
        avoid_location_address: 需要避开的地点地址，默认"济宁市任城区党史陈列馆"
        avoid_location_city: 需要避开的地点所在城市，默认"济宁"
        min_distance_from_avoid: 与需要避开的地点的最小距离（米），默认800
        station_address: 车站地址，默认"济宁站"
        station_city: 车站所在城市，默认"济宁"
        max_total_detour_time: 最大绕行总时间（秒），默认720（12分钟）
        max_detour_increase: 最大绕行增加时间（秒），默认120（2分钟）
        bus_stop_search_radius: 公交站搜索半径（米），默认500
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_walking_to_bus: 最大步行到公交站时间（秒），默认480（8分钟）

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

    # 步骤2: POI类型与评分
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

    # 步骤3: 不在其他地点附近
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

    distance_result = maps_distance(origins=poi_location, destination=avoid_location)
    if distance_result.error:
        print(f"❌ 计算距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到距离信息")
        return False

    distance_to_avoid = distance_result.results[0].distance_meters
    if distance_to_avoid < min_distance_from_avoid:
        print(f"❌ 与{avoid_location_address}的距离{distance_to_avoid}米，小于要求的{min_distance_from_avoid}米")
        return False
    print(f"✅ 与{avoid_location_address}的距离{distance_to_avoid}米，符合要求（>= {min_distance_from_avoid}米）")

    # 步骤4: 绕行总行程时间上限
    station_text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_search_result.error:
        print(f"❌ 获取车站坐标失败: {station_text_search_result.error}")
        return False

    if not station_text_search_result.pois or len(station_text_search_result.pois) == 0:
        print(f"❌ 未找到车站坐标")
        return False

    station_poi_id = station_text_search_result.pois[0].id
    station_detail_result = maps_search_detail(id=station_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取车站详情失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print(f"❌ 车站没有location信息")
        return False
    station_location = station_detail_result.location
    print(f"✅ 获取车站坐标: {station_location} ({station_address})")

    # 计算从车站到POI的驾车时间
    station_to_poi_result = maps_driving_by_coordinates(origin=station_location, destination=poi_location)
    if station_to_poi_result.error:
        print(f"❌ 计算从车站到POI驾车路线失败: {station_to_poi_result.error}")
        return False

    if station_to_poi_result.total_duration_seconds is None:
        print(f"❌ 无法获取从车站到POI驾车时长")
        return False

    t_station_to_poi = station_to_poi_result.total_duration_seconds
    print(f"✅ 从车站到POI驾车时长{t_station_to_poi}秒")

    # 计算从POI到用户位置的驾车时间
    poi_to_user_result = maps_driving_by_coordinates(origin=poi_location, destination=user_location)
    if poi_to_user_result.error:
        print(f"❌ 计算从POI到用户位置驾车路线失败: {poi_to_user_result.error}")
        return False

    if poi_to_user_result.total_duration_seconds is None:
        print(f"❌ 无法获取从POI到用户位置驾车时长")
        return False

    t_poi_to_user = poi_to_user_result.total_duration_seconds
    print(f"✅ 从POI到用户位置驾车时长{t_poi_to_user}秒")

    # 计算总绕行时间
    total_detour_time = t_station_to_poi + t_poi_to_user
    if total_detour_time > max_total_detour_time:
        print(f"❌ 绕行总时间{total_detour_time}秒（{total_detour_time / 60:.2f}分钟），超过{max_total_detour_time}秒（{max_total_detour_time // 60}分钟）")
        return False
    print(f"✅ 绕行总时间{total_detour_time}秒（{total_detour_time / 60:.2f}分钟），符合要求（<= {max_total_detour_time}秒，即{max_total_detour_time // 60}分钟）")

    # 步骤5: 绕行相对增量
    # 计算从车站直接到用户位置的驾车时间
    station_to_user_result = maps_driving_by_coordinates(origin=station_location, destination=user_location)
    if station_to_user_result.error:
        print(f"❌ 计算从车站到用户位置驾车路线失败: {station_to_user_result.error}")
        return False

    if station_to_user_result.total_duration_seconds is None:
        print(f"❌ 无法获取从车站到用户位置驾车时长")
        return False

    t_station_to_user = station_to_user_result.total_duration_seconds
    print(f"✅ 从车站直接到用户位置驾车时长{t_station_to_user}秒")

    # 计算绕行增加的时间
    detour_increase = total_detour_time - t_station_to_user
    if detour_increase > max_detour_increase:
        print(f"❌ 绕行增加时间{detour_increase}秒（{detour_increase / 60:.2f}分钟），超过{max_detour_increase}秒（{max_detour_increase // 60}分钟）")
        return False
    print(f"✅ 绕行增加时间{detour_increase}秒（{detour_increase / 60:.2f}分钟），符合要求（<= {max_detour_increase}秒，即{max_detour_increase // 60}分钟）")

    # 步骤6: 交通枢纽步行时间
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

    # 计算到每个公交站的步行时长，找到最小值
    min_walking_duration = None
    nearest_bus_stop_name = None
    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue
        walking_result = maps_walking_by_coordinates(origin=poi_location, destination=bus_stop.location)
        if walking_result.error or walking_result.total_duration_seconds is None:
            continue
        if min_walking_duration is None or walking_result.total_duration_seconds < min_walking_duration:
            min_walking_duration = walking_result.total_duration_seconds
            nearest_bus_stop_name = bus_stop.name

    if min_walking_duration is None:
        print(f"❌ 无法计算到公交站的步行时长")
        return False

    if min_walking_duration > max_walking_to_bus:
        print(f"❌ 到最近公交站({nearest_bus_stop_name})步行时长{min_walking_duration}秒（{min_walking_duration / 60:.2f}分钟），超过{max_walking_to_bus}秒（{max_walking_to_bus // 60}分钟）")
        return False
    print(f"✅ 到最近公交站({nearest_bus_stop_name})步行时长{min_walking_duration}秒（{min_walking_duration / 60:.2f}分钟），符合要求（<= {max_walking_to_bus}秒，即{max_walking_to_bus // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 856.py 文件...\\n")
    result = verify_poi(poi_id="B021905525")
    print(f"\n验证结果: {result}")
