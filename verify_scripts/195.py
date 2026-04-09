"""
修改任务指令：你想在附近5公里以内找一个加油站。加油站的评分要高于4.5分。加油站与宝鸡火车站直线距离需要超过500米。加油站附近500米内需要至少存在一个公交站，满足直线距离不超过200米，而且从加油站骑自行车到这个公交站不能超过6分钟。从你当前位置到加油站的开车路线的途径点中，至少需要存在一个途径点满足其附近300米有公园。你加完油后要去宝鸡南站，所以从你当前位置出发，先到加油站再到宝鸡南站，整个开车时间不能超过30分钟，而且这样绕一下相比直接去宝鸡南站，最多只能多花15分钟。你害羞且缺乏安全感，说话犹豫，不自信。
输入：B03950291Z
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用 maps_around_search('107.153206,34.365809', '加油站', 5000) 验证目标加油站ID B03950291Z 在结果列表中。
2. 调用 maps_search_detail('B03950291Z') 获取加油站评分，验证 rating > 4.5。
3. 调用 maps_text_search('宝鸡站', '宝鸡') 获取宝鸡站poi_id，再调用 maps_search_detail 获取其坐标。调用 maps_distance 计算加油站坐标('107.144683,34.356481')到宝鸡站坐标的距离，验证 > 500 米。
4. 调用 maps_around_search('107.144683,34.356481', '公交站', 500) 获取附近公交站列表。遍历公交站列表，验证是否存在某个公交站能满足要求：对每个公交站调用 maps_distance 计算与加油站的直线距离，找到距离 ≤ 200 米的公交站（如 BV10294578 '公交二公司(公交站)' 距离约141米）。对该公交站调用 maps_bicycling_by_coordinates 计算加油站到该公交站的骑行时间，验证 ≤ 360 秒（6分钟）。
5. 调用 maps_driving_by_coordinates('107.153206,34.365809', '107.144683,34.356481') 获取驾车路线步骤点。取第一个步骤点（坐标 '107.152309,34.359256'）。调用 maps_around_search('107.152309,34.359256', '公园', 300) 验证该点附近300米内有公园（如人民公园 B039500B70，距离约206米）。
6. 调用 maps_text_search('宝鸡南站', '宝鸡') 获取宝鸡南站poi_id，再调用 maps_search_detail 获取其坐标('107.232455,34.334906')。调用 maps_driving_by_coordinates('107.153206,34.365809', '107.144683,34.356481') 得到时间 t1，调用 maps_driving_by_coordinates('107.144683,34.356481', '107.232455,34.334906') 得到时间 t2，计算总时间 t_total = t1 + t2，验证 ≤ 1800 秒（30分钟）。
7. 调用 maps_driving_by_coordinates('107.153206,34.365809', '107.232455,34.334906') 得到直接时间 t_direct，验证 t_total - t_direct ≤ 900 秒（15分钟）。
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
    target_poi_id: str = 'B03950291Z',
    user_location: str = '107.153206,34.365809',
    search_keywords: str = '加油站',
    search_radius: str = '5000',
    min_rating: float = 4.5,
    train_station_keywords: str = '宝鸡站',
    train_station_city: str = '宝鸡',
    min_distance_to_train_station_meters: int = 500,
    bus_station_keywords: str = '公交站',
    bus_station_radius: str = '500',
    max_distance_to_bus_station_meters: int = 200,
    max_bicycling_seconds: int = 360,
    park_keywords: str = '公园',
    park_radius: str = '300',
    train_station_south_keywords: str = '宝鸡南站',
    max_total_driving_seconds: int = 1800,
    max_detour_seconds: int = 900
) -> bool:
    """
    验证POI是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID
        user_location: 用户位置坐标（写死）
        search_keywords: 搜索关键词
        search_radius: 搜索半径（米）
        min_rating: 最小评分
        train_station_keywords: 火车站搜索关键词
        train_station_city: 火车站搜索城市
        min_distance_to_train_station_meters: 到火车站的最小距离（米）
        bus_station_keywords: 公交站搜索关键词
        bus_station_radius: 公交站搜索半径（米）
        max_distance_to_bus_station_meters: 到公交站的最大距离（米）
        max_bicycling_seconds: 最大骑行时间（秒）
        park_keywords: 公园搜索关键词
        park_radius: 公园搜索半径（米）
        train_station_south_keywords: 宝鸡南站搜索关键词
        max_total_driving_seconds: 最大总驾车时间（秒）
        max_detour_seconds: 最大绕路时间（秒）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 检查目标加油站是否在周边搜索结果中
    print("验证步骤1: 检查目标加油站是否在周边搜索结果中...")
    around_result = maps_around_search(user_location, search_radius, search_keywords)
    if around_result.error:
        print(f"  验证失败: {around_result.error}")
        all_passed = False
    elif around_result.pois:
        poi_ids = [poi.id for poi in around_result.pois]
        if target_poi_id in poi_ids:
            print(f"  验证通过: 目标加油站 {target_poi_id} 在搜索结果中")
        else:
            print(f"  验证失败: 目标加油站 {target_poi_id} 不在搜索结果中")
            all_passed = False
    else:
        print("  验证失败: 搜索结果为空")
        all_passed = False
    
    # 验证步骤2: 获取加油站评分和坐标，验证 rating > 4.5
    print("验证步骤2: 验证评分 > 4.5...")
    detail_result = maps_search_detail(target_poi_id)
    if detail_result.error:
        print(f"  验证失败: {detail_result.error}")
        all_passed = False
        target_poi_location = None
    else:
        # 获取目标POI坐标，后续步骤需要用到
        target_poi_location = detail_result.location
        if not target_poi_location:
            print("  验证失败: 无法获取目标加油站坐标")
            all_passed = False
        else:
            # 检查评分
            rating = None
            if detail_result.biz_ext and isinstance(detail_result.biz_ext, dict):
                rating_str = detail_result.biz_ext.get('rating', '')
                if rating_str:
                    try:
                        rating = float(rating_str)
                    except (ValueError, TypeError):
                        pass
            
            if rating is not None:
                if rating > min_rating:
                    print(f"  验证通过: 评分 {rating} > {min_rating}")
                else:
                    print(f"  验证失败: 评分 {rating} <= {min_rating}")
                    all_passed = False
            else:
                print("  验证失败: 无法获取评分信息")
                all_passed = False
    
    # 验证步骤3: 验证到宝鸡站的距离 > 500 米
    print("验证步骤3: 验证到宝鸡站的距离 > 500 米...")
    if not target_poi_location:
        print("  验证失败: 目标加油站坐标未获取")
        all_passed = False
    else:
        train_station_search_result = maps_text_search(train_station_keywords, train_station_city)
        if train_station_search_result.error:
            print(f"  验证失败: 搜索宝鸡站失败 - {train_station_search_result.error}")
            all_passed = False
        elif not train_station_search_result.pois or len(train_station_search_result.pois) == 0:
            print("  验证失败: 未找到宝鸡站 POI")
            all_passed = False
        else:
            train_station_poi_id = train_station_search_result.pois[0].id
            train_station_detail = maps_search_detail(train_station_poi_id)
            if train_station_detail.error or not train_station_detail.location:
                print(f"  验证失败: 无法获取宝鸡站坐标 - {train_station_detail.error if train_station_detail.error else '坐标为空'}")
                all_passed = False
            else:
                train_station_location = train_station_detail.location
                distance_result = maps_distance(target_poi_location, train_station_location)
                if distance_result.error or not distance_result.results:
                    print(f"  验证失败: 计算距离失败 - {distance_result.error if distance_result.error else '结果为空'}")
                    all_passed = False
                else:
                    distance = distance_result.results[0].distance_meters
                    if distance > min_distance_to_train_station_meters:
                        print(f"  验证通过: 距离 {distance} 米 > {min_distance_to_train_station_meters} 米")
                    else:
                        print(f"  验证失败: 距离 {distance} 米 <= {min_distance_to_train_station_meters} 米")
                        all_passed = False
    
    # 验证步骤4: 验证附近有公交站，且至少有一个公交站满足距离 <= 200米且骑行时间 <= 360秒
    print("验证步骤4: 验证附近有公交站，且至少有一个公交站满足距离 <= 200米且骑行时间 <= 360秒...")
    if not target_poi_location:
        print("  验证失败: 目标加油站坐标未获取")
        all_passed = False
    else:
        bus_around_result = maps_around_search(target_poi_location, bus_station_radius, bus_station_keywords)
        if bus_around_result.error:
            print(f"  验证失败: 搜索公交站失败 - {bus_around_result.error}")
            all_passed = False
        elif not bus_around_result.pois or len(bus_around_result.pois) == 0:
            print("  验证失败: 未找到公交站")
            all_passed = False
        else:
            bus_stations = bus_around_result.pois
            found_valid_bus_station = False
            for bus_station in bus_stations:
                if not bus_station.location:
                    continue
                bus_station_location = bus_station.location
                # 计算直线距离
                distance_result = maps_distance(target_poi_location, bus_station_location)
                if distance_result.error or not distance_result.results:
                    continue
                distance = distance_result.results[0].distance_meters
                if distance <= max_distance_to_bus_station_meters:
                    # 计算骑行时间
                    bicycling_result = maps_bicycling_by_coordinates(target_poi_location, bus_station_location)
                    if not bicycling_result.error and bicycling_result.total_duration_seconds is not None:
                        bicycling_time = bicycling_result.total_duration_seconds
                        if bicycling_time <= max_bicycling_seconds:
                            found_valid_bus_station = True
                            print(f"  验证通过: 找到公交站 {bus_station.name} ({bus_station.id}) 满足条件（距离 {distance} 米 <= {max_distance_to_bus_station_meters} 米，骑行时间 {bicycling_time} 秒 <= {max_bicycling_seconds} 秒）")
                            break
            
            if not found_valid_bus_station:
                print("  验证失败: 未找到满足条件的公交站（距离 <= 200米且骑行时间 <= 360秒）")
                all_passed = False
    
    # 验证步骤5: 验证驾车路线第一个步骤点附近300米内有公园
    print("验证步骤5: 验证驾车路线第一个步骤点附近300米内有公园...")
    if not target_poi_location:
        print("  验证失败: 目标加油站坐标未获取")
        all_passed = False
    else:
        driving_result = maps_driving_by_coordinates(user_location, target_poi_location)
        if driving_result.error or not driving_result.steps or len(driving_result.steps) == 0:
            print(f"  验证失败: 获取驾车路线失败 - {driving_result.error if driving_result.error else 'steps为空'}")
            all_passed = False
        else:
            # 取第一个步骤点的 to_coordinates（第一个步骤的终点）
            first_step = driving_result.steps[0]
            first_waypoint = first_step.to_coordinates
            # 检查该点附近300米内是否有公园
            park_around_result = maps_around_search(first_waypoint, park_radius, park_keywords)
            if park_around_result.error:
                print(f"  验证失败: 搜索公园失败 - {park_around_result.error}")
                all_passed = False
            elif not park_around_result.pois or len(park_around_result.pois) == 0:
                print(f"  验证失败: 第一个步骤点 {first_waypoint} 附近300米内未找到公园")
                all_passed = False
            else:
                print(f"  验证通过: 第一个步骤点 {first_waypoint} 附近300米内找到公园")
    
    # 验证步骤6: 验证从用户位置到加油站再到宝鸡南站的总时间 <= 1800秒（30分钟）
    print("验证步骤6: 验证从用户位置到加油站再到宝鸡南站的总时间 <= 1800秒（30分钟）...")
    if not target_poi_location:
        print("  验证失败: 目标加油站坐标未获取")
        all_passed = False
    else:
        train_station_south_search = maps_text_search(train_station_south_keywords, train_station_city)
        if train_station_south_search.error or not train_station_south_search.pois or len(train_station_south_search.pois) == 0:
            print(f"  验证失败: 搜索宝鸡南站失败 - {train_station_south_search.error if train_station_south_search.error else '未找到宝鸡南站'}")
            all_passed = False
        else:
            train_station_south_poi_id = train_station_south_search.pois[0].id
            train_station_south_detail = maps_search_detail(train_station_south_poi_id)
            if train_station_south_detail.error or not train_station_south_detail.location:
                print(f"  验证失败: 获取宝鸡南站坐标失败 - {train_station_south_detail.error if train_station_south_detail.error else '坐标为空'}")
                all_passed = False
            else:
                train_station_south_location = train_station_south_detail.location
                # 计算用户位置到加油站的驾车时间 t1
                route1 = maps_driving_by_coordinates(user_location, target_poi_location)
                if route1.error or route1.total_duration_seconds is None:
                    print(f"  验证失败: 计算用户位置到加油站的驾车时间失败 - {route1.error if route1.error else '时间为空'}")
                    all_passed = False
                else:
                    t1 = route1.total_duration_seconds
                    # 计算加油站到宝鸡南站的驾车时间 t2
                    route2 = maps_driving_by_coordinates(target_poi_location, train_station_south_location)
                    if route2.error or route2.total_duration_seconds is None:
                        print(f"  验证失败: 计算加油站到宝鸡南站的驾车时间失败 - {route2.error if route2.error else '时间为空'}")
                        all_passed = False
                    else:
                        t2 = route2.total_duration_seconds
                        total_time = t1 + t2
                        if total_time <= max_total_driving_seconds:
                            print(f"  验证通过: 总时间 {total_time} 秒 <= {max_total_driving_seconds} 秒 (t1={t1}秒, t2={t2}秒)")
                        else:
                            print(f"  验证失败: 总时间 {total_time} 秒 > {max_total_driving_seconds} 秒 (t1={t1}秒, t2={t2}秒)")
                            all_passed = False
    
    # 验证步骤7: 验证绕道加油站比直接去宝鸡南站多花的时间 <= 900秒（15分钟）
    print("验证步骤7: 验证绕道加油站比直接去宝鸡南站多花的时间 <= 900秒（15分钟）...")
    if not target_poi_location:
        print("  验证失败: 目标加油站坐标未获取")
        all_passed = False
    else:
        train_station_south_search = maps_text_search(train_station_south_keywords, train_station_city)
        if train_station_south_search.error or not train_station_south_search.pois or len(train_station_south_search.pois) == 0:
            print(f"  验证失败: 搜索宝鸡南站失败 - {train_station_south_search.error if train_station_south_search.error else '未找到宝鸡南站'}")
            all_passed = False
        else:
            train_station_south_poi_id = train_station_south_search.pois[0].id
            train_station_south_detail = maps_search_detail(train_station_south_poi_id)
            if train_station_south_detail.error or not train_station_south_detail.location:
                print(f"  验证失败: 获取宝鸡南站坐标失败 - {train_station_south_detail.error if train_station_south_detail.error else '坐标为空'}")
                all_passed = False
            else:
                train_station_south_location = train_station_south_detail.location
                # 需要先获取 t1 和 t2（从步骤6）
                route1 = maps_driving_by_coordinates(user_location, target_poi_location)
                if route1.error or route1.total_duration_seconds is None:
                    print(f"  验证失败: 计算用户位置到加油站的驾车时间失败 - {route1.error if route1.error else '时间为空'}")
                    all_passed = False
                else:
                    t1 = route1.total_duration_seconds
                    route2 = maps_driving_by_coordinates(target_poi_location, train_station_south_location)
                    if route2.error or route2.total_duration_seconds is None:
                        print(f"  验证失败: 计算加油站到宝鸡南站的驾车时间失败 - {route2.error if route2.error else '时间为空'}")
                        all_passed = False
                    else:
                        t2 = route2.total_duration_seconds
                        # 计算直接到宝鸡南站的时间 t_direct
                        route_direct = maps_driving_by_coordinates(user_location, train_station_south_location)
                        if route_direct.error or route_direct.total_duration_seconds is None:
                            print(f"  验证失败: 计算用户位置直接到宝鸡南站的驾车时间失败 - {route_direct.error if route_direct.error else '时间为空'}")
                            all_passed = False
                        else:
                            t_direct = route_direct.total_duration_seconds
                            detour_time = (t1 + t2) - t_direct
                            if detour_time <= max_detour_seconds:
                                print(f"  验证通过: 绕路时间 {detour_time} 秒 <= {max_detour_seconds} 秒 (t1={t1}秒, t2={t2}秒, t_direct={t_direct}秒)")
                            else:
                                print(f"  验证失败: 绕路时间 {detour_time} 秒 > {max_detour_seconds} 秒 (t1={t1}秒, t2={t2}秒, t_direct={t_direct}秒)")
                                all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
