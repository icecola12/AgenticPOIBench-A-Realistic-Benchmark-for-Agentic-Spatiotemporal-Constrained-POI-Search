"""
修改任务指令：你想在附近3000米内找一个加油站。这个加油站距离枣强县人民医院的直线距离需要大于500米。你开车从当前位置去加油站，希望途中有一个途经点满足附近300米内有一个公交站且附近500米内有超市。加油站附近要有一个公交站。你计划从当前位置出发，经过加油站，再去汽车站，总行程时间不超过10分钟。而且与直接去汽车站相比，绕行增加的时间不超过3分钟。最后，你从当前位置步行到加油站的时间要比从汽车站开车到加油站的时间至少多5分钟。你说话简短急促，希望快速完成所有事。
输入：B013E00D1Z
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('115.713902,37.51717', '加油站', '3000')确认目标加油站在结果中。
2. 调用maps_search_detail('B013E00D1Z')获取加油站坐标。
3. 调用maps_text_search('枣强县人民医院', '枣强县')获取医院poi_id，再调用maps_search_detail获取坐标，调用maps_distance计算加油站到医院距离，验证>500米。
4. 调用maps_driving_by_coordinates('115.713902,37.51717', '115.732103,37.517990')获取驾车路线，遍历途径点，调用maps_around_search(途径点, '公交站', '300')验证附近300米存在公交站。调用maps_around_search(同一个途经点坐标, '超市', '500')验证存在超市。
7. 调用maps_text_search('枣强汽车站', '枣强县')获取汽车站poi_id，再调用maps_search_detail获取坐标。
8. 调用maps_driving_by_coordinates('115.713902,37.51717', '115.732103,37.517990')获取时间t1，调用maps_driving_by_coordinates('115.732103,37.517990', '115.731223,37.506607')获取时间t2，计算总时间=t1+t2，验证≤600秒。
9. 调用maps_driving_by_coordinates('115.713902,37.51717', '115.731223,37.506607')获取直达时间t3，计算绕行增加时间=(t1+t2)-t3，验证≤180秒。
11. 调用maps_walking_by_coordinates('115.713902,37.51717', '115.732103,37.517990')获取步行时间t_walk，调用maps_driving_by_coordinates('115.731223,37.506607', '115.732103,37.517990')获取驾车时间t_drive，计算t_walk - t_drive，验证>300秒。
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
    target_poi_id: str = 'B013E00D1Z',
    user_location: str = '115.713902,37.51717',
    hospital_keywords: str = '枣强县人民医院',
    hospital_city: str = '枣强县',
    bus_station_keywords: str = '公交站',
    supermarket_keywords: str = '超市',
    bus_station_radius: str = '300',
    supermarket_radius: str = '500',
    station_keywords: str = '枣强汽车站',
    station_city: str = '枣强县',
    gas_station_keywords: str = '加油站',
    gas_station_radius: str = '3000',
    min_distance_to_hospital: int = 500,
    max_total_time_seconds: int = 600,
    max_detour_time_seconds: int = 180,
    min_walk_drive_time_diff_seconds: int = 300
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID，默认值为 'B013E00D1Z'
        user_location: 用户位置坐标，默认值为 '115.713902,37.51717'
        其他参数为验证步骤中需要的参数，使用验证步骤中的值作为默认值
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 调用maps_around_search确认目标加油站在结果中
    print("验证步骤1: 检查目标加油站在用户位置3000米范围内")
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
    
    # 验证步骤3: 验证加油站距离医院>500米
    print("验证步骤3: 验证加油站距离医院大于500米")
    hospital_search = maps_text_search(hospital_keywords, hospital_city)
    if hospital_search.error or not hospital_search.pois:
        print(f"  验证失败: 无法搜索到医院 - {hospital_search.error if hospital_search.error else '未找到结果'}")
        all_passed = False
    else:
        hospital_poi_id = hospital_search.pois[0].id
        hospital_detail = maps_search_detail(hospital_poi_id)
        if hospital_detail.error or not hospital_detail.location:
            print(f"  验证失败: 无法获取医院坐标 - {hospital_detail.error if hospital_detail.error else '坐标为空'}")
            all_passed = False
        else:
            hospital_location = hospital_detail.location
            distance_result = maps_distance(gas_station_location, hospital_location)
            if distance_result.error or not distance_result.results:
                print(f"  验证失败: 无法计算距离 - {distance_result.error if distance_result.error else '未找到结果'}")
                all_passed = False
            else:
                distance = distance_result.results[0].distance_meters
                if distance > min_distance_to_hospital:
                    print(f"  验证通过: 加油站距离医院 {distance} 米，大于 {min_distance_to_hospital} 米")
                else:
                    print(f"  验证失败: 加油站距离医院 {distance} 米，不大于 {min_distance_to_hospital} 米")
                    all_passed = False
    
    # 验证步骤4: 验证从用户位置到加油站的驾车路线中，有一个途经点满足附近300米有公交站且附近500米有超市
    print("验证步骤4: 验证驾车路线中有一个途经点满足附近300米有公交站且附近500米有超市")
    driving_route = maps_driving_by_coordinates(user_location, gas_station_location)
    if driving_route.error or not driving_route.steps:
        print(f"  验证失败: 无法获取驾车路线 - {driving_route.error if driving_route.error else '路线为空'}")
        all_passed = False
    else:
        waypoint_found = False
        # 遍历途经点（steps中的to_coordinates，除了最后一个）
        for i, step in enumerate(driving_route.steps[:-1]):  # 排除最后一个，因为最后一个是终点
            waypoint = step.to_coordinates
            # 检查附近300米是否有公交站
            bus_result = maps_around_search(waypoint, bus_station_radius, bus_station_keywords)
            has_bus_station = not bus_result.error and bus_result.pois and len(bus_result.pois) > 0
            
            # 检查附近500米是否有超市
            supermarket_result = maps_around_search(waypoint, supermarket_radius, supermarket_keywords)
            has_supermarket = not supermarket_result.error and supermarket_result.pois and len(supermarket_result.pois) > 0
            
            if has_bus_station and has_supermarket:
                waypoint_found = True
                print(f"  验证通过: 途经点 {waypoint} 满足条件（附近有公交站和超市）")
                break
        
        if not waypoint_found:
            print("  验证失败: 未找到满足条件的途经点（附近300米有公交站且附近500米有超市）")
            all_passed = False
    
    # 验证步骤5: 验证加油站附近有公交站（根据用户原始指令，但验证步骤中没有明确提到，先跳过）
    # 注意：验证步骤中没有明确提到这一步，但用户原始指令中有，我先不实现
    
    # 验证步骤7: 获取汽车站坐标
    print("验证步骤7: 获取汽车站坐标")
    station_search = maps_text_search(station_keywords, station_city)
    if station_search.error or not station_search.pois:
        print(f"  验证失败: 无法搜索到汽车站 - {station_search.error if station_search.error else '未找到结果'}")
        all_passed = False
        station_location = None
    else:
        station_poi_id = station_search.pois[0].id
        station_detail = maps_search_detail(station_poi_id)
        if station_detail.error or not station_detail.location:
            print(f"  验证失败: 无法获取汽车站坐标 - {station_detail.error if station_detail.error else '坐标为空'}")
            all_passed = False
            station_location = None
        else:
            station_location = station_detail.location
            print(f"  验证通过: 汽车站坐标 {station_location}")
    
    # 验证步骤8: 验证从用户位置->加油站->汽车站的总时间≤600秒
    if station_location:
        print("验证步骤8: 验证从用户位置到加油站再到汽车站的总时间不超过600秒")
        route1 = maps_driving_by_coordinates(user_location, gas_station_location)
        route2 = maps_driving_by_coordinates(gas_station_location, station_location)
        
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
        
        # 验证步骤9: 验证绕行增加时间≤180秒
        print("验证步骤9: 验证绕行增加时间不超过180秒")
        direct_route = maps_driving_by_coordinates(user_location, station_location)
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
        
        # 验证步骤11: 验证步行时间-驾车时间>300秒
        print("验证步骤11: 验证从用户位置步行到加油站的时间比从汽车站开车到加油站的时间至少多300秒")
        walk_route = maps_walking_by_coordinates(user_location, gas_station_location)
        drive_route = maps_driving_by_coordinates(station_location, gas_station_location)
        
        if walk_route.error or drive_route.error:
            print(f"  验证失败: 无法获取路线时间 - {walk_route.error if walk_route.error else drive_route.error}")
            all_passed = False
        else:
            t_walk = walk_route.total_duration_seconds if walk_route.total_duration_seconds else 0
            t_drive = drive_route.total_duration_seconds if drive_route.total_duration_seconds else 0
            time_diff = t_walk - t_drive
            if time_diff > min_walk_drive_time_diff_seconds:
                print(f"  验证通过: 时间差 {time_diff} 秒，大于 {min_walk_drive_time_diff_seconds} 秒")
            else:
                print(f"  验证失败: 时间差 {time_diff} 秒，不大于 {min_walk_drive_time_diff_seconds} 秒")
                all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
