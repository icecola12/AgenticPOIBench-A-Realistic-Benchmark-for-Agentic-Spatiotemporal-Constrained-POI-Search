"""
修改任务指令：你想在附近2000米内找一个加油站。这个加油站离长春火车站的直线距离不少于500米。从你家到加油站的开车路线中，至少要存在一个途经点满足离宽平桥地铁站直线距离小于600米。而且这个途经点附近500米内得有邮局。你计划从家先去加油站，然后去机场，整个开车时间不能超过60分钟。绕道去加油站相比直接去机场，增加的时间不能超过15分钟。加油站到宽平桥地铁站的骑车时间要在10分钟以内。另外，你从家到加油站的时间和你朋友从欧亚卖场到加油站的时间差不能超过10分钟。你思路混乱，可能会混淆信息，让对话难以跟进。
输入：B0IUPR7E5S
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用 maps_around_search('125.278839,43.862659', '加油站', 2000) 验证目标加油站是否在2000米范围内。
2. 调用 maps_search_detail('B0IUPR7E5S') 获取加油站坐标 (125.275842,43.863489)。
3. 调用 maps_distance('125.275842,43.863489', '125.324675,43.911531') 验证加油站到长春火车站距离 ≥ 500米。
4. 调用 maps_driving_by_coordinates('125.278839,43.862659', '125.275842,43.863489') 获取驾车路线步骤，提取所有途经点坐标。
5. 对每个途经点，调用 maps_distance(途经点坐标, '125.274103,43.862603') 验证到宽平桥地铁站的直线距离 < 600米。调用 maps_around_search(途经点坐标, '邮局', 500) 验证该点500米范围内存在邮局。
7. 调用 maps_driving_by_coordinates('125.278839,43.862659', '125.275842,43.863489') 获取时间 t1，调用 maps_driving_by_coordinates('125.275842,43.863489', '125.694951,43.997004') 获取时间 t2，验证 t1 + t2 ≤ 3600秒。
8. 调用 maps_driving_by_coordinates('125.278839,43.862659', '125.694951,43.997004') 获取时间 t3，验证 (t1 + t2) - t3 ≤ 900秒。
9. 调用 maps_bicycling_by_coordinates('125.275842,43.863489', '125.274103,43.862603') 验证骑行时间 ≤ 600秒。
10. 调用 maps_driving_by_coordinates('125.245370,43.841029', '125.275842,43.863489') 获取时间 t4，调用 maps_driving_by_coordinates('125.278839,43.862659', '125.275842,43.863489') 获取时间 t1，验证 |t1 - t4| ≤ 600秒。
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
    target_poi_id: str = 'B0IUPR7E5S',
    user_location: str = '125.278839,43.862659',
    gas_station_keywords: str = '加油站',
    gas_station_radius: str = '2000',
    train_station_keywords: str = '长春火车站',
    train_station_city: str = '长春',
    min_distance_to_train_station: int = 500,
    subway_station_keywords: str = '宽平桥地铁站',
    subway_station_city: str = '长春',
    max_distance_to_subway_station: int = 600,
    post_office_keywords: str = '邮局',
    post_office_radius: str = '500',
    airport_keywords: str = '机场',
    airport_city: str = '长春',
    max_total_time_seconds: int = 3600,
    max_detour_time_seconds: int = 900,
    max_bicycling_time_seconds: int = 600,
    friend_location_keywords: str = '欧亚卖场',
    friend_location_city: str = '长春',
    max_time_diff_seconds: int = 600
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID，默认值为 'B0IUPR7E5S'
        user_location: 用户位置坐标，默认值为 '125.278839,43.862659'
        其他参数为验证步骤中需要的参数，使用验证步骤中的值作为默认值
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 调用maps_around_search验证目标加油站是否在2000米范围内
    print("验证步骤1: 检查目标加油站在用户位置2000米范围内")
    around_result = maps_around_search(user_location, gas_station_radius, gas_station_keywords)
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
        print("  验证失败: 目标加油站不在搜索结果中")
        all_passed = False
    else:
        print("  验证通过: 目标加油站在搜索结果中")
    
    # 验证步骤2: 调用maps_search_detail获取加油站坐标
    print("验证步骤2: 获取加油站坐标")
    gas_station_detail = maps_search_detail(target_poi_id)
    if gas_station_detail.error or not gas_station_detail.location:
        print(f"  验证失败: 无法获取加油站坐标 - {gas_station_detail.error if gas_station_detail.error else '坐标为空'}")
        return False
    
    gas_station_location = gas_station_detail.location
    print(f"  验证通过: 加油站坐标 {gas_station_location}")
    
    # 验证步骤3: 获取长春火车站坐标，验证加油站到长春火车站距离≥500米
    print("验证步骤3: 验证加油站距离长春火车站不少于500米")
    train_station_search = maps_text_search(train_station_keywords, train_station_city)
    if train_station_search.error or not train_station_search.pois:
        print(f"  验证失败: 无法搜索到长春火车站 - {train_station_search.error if train_station_search.error else '未找到结果'}")
        all_passed = False
    else:
        train_station_poi_id = train_station_search.pois[0].id
        train_station_detail = maps_search_detail(train_station_poi_id)
        if train_station_detail.error or not train_station_detail.location:
            print(f"  验证失败: 无法获取长春火车站坐标 - {train_station_detail.error if train_station_detail.error else '坐标为空'}")
            all_passed = False
        else:
            train_station_location = train_station_detail.location
            distance_result = maps_distance(gas_station_location, train_station_location)
            if distance_result.error or not distance_result.results:
                print(f"  验证失败: 无法计算距离 - {distance_result.error if distance_result.error else '未找到结果'}")
                all_passed = False
            else:
                distance = distance_result.results[0].distance_meters
                if distance >= min_distance_to_train_station:
                    print(f"  验证通过: 加油站距离长春火车站 {distance} 米，不少于 {min_distance_to_train_station} 米")
                else:
                    print(f"  验证失败: 加油站距离长春火车站 {distance} 米，少于 {min_distance_to_train_station} 米")
                    all_passed = False
    
    # 验证步骤4: 调用maps_driving_by_coordinates获取驾车路线步骤，提取所有途经点坐标
    print("验证步骤4: 获取驾车路线途经点")
    driving_route = maps_driving_by_coordinates(user_location, gas_station_location)
    if driving_route.error or not driving_route.steps:
        print(f"  验证失败: 无法获取驾车路线 - {driving_route.error if driving_route.error else '路线为空'}")
        all_passed = False
        waypoints = []
    else:
        # 提取所有途经点坐标（steps中的to_coordinates，除了最后一个）
        waypoints = [step.to_coordinates for step in driving_route.steps[:-1]]
        print(f"  验证通过: 获取到 {len(waypoints)} 个途经点")
    
    # 验证步骤5: 对每个途经点，验证到宽平桥地铁站距离<600米，且附近500米有邮局
    if waypoints:
        print("验证步骤5: 验证途经点到宽平桥地铁站距离小于600米且附近500米有邮局")
        # 先获取宽平桥地铁站坐标
        subway_station_search = maps_text_search(subway_station_keywords, subway_station_city)
        if subway_station_search.error or not subway_station_search.pois:
            print(f"  验证失败: 无法搜索到宽平桥地铁站 - {subway_station_search.error if subway_station_search.error else '未找到结果'}")
            all_passed = False
            subway_station_location = None
        else:
            subway_station_poi_id = subway_station_search.pois[0].id
            subway_station_detail = maps_search_detail(subway_station_poi_id)
            if subway_station_detail.error or not subway_station_detail.location:
                print(f"  验证失败: 无法获取宽平桥地铁站坐标 - {subway_station_detail.error if subway_station_detail.error else '坐标为空'}")
                all_passed = False
                subway_station_location = None
            else:
                subway_station_location = subway_station_detail.location
                print(f"  获取宽平桥地铁站坐标: {subway_station_location}")
        
        if subway_station_location:
            waypoint_found = False
            for waypoint in waypoints:
                # 验证到宽平桥地铁站距离<600米
                waypoint_distance_result = maps_distance(waypoint, subway_station_location)
                if waypoint_distance_result.error or not waypoint_distance_result.results:
                    continue
                
                waypoint_distance = waypoint_distance_result.results[0].distance_meters
                if waypoint_distance >= max_distance_to_subway_station:
                    continue
                
                # 验证附近500米有邮局
                post_office_result = maps_around_search(waypoint, post_office_radius, post_office_keywords)
                has_post_office = not post_office_result.error and post_office_result.pois and len(post_office_result.pois) > 0
                
                if has_post_office:
                    waypoint_found = True
                    print(f"  验证通过: 途经点 {waypoint} 满足条件（距离宽平桥地铁站 {waypoint_distance} 米，附近有邮局）")
                    break
            
            if not waypoint_found:
                print("  验证失败: 未找到满足条件的途经点（距离宽平桥地铁站小于600米且附近500米有邮局）")
                all_passed = False
    
    # 验证步骤7: 获取机场坐标，验证总时间≤3600秒
    print("验证步骤7: 验证从用户位置到加油站再到机场的总时间不超过3600秒")
    airport_search = maps_text_search(airport_keywords, airport_city)
    if airport_search.error or not airport_search.pois:
        print(f"  验证失败: 无法搜索到机场 - {airport_search.error if airport_search.error else '未找到结果'}")
        all_passed = False
        airport_location = None
    else:
        airport_poi_id = airport_search.pois[0].id
        airport_detail = maps_search_detail(airport_poi_id)
        if airport_detail.error or not airport_detail.location:
            print(f"  验证失败: 无法获取机场坐标 - {airport_detail.error if airport_detail.error else '坐标为空'}")
            all_passed = False
            airport_location = None
        else:
            airport_location = airport_detail.location
            print(f"  获取机场坐标: {airport_location}")
    
    if airport_location:
        route1 = maps_driving_by_coordinates(user_location, gas_station_location)
        route2 = maps_driving_by_coordinates(gas_station_location, airport_location)
        
        if route1.error or route2.error:
            print(f"  验证失败: 无法获取路线时间 - {route1.error if route1.error else route2.error}")
            all_passed = False
        else:
            t1 = route1.total_duration_seconds if route1.total_duration_seconds else 0
            t2 = route2.total_duration_seconds if route2.total_duration_seconds else 0
            total_time = t1 + t2
            if total_time <= max_total_time_seconds:
                print(f"  验证通过: 总时间 {total_time} 秒，不超过 {max_total_time_seconds} 秒")
            else:
                print(f"  验证失败: 总时间 {total_time} 秒，超过 {max_total_time_seconds} 秒")
                all_passed = False
        
        # 验证步骤8: 验证绕行增加时间≤900秒
        print("验证步骤8: 验证绕行增加时间不超过900秒")
        direct_route = maps_driving_by_coordinates(user_location, airport_location)
        if direct_route.error:
            print(f"  验证失败: 无法获取直达路线时间 - {direct_route.error}")
            all_passed = False
        else:
            t3 = direct_route.total_duration_seconds if direct_route.total_duration_seconds else 0
            detour_time = total_time - t3
            if detour_time <= max_detour_time_seconds:
                print(f"  验证通过: 绕行增加时间 {detour_time} 秒，不超过 {max_detour_time_seconds} 秒")
            else:
                print(f"  验证失败: 绕行增加时间 {detour_time} 秒，超过 {max_detour_time_seconds} 秒")
                all_passed = False
    
    # 验证步骤9: 验证加油站到宽平桥地铁站骑行时间≤600秒
    print("验证步骤9: 验证加油站到宽平桥地铁站骑行时间不超过600秒")
    if subway_station_location:
        bicycling_route = maps_bicycling_by_coordinates(gas_station_location, subway_station_location)
        if bicycling_route.error:
            print(f"  验证失败: 无法获取骑行路线时间 - {bicycling_route.error}")
            all_passed = False
        else:
            bicycling_time = bicycling_route.total_duration_seconds if bicycling_route.total_duration_seconds else 0
            if bicycling_time <= max_bicycling_time_seconds:
                print(f"  验证通过: 骑行时间 {bicycling_time} 秒，不超过 {max_bicycling_time_seconds} 秒")
            else:
                print(f"  验证失败: 骑行时间 {bicycling_time} 秒，超过 {max_bicycling_time_seconds} 秒")
                all_passed = False
    else:
        print("  验证失败: 无法获取宽平桥地铁站坐标")
        all_passed = False
    
    # 验证步骤10: 验证从用户位置到加油站的时间与从欧亚卖场到加油站的时间差≤600秒
    print("验证步骤10: 验证从用户位置到加油站的时间与从欧亚卖场到加油站的时间差不超过600秒")
    friend_location_search = maps_text_search(friend_location_keywords, friend_location_city)
    if friend_location_search.error or not friend_location_search.pois:
        print(f"  验证失败: 无法搜索到欧亚卖场 - {friend_location_search.error if friend_location_search.error else '未找到结果'}")
        all_passed = False
    else:
        friend_location_poi_id = friend_location_search.pois[0].id
        friend_location_detail = maps_search_detail(friend_location_poi_id)
        if friend_location_detail.error or not friend_location_detail.location:
            print(f"  验证失败: 无法获取欧亚卖场坐标 - {friend_location_detail.error if friend_location_detail.error else '坐标为空'}")
            all_passed = False
        else:
            friend_location = friend_location_detail.location
            print(f"  获取欧亚卖场坐标: {friend_location}")
            
            # 获取从用户位置到加油站的时间 t1
            route1 = maps_driving_by_coordinates(user_location, gas_station_location)
            # 获取从欧亚卖场到加油站的时间 t4
            route4 = maps_driving_by_coordinates(friend_location, gas_station_location)
            
            if route1.error or route4.error:
                print(f"  验证失败: 无法获取路线时间 - {route1.error if route1.error else route4.error}")
                all_passed = False
            else:
                t1 = route1.total_duration_seconds if route1.total_duration_seconds else 0
                t4 = route4.total_duration_seconds if route4.total_duration_seconds else 0
                time_diff = abs(t1 - t4)
                if time_diff <= max_time_diff_seconds:
                    print(f"  验证通过: 时间差 {time_diff} 秒，不超过 {max_time_diff_seconds} 秒")
                else:
                    print(f"  验证失败: 时间差 {time_diff} 秒，超过 {max_time_diff_seconds} 秒")
                    all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
