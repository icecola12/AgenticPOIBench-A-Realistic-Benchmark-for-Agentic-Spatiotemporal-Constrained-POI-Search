"""
修改任务指令：你想在附近1500米以内找一家洗衣店。这家洗衣店距离西昌站的直线距离要大于500米。你打算步行过去，希望步行路线上存在一个途径点满足离五鑫超市的直线距离小于200米，并且那个地方到围坐融合餐厅的直线距离小于100米。你骑自行车去洗衣店的距离不能超过2000米。另外，从洗衣店骑自行车到西昌汽车旅游客运中心的时间不能超过10分钟。你计划从家先去洗衣店，然后去汽车站，整个行程的时间不要超过30分钟，而且这样绕路去洗衣店比直接去汽车站多花的时间不要超过15分钟。你思路混乱，可能会混淆信息，让对话难以跟进。
输入：B034202TUX
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用 maps_around_search('102.250857,27.884912', '洗衣店', 1500) 确认目标洗衣店在1500米范围内。
2. 调用 maps_search_detail('B034202TUX') 获取洗衣店坐标(102.252853,27.882520)。
3. 调用 maps_distance('102.252853,27.882520', '102.224060,27.877396') 验证洗衣店到西昌站的直线距离 > 500米。
4. 调用 maps_walking_by_coordinates('102.250857,27.884912', '102.252853,27.882520') 获取步行路线，提取步骤2的终点坐标(102.252482,27.882641)作为途经点。
5. 调用 maps_distance('102.252482,27.882641', '102.251825,27.884162') 验证途经点到五鑫超市的直线距离 < 200米。
6. 调用 maps_distance('102.252482,27.882641', '102.252374,27.882638') 验证途经点到围坐融合餐厅的直线距离 < 100米。
7. 调用 maps_bicycling_by_coordinates('102.250857,27.884912', '102.252853,27.882520') 验证骑行距离 ≤ 2000米。
8. 调用 maps_bicycling_by_coordinates('102.252853,27.882520', '102.260590,27.868199') 验证骑行时间 ≤ 600秒（10分钟）。
9. 调用 maps_walking_by_coordinates('102.250857,27.884912', '102.252853,27.882520') 获取步行时间 t_walk。
10. 调用 maps_bicycling_by_coordinates('102.252853,27.882520', '102.260590,27.868199') 获取骑行时间 t_bike。
11. 计算总时间 t_total = t_walk + t_bike，验证 t_total ≤ 1800秒（30分钟）。
12. 调用 maps_bicycling_by_coordinates('102.250857,27.884912', '102.260590,27.868199') 获取直接骑行时间 t_direct，验证 t_total - t_direct ≤ 900秒（15分钟）。
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
    maps_around_search,
    maps_text_search,
    maps_bicycling_by_coordinates
)

"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(
    target_poi_id: str = 'B034202TUX',
    user_location: str = '102.250857,27.884912',
    laundry_keywords: str = '洗衣店',
    laundry_radius: str = '1500',
    train_station_keywords: str = '西昌站',
    train_station_city: str = '西昌',
    min_distance_to_train_station: int = 500,
    supermarket_keywords: str = '五鑫超市',
    supermarket_city: str = '西昌',
    max_distance_to_supermarket: int = 200,
    restaurant_keywords: str = '围坐融合餐厅',
    restaurant_city: str = '西昌',
    max_distance_to_restaurant: int = 100,
    max_bicycling_distance_meters: int = 2000,
    bus_station_keywords: str = '西昌汽车旅游客运中心',
    bus_station_city: str = '西昌',
    max_bicycling_time_seconds: int = 600,
    max_total_time_seconds: int = 1800,
    max_detour_time_seconds: int = 900
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID，默认值为 'B034202TUX'
        user_location: 用户位置坐标，默认值为 '102.250857,27.884912'
        其他参数为验证步骤中需要的参数，使用验证步骤中的值作为默认值
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 调用maps_around_search确认目标洗衣店在1500米范围内
    print("验证步骤1: 检查目标洗衣店在用户位置1500米范围内")
    around_result = maps_around_search(user_location, laundry_radius, laundry_keywords)
    if around_result.error:
        print(f"  验证失败: {around_result.error}")
        return False
    
    target_found = False
    if around_result.pois:
        for poi in around_result.pois:
            if poi.id == target_poi_id:
                target_found = True
                break
    
    if not target_found:
        print("  验证失败: 目标洗衣店不在搜索结果中")
        all_passed = False
    else:
        print("  验证通过: 目标洗衣店在搜索结果中")
    
    # 验证步骤2: 调用maps_search_detail获取洗衣店坐标
    print("验证步骤2: 获取洗衣店坐标")
    laundry_detail = maps_search_detail(target_poi_id)
    if laundry_detail.error or not laundry_detail.location:
        print(f"  验证失败: 无法获取洗衣店坐标 - {laundry_detail.error if laundry_detail.error else '坐标为空'}")
        return False
    
    laundry_location = laundry_detail.location
    print(f"  验证通过: 洗衣店坐标 {laundry_location}")
    
    # 验证步骤3: 验证洗衣店到西昌站的直线距离 > 500米
    print("验证步骤3: 验证洗衣店距离西昌站大于500米")
    train_station_search = maps_text_search(train_station_keywords, train_station_city)
    if train_station_search.error or not train_station_search.pois:
        print(f"  验证失败: 无法搜索到西昌站 - {train_station_search.error if train_station_search.error else '未找到结果'}")
        all_passed = False
    else:
        train_station_poi_id = train_station_search.pois[0].id
        train_station_detail = maps_search_detail(train_station_poi_id)
        if train_station_detail.error or not train_station_detail.location:
            print(f"  验证失败: 无法获取西昌站坐标 - {train_station_detail.error if train_station_detail.error else '坐标为空'}")
            all_passed = False
        else:
            train_station_location = train_station_detail.location
            distance_result = maps_distance(laundry_location, train_station_location)
            if distance_result.error or not distance_result.results:
                print(f"  验证失败: 无法计算距离 - {distance_result.error if distance_result.error else '未找到结果'}")
                all_passed = False
            else:
                distance = distance_result.results[0].distance_meters
                if distance > min_distance_to_train_station:
                    print(f"  验证通过: 洗衣店距离西昌站 {distance} 米，大于 {min_distance_to_train_station} 米")
                else:
                    print(f"  验证失败: 洗衣店距离西昌站 {distance} 米，不大于 {min_distance_to_train_station} 米")
                    all_passed = False
    
    # 验证步骤4: 调用maps_walking_by_coordinates获取步行路线，提取步骤2的终点坐标作为途经点
    print("验证步骤4: 获取步行路线途经点")
    walking_route = maps_walking_by_coordinates(user_location, laundry_location)
    if walking_route.error or not walking_route.steps:
        print(f"  验证失败: 无法获取步行路线 - {walking_route.error if walking_route.error else '路线为空'}")
        all_passed = False
        waypoint = None
    else:
        # 提取步骤2的终点坐标（索引为1，因为索引从0开始）
        if len(walking_route.steps) > 1:
            waypoint = walking_route.steps[1].to_coordinates
            print(f"  验证通过: 获取途经点坐标 {waypoint}")
        else:
            print("  验证失败: 步行路线步骤不足，无法提取步骤2的终点坐标")
            all_passed = False
            waypoint = None
    
    # 验证步骤5: 验证途经点到五鑫超市的直线距离 < 200米
    if waypoint:
        print("验证步骤5: 验证途经点到五鑫超市的直线距离小于200米")
        supermarket_search = maps_text_search(supermarket_keywords, supermarket_city)
        if supermarket_search.error or not supermarket_search.pois:
            print(f"  验证失败: 无法搜索到五鑫超市 - {supermarket_search.error if supermarket_search.error else '未找到结果'}")
            all_passed = False
        else:
            supermarket_poi_id = supermarket_search.pois[0].id
            supermarket_detail = maps_search_detail(supermarket_poi_id)
            if supermarket_detail.error or not supermarket_detail.location:
                print(f"  验证失败: 无法获取五鑫超市坐标 - {supermarket_detail.error if supermarket_detail.error else '坐标为空'}")
                all_passed = False
            else:
                supermarket_location = supermarket_detail.location
                waypoint_distance_result = maps_distance(waypoint, supermarket_location)
                if waypoint_distance_result.error or not waypoint_distance_result.results:
                    print(f"  验证失败: 无法计算距离 - {waypoint_distance_result.error if waypoint_distance_result.error else '未找到结果'}")
                    all_passed = False
                else:
                    waypoint_distance = waypoint_distance_result.results[0].distance_meters
                    if waypoint_distance < max_distance_to_supermarket:
                        print(f"  验证通过: 途经点到五鑫超市距离 {waypoint_distance} 米，小于 {max_distance_to_supermarket} 米")
                    else:
                        print(f"  验证失败: 途经点到五鑫超市距离 {waypoint_distance} 米，不小于 {max_distance_to_supermarket} 米")
                        all_passed = False
        
        # 验证步骤6: 验证途经点到围坐融合餐厅的直线距离 < 100米
        print("验证步骤6: 验证途经点到围坐融合餐厅的直线距离小于100米")
        restaurant_search = maps_text_search(restaurant_keywords, restaurant_city)
        if restaurant_search.error or not restaurant_search.pois:
            print(f"  验证失败: 无法搜索到围坐融合餐厅 - {restaurant_search.error if restaurant_search.error else '未找到结果'}")
            all_passed = False
        else:
            restaurant_poi_id = restaurant_search.pois[0].id
            restaurant_detail = maps_search_detail(restaurant_poi_id)
            if restaurant_detail.error or not restaurant_detail.location:
                print(f"  验证失败: 无法获取围坐融合餐厅坐标 - {restaurant_detail.error if restaurant_detail.error else '坐标为空'}")
                all_passed = False
            else:
                restaurant_location = restaurant_detail.location
                waypoint_distance_result2 = maps_distance(waypoint, restaurant_location)
                if waypoint_distance_result2.error or not waypoint_distance_result2.results:
                    print(f"  验证失败: 无法计算距离 - {waypoint_distance_result2.error if waypoint_distance_result2.error else '未找到结果'}")
                    all_passed = False
                else:
                    waypoint_distance2 = waypoint_distance_result2.results[0].distance_meters
                    if waypoint_distance2 < max_distance_to_restaurant:
                        print(f"  验证通过: 途经点到围坐融合餐厅距离 {waypoint_distance2} 米，小于 {max_distance_to_restaurant} 米")
                    else:
                        print(f"  验证失败: 途经点到围坐融合餐厅距离 {waypoint_distance2} 米，不小于 {max_distance_to_restaurant} 米")
                        all_passed = False
    
    # 验证步骤7: 验证骑行距离 ≤ 2000米
    print("验证步骤7: 验证从用户位置到洗衣店的骑行距离不超过2000米")
    bicycling_route1 = maps_bicycling_by_coordinates(user_location, laundry_location)
    if bicycling_route1.error:
        print(f"  验证失败: 无法获取骑行路线 - {bicycling_route1.error}")
        all_passed = False
    else:
        bicycling_distance = bicycling_route1.total_distance_meters if bicycling_route1.total_distance_meters else 0
        if bicycling_distance <= max_bicycling_distance_meters:
            print(f"  验证通过: 骑行距离 {bicycling_distance} 米，不超过 {max_bicycling_distance_meters} 米")
        else:
            print(f"  验证失败: 骑行距离 {bicycling_distance} 米，超过 {max_bicycling_distance_meters} 米")
            all_passed = False
    
    # 验证步骤8: 验证从洗衣店到西昌汽车旅游客运中心的骑行时间 ≤ 600秒
    print("验证步骤8: 验证从洗衣店到西昌汽车旅游客运中心的骑行时间不超过600秒")
    bus_station_search = maps_text_search(bus_station_keywords, bus_station_city)
    if bus_station_search.error or not bus_station_search.pois:
        print(f"  验证失败: 无法搜索到西昌汽车旅游客运中心 - {bus_station_search.error if bus_station_search.error else '未找到结果'}")
        all_passed = False
        bus_station_location = None
    else:
        bus_station_poi_id = bus_station_search.pois[0].id
        bus_station_detail = maps_search_detail(bus_station_poi_id)
        if bus_station_detail.error or not bus_station_detail.location:
            print(f"  验证失败: 无法获取西昌汽车旅游客运中心坐标 - {bus_station_detail.error if bus_station_detail.error else '坐标为空'}")
            all_passed = False
            bus_station_location = None
        else:
            bus_station_location = bus_station_detail.location
            print(f"  获取西昌汽车旅游客运中心坐标: {bus_station_location}")
    
    if bus_station_location:
        bicycling_route2 = maps_bicycling_by_coordinates(laundry_location, bus_station_location)
        if bicycling_route2.error:
            print(f"  验证失败: 无法获取骑行路线时间 - {bicycling_route2.error}")
            all_passed = False
        else:
            bicycling_time = bicycling_route2.total_duration_seconds if bicycling_route2.total_duration_seconds else 0
            if bicycling_time <= max_bicycling_time_seconds:
                print(f"  验证通过: 骑行时间 {bicycling_time} 秒，不超过 {max_bicycling_time_seconds} 秒")
            else:
                print(f"  验证失败: 骑行时间 {bicycling_time} 秒，超过 {max_bicycling_time_seconds} 秒")
                all_passed = False
    
    # 验证步骤9: 获取从用户位置到洗衣店的步行时间 t_walk
    print("验证步骤9: 获取从用户位置到洗衣店的步行时间")
    walk_route = maps_walking_by_coordinates(user_location, laundry_location)
    if walk_route.error:
        print(f"  验证失败: 无法获取步行路线时间 - {walk_route.error}")
        all_passed = False
        t_walk = None
    else:
        t_walk = walk_route.total_duration_seconds if walk_route.total_duration_seconds else 0
        print(f"  获取步行时间: {t_walk} 秒")
    
    # 验证步骤10: 获取从洗衣店到西昌汽车旅游客运中心的骑行时间 t_bike
    if bus_station_location:
        print("验证步骤10: 获取从洗衣店到西昌汽车旅游客运中心的骑行时间")
        bike_route = maps_bicycling_by_coordinates(laundry_location, bus_station_location)
        if bike_route.error:
            print(f"  验证失败: 无法获取骑行路线时间 - {bike_route.error}")
            all_passed = False
            t_bike = None
        else:
            t_bike = bike_route.total_duration_seconds if bike_route.total_duration_seconds else 0
            print(f"  获取骑行时间: {t_bike} 秒")
        
        # 验证步骤11: 验证总时间 t_total = t_walk + t_bike ≤ 1800秒
        if t_walk is not None and t_bike is not None:
            print("验证步骤11: 验证总时间不超过1800秒")
            t_total = t_walk + t_bike
            if t_total <= max_total_time_seconds:
                print(f"  验证通过: 总时间 {t_total} 秒，不超过 {max_total_time_seconds} 秒")
            else:
                print(f"  验证失败: 总时间 {t_total} 秒，超过 {max_total_time_seconds} 秒")
                all_passed = False
            
            # 验证步骤12: 验证绕行增加时间 ≤ 900秒
            print("验证步骤12: 验证绕行增加时间不超过900秒")
            direct_bike_route = maps_bicycling_by_coordinates(user_location, bus_station_location)
            if direct_bike_route.error:
                print(f"  验证失败: 无法获取直接骑行路线时间 - {direct_bike_route.error}")
                all_passed = False
            else:
                t_direct = direct_bike_route.total_duration_seconds if direct_bike_route.total_duration_seconds else 0
                detour_time = t_total - t_direct
                if detour_time <= max_detour_time_seconds:
                    print(f"  验证通过: 绕行增加时间 {detour_time} 秒，不超过 {max_detour_time_seconds} 秒")
                else:
                    print(f"  验证失败: 绕行增加时间 {detour_time} 秒，超过 {max_detour_time_seconds} 秒")
                    all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
