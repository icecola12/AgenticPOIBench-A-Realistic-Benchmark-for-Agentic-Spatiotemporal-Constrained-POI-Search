
"""
修改任务指令:你想在附近800米以内找一家评分高于4.0的酒吧。这家酒吧不能离金澜酒店太近，直线距离至少600米以外。你打算步行过去，希望路上能经过一个离万达广场不超过2000米的地方，而且从酒吧回来的路上附近300米内得有超市。之后你要从酒吧打车去大庆西站，全程时间不能超过20分钟，绕道去酒吧相比直接去西站最多只能多花10分钟。另外，酒吧到公交站的步行时间要在15分钟以内。你逻辑性强但没有耐心，希望高效沟通，讨厌废话。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('124.887084,46.62794', '酒吧', 800)验证目标酒吧在搜索范围内。
2. 调用maps_search_detail('B0L1ZSMRP3')获取评分，验证≥4.0。
3. 调用maps_text_search('金澜酒店', '大庆')获取金澜酒店poi_id，再调用maps_search_detail获取坐标，调用maps_distance('124.883608,46.631808', '124.887062,46.624222')验证距离≥600米。
4. 调用maps_walking_by_coordinates('124.887084,46.62794', '124.883608,46.631808')获取步行路线，提取所有包括起点终点的途经点坐标(例如124.888583,46.631041)，调用maps_text_search('万达广场让胡路', '大庆')获取万达广场poi_id，再逐个途径点调用maps_search_detail获取坐标，调用maps_distance('124.888583,46.631041', '124.867763,46.624814')验证存在poi返回的距离<2000米。
5. 调用maps_walking_by_coordinates('124.883608,46.631808', '124.887084,46.62794')获取步行路线，提取所有包括起点终点的途经点坐标(124.888583,46.631041)，逐个调用maps_around_search('124.888583,46.631041', '超市', 300)验证存在poi点返回的数量>0，代表附近有超市。
6. 调用maps_walking_by_coordinates('124.887084,46.62794', '124.883608,46.631808')获取步行时间t_walk，调用maps_driving_by_coordinates('124.883608,46.631808', '124.885743,46.656631')获取驾车时间t_drive，验证(t_walk + t_drive) ≤ 20分钟。
7. 调用maps_driving_by_coordinates('124.887084,46.62794', '124.885743,46.656631')获取直接驾车时间t_direct，验证(t_walk + t_drive - t_direct) ≤ 10分钟。
8. 调用maps_around_search('124.883608,46.631808', '公交站', 500)获取最近公交站poi_id(BV10427840)，调用maps_walking_by_coordinates('124.883608,46.631808', '124.885628,46.630196')获取步行时间，验证≤15分钟。
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
    maps_distance,
    maps_walking_by_coordinates,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "124.887084,46.62794",
    search_radius: int = 800,
    keywords: str = "酒吧",
    min_rating: float = 4.0,
    hotel_name: str = "金澜酒店",
    hotel_city: str = "大庆",
    min_hotel_distance: int = 600,
    mall_name: str = "万达广场让胡路",
    mall_city: str = "大庆",
    max_mall_distance: int = 2000,
    supermarket_keywords: str = "超市",
    supermarket_radius: int = 300,
    station_name: str = "大庆西站",
    station_city: str = "大庆",
    max_total_duration: int = 1200,  # 20 minutes = 1200 seconds
    max_detour_duration: int = 600,  # 10 minutes = 600 seconds
    bus_stop_keywords: str = "公交站",
    bus_stop_radius: int = 500,
    max_bus_stop_walking_duration: int = 900  # 15 minutes = 900 seconds
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 距离约束（附近800米）：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 评分约束：调用 maps_search_detail 获取评分，验证≥4.0。
    3) 与金澜酒店距离约束：调用 maps_text_search 获取酒店坐标，验证距离≥600米。
    4) 步行路线经过万达广场附近：验证步行路线上存在距离万达广场<2000米的途经点。
    5) 返回路线附近有超市：验证返回路线上存在途经点附近300米内有超市。
    6) 总时长约束：验证步行到酒吧+驾车到西站的总时长≤20分钟。
    7) 绕道时间约束：验证绕道时间≤10分钟。
    8) 公交站步行时间约束：验证酒吧到最近公交站的步行时间≤15分钟。
    
    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"124.887084,46.62794"
        search_radius: 搜索半径（米），默认800
        keywords: 搜索关键词，默认"酒吧"
        min_rating: 最低评分，默认4.0
        hotel_name: 酒店名称，默认"金澜酒店"
        hotel_city: 酒店所在城市，默认"大庆"
        min_hotel_distance: 与酒店的最小距离（米），默认600
        mall_name: 商场名称，默认"万达广场让胡路"
        mall_city: 商场所在城市，默认"大庆"
        max_mall_distance: 与商场的最大距离（米），默认2000
        supermarket_keywords: 超市搜索关键词，默认"超市"
        supermarket_radius: 超市搜索半径（米），默认300
        station_name: 车站名称，默认"大庆西站"
        station_city: 车站所在城市，默认"大庆"
        max_total_duration: 最大总时长（秒），默认1200（20分钟）
        max_detour_duration: 最大绕道时长（秒），默认600（10分钟）
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        bus_stop_radius: 公交站搜索半径（米），默认500
        max_bus_stop_walking_duration: 到公交站的最大步行时长（秒），默认900（15分钟）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（附近800米）
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
    
    # 步骤2: 获取目标POI详情并验证评分
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
                print(f"❌ POI评分{rating}，低于要求的{min_rating}")
                return False
            print(f"✅ POI评分{rating}，符合要求（>= {min_rating}）")
        except (ValueError, TypeError):
            print(f"❌ 无法解析POI评分")
            return False
    else:
        print(f"❌ POI没有评分信息")
        return False
    
    # 步骤3: 与金澜酒店距离约束
    hotel_search_result = maps_text_search(keywords=hotel_name, city=hotel_city)
    if hotel_search_result.error:
        print(f"❌ 搜索酒店失败: {hotel_search_result.error}")
        return False
    
    if not hotel_search_result.pois or len(hotel_search_result.pois) == 0:
        print(f"❌ 未找到酒店: {hotel_name}")
        return False
    
    hotel_poi_id = hotel_search_result.pois[0].id
    print(f"✅ 找到酒店: {hotel_search_result.pois[0].name} (ID: {hotel_poi_id})")
    
    hotel_detail = maps_search_detail(id=hotel_poi_id)
    if hotel_detail.error:
        print(f"❌ 获取酒店详情失败: {hotel_detail.error}")
        return False
    
    if not hotel_detail.location:
        print(f"❌ 酒店没有location信息")
        return False
    
    hotel_location = hotel_detail.location
    print(f"✅ 获取酒店坐标: {hotel_location}")
    
    distance_result = maps_distance(origins=poi_location, destination=hotel_location)
    if distance_result.error:
        print(f"❌ 计算距离失败: {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未获取到距离信息")
        return False
    
    hotel_distance = distance_result.results[0].distance_meters
    if hotel_distance < min_hotel_distance:
        print(f"❌ 与酒店距离{hotel_distance}米，小于要求的{min_hotel_distance}米")
        return False
    print(f"✅ 与酒店距离{hotel_distance}米，符合要求（>= {min_hotel_distance}米）")

    # 步骤4: 步行路线经过万达广场附近
    # 获取从用户位置到酒吧的步行路线
    walking_to_bar_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_to_bar_result.error:
        print(f"❌ 计算步行路线失败: {walking_to_bar_result.error}")
        return False

    if walking_to_bar_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    t_walk = walking_to_bar_result.total_duration_seconds
    print(f"✅ 从用户位置到酒吧步行时长{t_walk}秒（{t_walk / 60:.2f}分钟）")

    # 搜索万达广场
    mall_search_result = maps_text_search(keywords=mall_name, city=mall_city)
    if mall_search_result.error:
        print(f"❌ 搜索商场失败: {mall_search_result.error}")
        return False

    if not mall_search_result.pois or len(mall_search_result.pois) == 0:
        print(f"❌ 未找到商场: {mall_name}")
        return False

    mall_poi_id = mall_search_result.pois[0].id
    print(f"✅ 找到商场: {mall_search_result.pois[0].name} (ID: {mall_poi_id})")

    mall_detail = maps_search_detail(id=mall_poi_id)
    if mall_detail.error:
        print(f"❌ 获取商场详情失败: {mall_detail.error}")
        return False

    if not mall_detail.location:
        print(f"❌ 商场没有location信息")
        return False

    mall_location = mall_detail.location
    print(f"✅ 获取商场坐标: {mall_location}")

    # 提取步行路线的所有途经点
    waypoints_to_bar = []
    if walking_to_bar_result.steps:
        for step in walking_to_bar_result.steps:
            if step.from_coordinates:
                waypoints_to_bar.append(step.from_coordinates)
            if step.to_coordinates:
                waypoints_to_bar.append(step.to_coordinates)

    # 去重
    waypoints_to_bar = list(set(waypoints_to_bar))
    print(f"✅ 提取到{len(waypoints_to_bar)}个途经点")

    # 检查是否有途经点距离商场<2000米
    has_close_waypoint = False
    for waypoint in waypoints_to_bar:
        dist_result = maps_distance(origins=waypoint, destination=mall_location)
        if not dist_result.error and dist_result.results and len(dist_result.results) > 0:
            dist = dist_result.results[0].distance_meters
            if dist < max_mall_distance:
                has_close_waypoint = True
                print(f"✅ 找到距离商场{dist}米的途经点，符合要求（< {max_mall_distance}米）")
                break

    if not has_close_waypoint:
        print(f"❌ 步行路线中没有距离商场小于{max_mall_distance}米的途经点")
        return False

    # 步骤5: 返回路线附近有超市
    # 获取从酒吧返回用户位置的步行路线
    walking_from_bar_result = maps_walking_by_coordinates(origin=poi_location, destination=user_location)
    if walking_from_bar_result.error:
        print(f"❌ 计算返回步行路线失败: {walking_from_bar_result.error}")
        return False

    # 提取返回路线的所有途经点
    waypoints_from_bar = []
    if walking_from_bar_result.steps:
        for step in walking_from_bar_result.steps:
            if step.from_coordinates:
                waypoints_from_bar.append(step.from_coordinates)
            if step.to_coordinates:
                waypoints_from_bar.append(step.to_coordinates)

    # 去重
    waypoints_from_bar = list(set(waypoints_from_bar))
    print(f"✅ 提取到返回路线{len(waypoints_from_bar)}个途经点")

    # 检查是否有途经点附近有超市
    has_supermarket_nearby = False
    for waypoint in waypoints_from_bar:
        supermarket_result = maps_around_search(
            location=waypoint,
            radius=str(supermarket_radius),
            keywords=supermarket_keywords
        )
        if not supermarket_result.error and supermarket_result.pois and len(supermarket_result.pois) > 0:
            has_supermarket_nearby = True
            print(f"✅ 找到途经点附近{supermarket_radius}米内有{len(supermarket_result.pois)}个超市")
            break

    if not has_supermarket_nearby:
        print(f"❌ 返回路线中没有途经点附近{supermarket_radius}米内有超市")
        return False

    # 步骤6: 总时长约束（步行到酒吧+驾车到西站≤20分钟）
    # 查询车站坐标
    station_search_result = maps_text_search(keywords=station_name, city=station_city)
    if station_search_result.error:
        print(f"❌ 搜索车站失败: {station_search_result.error}")
        return False

    if not station_search_result.pois or len(station_search_result.pois) == 0:
        print(f"❌ 未找到车站: {station_name}")
        return False

    station_poi_id = station_search_result.pois[0].id
    print(f"✅ 找到车站: {station_search_result.pois[0].name} (ID: {station_poi_id})")

    station_detail = maps_search_detail(id=station_poi_id)
    if station_detail.error:
        print(f"❌ 获取车站详情失败: {station_detail.error}")
        return False

    if not station_detail.location:
        print(f"❌ 车站没有location信息")
        return False

    station_location = station_detail.location
    print(f"✅ 获取车站坐标: {station_location}")

    # 获取从酒吧驾车到车站的时间
    driving_to_station_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_to_station_result.error:
        print(f"❌ 计算驾车路线失败: {driving_to_station_result.error}")
        return False

    if driving_to_station_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    t_drive = driving_to_station_result.total_duration_seconds
    print(f"✅ 从酒吧驾车到车站时长{t_drive}秒（{t_drive / 60:.2f}分钟）")

    total_duration = t_walk + t_drive
    if total_duration > max_total_duration:
        print(f"❌ 总时长{total_duration}秒（{total_duration / 60:.2f}分钟），超过{max_total_duration}秒（{max_total_duration // 60}分钟）")
        return False
    print(f"✅ 总时长{total_duration}秒（{total_duration / 60:.2f}分钟），符合要求（<= {max_total_duration}秒，即{max_total_duration // 60}分钟）")

    # 步骤7: 绕道时间约束（≤10分钟）
    # 获取从用户位置直接驾车到车站的时间
    direct_driving_result = maps_driving_by_coordinates(origin=user_location, destination=station_location)
    if direct_driving_result.error:
        print(f"❌ 计算直接驾车路线失败: {direct_driving_result.error}")
        return False

    if direct_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取直接驾车时长")
        return False

    t_direct = direct_driving_result.total_duration_seconds
    print(f"✅ 从用户位置直接驾车到车站时长{t_direct}秒（{t_direct / 60:.2f}分钟）")

    detour_duration = total_duration - t_direct
    if detour_duration > max_detour_duration:
        print(f"❌ 绕道时间{detour_duration}秒（{detour_duration / 60:.2f}分钟），超过{max_detour_duration}秒（{max_detour_duration // 60}分钟）")
        return False
    print(f"✅ 绕道时间{detour_duration}秒（{detour_duration / 60:.2f}分钟），符合要求（<= {max_detour_duration}秒，即{max_detour_duration // 60}分钟）")

    # 步骤8: 公交站步行时间约束（≤15分钟）
    # 搜索酒吧附近的公交站
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到公交站")
        return False

    # 获取最近的公交站
    nearest_bus_stop = bus_stop_search_result.pois[0]
    print(f"✅ 找到最近公交站: {nearest_bus_stop.name} (ID: {nearest_bus_stop.id})")

    # 获取公交站详情以获取坐标
    bus_stop_detail = maps_search_detail(id=nearest_bus_stop.id)
    if bus_stop_detail.error:
        print(f"❌ 获取公交站详情失败: {bus_stop_detail.error}")
        return False

    if not bus_stop_detail.location:
        print(f"❌ 公交站没有location信息")
        return False

    bus_stop_location = bus_stop_detail.location
    print(f"✅ 获取公交站坐标: {bus_stop_location}")

    # 计算从酒吧到公交站的步行时间
    walking_to_bus_stop_result = maps_walking_by_coordinates(origin=poi_location, destination=bus_stop_location)
    if walking_to_bus_stop_result.error:
        print(f"❌ 计算到公交站步行路线失败: {walking_to_bus_stop_result.error}")
        return False

    if walking_to_bus_stop_result.total_duration_seconds is None:
        print(f"❌ 无法获取到公交站步行时长")
        return False

    bus_stop_walking_duration = walking_to_bus_stop_result.total_duration_seconds
    if bus_stop_walking_duration > max_bus_stop_walking_duration:
        print(f"❌ 到公交站步行时长{bus_stop_walking_duration}秒（{bus_stop_walking_duration / 60:.2f}分钟），超过{max_bus_stop_walking_duration}秒（{max_bus_stop_walking_duration // 60}分钟）")
        return False
    print(f"✅ 到公交站步行时长{bus_stop_walking_duration}秒（{bus_stop_walking_duration / 60:.2f}分钟），符合要求（<= {max_bus_stop_walking_duration}秒，即{max_bus_stop_walking_duration // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    print("开始验证 895.py 文件...\n")
    result = verify_poi(poi_id="B0L1ZSMRP3")
    print(f"\n验证结果: {result}")

