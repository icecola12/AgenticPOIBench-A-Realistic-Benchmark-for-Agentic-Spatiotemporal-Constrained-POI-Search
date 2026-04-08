"""
修改任务指令：你想在附近1000米内找一个ATM取钱。这个ATM不能离中国工商银行24小时自助银行(古槐路支行)的直线距离需要大于500米。ATM到济医附院公交站的直线距离不超过800米。你取完钱后要去济宁火车站，所以从医院到ATM再到火车站的开车总时间不能超过10分钟，而且取钱绕路增加的时间不能超过2分钟。另外，从ATM走到济医附院公交站的时间不能超过15分钟。你步行去ATM的路线中，需要至少存在一个途径点满足离快活林公交站的直线距离小于300米，并且附近200米有餐厅。你善于使用强制和协商的策略来达到目的。
输入：B0FFKJBSWS
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('116.5794,35.40813', 'ATM', 1000)验证目标ATM在1000米范围内
2. 调用maps_search_detail('B0FFKJBSWS')获取目标ATM坐标(116.571978,35.405669)。
3. 调用maps_walking_by_coordinates('116.5794,35.40813', '116.571978,35.405669')计算步行距离，验证≤1000米。
4. 调用maps_search_detail('B02190BAGK')获取中国工商银行24小时自助银行(古槐路支行)坐标(116.581233,35.408711)。
5. 调用maps_distance('116.571978,35.405669', '116.581233,35.408711')计算直线距离，验证>500米。
6. 调用maps_search_detail('BV09035191')获取济医附院(公交站)坐标(116.580338,35.407390)。
7. 调用maps_distance('116.571978,35.405669', '116.580338,35.407390')计算直线距离，验证≤800米。
8. 调用maps_driving_by_coordinates('116.5794,35.40813', '116.571978,35.405669')获取医院到ATM驾车时间t1。
9. 调用maps_driving_by_coordinates('116.571978,35.405669', '116.600756,35.392521')获取ATM到火车站驾车时间t2。
10. 调用maps_driving_by_coordinates('116.5794,35.40813', '116.600756,35.392521')获取医院直接到火车站驾车时间t3。
11. 验证t1+t2 ≤ 10分钟，且(t1+t2)-t3 ≤ 2分钟。
12. 调用maps_walking_by_coordinates('116.571978,35.405669', '116.580338,35.407390')获取ATM到公交站步行时间，验证≤15分钟。
13. 调用maps_walking_by_coordinates('116.5794,35.40813', '116.571978,35.405669')获取步行路线steps，提取途径点坐标。
14. 对每个途径点调用maps_distance计算到快活林公交站(116.575152,35.405247)的直线距离，验证存在一点距离<300米。
15. 对每个途径点调用maps_around_search(途径点坐标, '餐厅', 200)验证存在餐厅。
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
    target_poi_id: str = 'B0FFKJBSWS',
    user_location: str = '116.5794,35.40813',
    atm_keywords: str = 'ATM',
    atm_radius: str = '1000',
    max_walking_distance_meters: int = 1000,
    bank_keywords: str = '中国工商银行24小时自助银行(古槐路支行)',
    bank_city: str = '济宁',
    min_distance_to_bank_meters: int = 500,
    bus_station_keywords: str = '济医附院',
    bus_station_city: str = '济宁',
    max_distance_to_bus_station_meters: int = 800,
    train_station_keywords: str = '济宁火车站',
    train_station_city: str = '济宁',
    max_total_driving_time_seconds: int = 600,
    max_detour_time_seconds: int = 120,
    max_walking_time_to_bus_station_seconds: int = 900,
    waypoint_bus_station_keywords: str = '快活林公交站',
    waypoint_bus_station_city: str = '济宁',
    max_distance_to_waypoint_bus_station_meters: int = 300,
    restaurant_keywords: str = '餐厅',
    restaurant_radius: str = '200'
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID，默认值为 'B0FFKJBSWS'
        user_location: 用户位置坐标，默认值为 '116.5794,35.40813'
        其他参数为验证步骤中需要的参数，使用验证步骤中的值作为默认值
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 调用maps_around_search验证目标ATM在1000米范围内
    print("验证步骤1: 检查目标ATM在用户位置1000米范围内")
    around_result = maps_around_search(user_location, atm_radius, atm_keywords)
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
        print("  验证失败: 目标ATM不在搜索结果中")
        all_passed = False
    else:
        print("  验证通过: 目标ATM在搜索结果中")
    
    # 验证步骤2: 调用maps_search_detail获取目标ATM坐标
    print("验证步骤2: 获取目标ATM坐标")
    atm_detail = maps_search_detail(target_poi_id)
    if atm_detail.error or not atm_detail.location:
        print(f"  验证失败: 无法获取ATM坐标 - {atm_detail.error if atm_detail.error else '坐标为空'}")
        return False
    
    atm_location = atm_detail.location
    print(f"  验证通过: ATM坐标 {atm_location}")
    
    # 验证步骤3: 调用maps_walking_by_coordinates计算步行距离，验证≤1000米
    print("验证步骤3: 验证从用户位置到ATM的步行距离不超过1000米")
    walking_route1 = maps_walking_by_coordinates(user_location, atm_location)
    if walking_route1.error:
        print(f"  验证失败: 无法获取步行路线 - {walking_route1.error}")
        all_passed = False
    else:
        walking_distance = walking_route1.total_distance_meters if walking_route1.total_distance_meters else 0
        if walking_distance <= max_walking_distance_meters:
            print(f"  验证通过: 步行距离 {walking_distance} 米，不超过 {max_walking_distance_meters} 米")
        else:
            print(f"  验证失败: 步行距离 {walking_distance} 米，超过 {max_walking_distance_meters} 米")
            all_passed = False
    
    # 验证步骤4: 搜索并获取中国工商银行24小时自助银行(古槐路支行)坐标
    print("验证步骤4: 获取中国工商银行24小时自助银行(古槐路支行)坐标")
    bank_search = maps_text_search(bank_keywords, bank_city)
    if bank_search.error or not bank_search.pois:
        print(f"  验证失败: 无法搜索到银行 - {bank_search.error if bank_search.error else '未找到结果'}")
        all_passed = False
        bank_location = None
    else:
        bank_poi_id = bank_search.pois[0].id
        bank_detail = maps_search_detail(bank_poi_id)
        if bank_detail.error or not bank_detail.location:
            print(f"  验证失败: 无法获取银行坐标 - {bank_detail.error if bank_detail.error else '坐标为空'}")
            all_passed = False
            bank_location = None
        else:
            bank_location = bank_detail.location
            print(f"  验证通过: 银行坐标 {bank_location}")
    
    # 验证步骤5: 调用maps_distance计算直线距离，验证>500米
    if bank_location:
        print("验证步骤5: 验证ATM到银行的直线距离大于500米")
        distance_result1 = maps_distance(atm_location, bank_location)
        if distance_result1.error or not distance_result1.results:
            print(f"  验证失败: 无法计算距离 - {distance_result1.error if distance_result1.error else '未找到结果'}")
            all_passed = False
        else:
            distance1 = distance_result1.results[0].distance_meters
            if distance1 > min_distance_to_bank_meters:
                print(f"  验证通过: ATM到银行距离 {distance1} 米，大于 {min_distance_to_bank_meters} 米")
            else:
                print(f"  验证失败: ATM到银行距离 {distance1} 米，不大于 {min_distance_to_bank_meters} 米")
                all_passed = False
    
    # 验证步骤6: 搜索并获取济医附院(公交站)坐标
    print("验证步骤6: 获取济医附院(公交站)坐标")
    bus_station_search = maps_text_search(bus_station_keywords, bus_station_city)
    if bus_station_search.error or not bus_station_search.pois:
        print(f"  验证失败: 无法搜索到济医附院公交站 - {bus_station_search.error if bus_station_search.error else '未找到结果'}")
        all_passed = False
        bus_station_location = None
    else:
        # 查找包含"公交站"的POI
        bus_station_poi_id = None
        for poi in bus_station_search.pois:
            if '公交站' in poi.name or '公交' in poi.name:
                bus_station_poi_id = poi.id
                break
        if not bus_station_poi_id and bus_station_search.pois:
            bus_station_poi_id = bus_station_search.pois[0].id
        
        if bus_station_poi_id:
            bus_station_detail = maps_search_detail(bus_station_poi_id)
            if bus_station_detail.error or not bus_station_detail.location:
                print(f"  验证失败: 无法获取公交站坐标 - {bus_station_detail.error if bus_station_detail.error else '坐标为空'}")
                all_passed = False
                bus_station_location = None
            else:
                bus_station_location = bus_station_detail.location
                print(f"  验证通过: 济医附院公交站坐标 {bus_station_location}")
        else:
            print("  验证失败: 未找到济医附院公交站")
            all_passed = False
            bus_station_location = None
    
    # 验证步骤7: 调用maps_distance计算直线距离，验证≤800米
    if bus_station_location:
        print("验证步骤7: 验证ATM到济医附院公交站的直线距离不超过800米")
        distance_result2 = maps_distance(atm_location, bus_station_location)
        if distance_result2.error or not distance_result2.results:
            print(f"  验证失败: 无法计算距离 - {distance_result2.error if distance_result2.error else '未找到结果'}")
            all_passed = False
        else:
            distance2 = distance_result2.results[0].distance_meters
            if distance2 <= max_distance_to_bus_station_meters:
                print(f"  验证通过: ATM到公交站距离 {distance2} 米，不超过 {max_distance_to_bus_station_meters} 米")
            else:
                print(f"  验证失败: ATM到公交站距离 {distance2} 米，超过 {max_distance_to_bus_station_meters} 米")
                all_passed = False
    
    # 验证步骤8-11: 获取驾车时间并验证
    print("验证步骤8-11: 验证驾车时间条件")
    train_station_search = maps_text_search(train_station_keywords, train_station_city)
    if train_station_search.error or not train_station_search.pois:
        print(f"  验证失败: 无法搜索到火车站 - {train_station_search.error if train_station_search.error else '未找到结果'}")
        all_passed = False
        train_station_location = None
    else:
        train_station_poi_id = train_station_search.pois[0].id
        train_station_detail = maps_search_detail(train_station_poi_id)
        if train_station_detail.error or not train_station_detail.location:
            print(f"  验证失败: 无法获取火车站坐标 - {train_station_detail.error if train_station_detail.error else '坐标为空'}")
            all_passed = False
            train_station_location = None
        else:
            train_station_location = train_station_detail.location
            print(f"  获取火车站坐标: {train_station_location}")
    
    if train_station_location:
        # 步骤8: 获取医院到ATM驾车时间t1
        route1 = maps_driving_by_coordinates(user_location, atm_location)
        # 步骤9: 获取ATM到火车站驾车时间t2
        route2 = maps_driving_by_coordinates(atm_location, train_station_location)
        # 步骤10: 获取医院直接到火车站驾车时间t3
        route3 = maps_driving_by_coordinates(user_location, train_station_location)
        
        if route1.error or route2.error or route3.error:
            print(f"  验证失败: 无法获取路线时间 - {route1.error if route1.error else (route2.error if route2.error else route3.error)}")
            all_passed = False
        else:
            t1 = route1.total_duration_seconds if route1.total_duration_seconds else 0
            t2 = route2.total_duration_seconds if route2.total_duration_seconds else 0
            t3 = route3.total_duration_seconds if route3.total_duration_seconds else 0
            total_time = t1 + t2
            detour_time = total_time - t3
            
            # 步骤11: 验证t1+t2 ≤ 10分钟，且(t1+t2)-t3 ≤ 2分钟
            if total_time <= max_total_driving_time_seconds:
                print(f"  验证通过: 总时间 {total_time} 秒，不超过 {max_total_driving_time_seconds} 秒")
            else:
                print(f"  验证失败: 总时间 {total_time} 秒，超过 {max_total_driving_time_seconds} 秒")
                all_passed = False
            
            if detour_time <= max_detour_time_seconds:
                print(f"  验证通过: 绕行增加时间 {detour_time} 秒，不超过 {max_detour_time_seconds} 秒")
            else:
                print(f"  验证失败: 绕行增加时间 {detour_time} 秒，超过 {max_detour_time_seconds} 秒")
                all_passed = False
    
    # 验证步骤12: 调用maps_walking_by_coordinates获取ATM到公交站步行时间，验证≤15分钟
    if bus_station_location:
        print("验证步骤12: 验证从ATM到济医附院公交站的步行时间不超过15分钟")
        walking_route2 = maps_walking_by_coordinates(atm_location, bus_station_location)
        if walking_route2.error:
            print(f"  验证失败: 无法获取步行路线时间 - {walking_route2.error}")
            all_passed = False
        else:
            walking_time = walking_route2.total_duration_seconds if walking_route2.total_duration_seconds else 0
            if walking_time <= max_walking_time_to_bus_station_seconds:
                print(f"  验证通过: 步行时间 {walking_time} 秒，不超过 {max_walking_time_to_bus_station_seconds} 秒")
            else:
                print(f"  验证失败: 步行时间 {walking_time} 秒，超过 {max_walking_time_to_bus_station_seconds} 秒")
                all_passed = False
    
    # 验证步骤13-15: 获取步行路线途径点并验证
    print("验证步骤13-15: 验证步行路线途径点条件")
    walking_route3 = maps_walking_by_coordinates(user_location, atm_location)
    if walking_route3.error or not walking_route3.steps:
        print(f"  验证失败: 无法获取步行路线 - {walking_route3.error if walking_route3.error else '路线为空'}")
        all_passed = False
        waypoints = []
    else:
        # 提取途径点坐标（steps中的to_coordinates，除了最后一个）
        waypoints = [step.to_coordinates for step in walking_route3.steps[:-1]]
        print(f"  获取到 {len(waypoints)} 个途径点")
    
    if waypoints:
        # 搜索快活林公交站
        waypoint_bus_station_search = maps_text_search(waypoint_bus_station_keywords, waypoint_bus_station_city)
        if waypoint_bus_station_search.error or not waypoint_bus_station_search.pois:
            print(f"  验证失败: 无法搜索到快活林公交站 - {waypoint_bus_station_search.error if waypoint_bus_station_search.error else '未找到结果'}")
            all_passed = False
            waypoint_bus_station_location = None
        else:
            waypoint_bus_station_poi_id = waypoint_bus_station_search.pois[0].id
            waypoint_bus_station_detail = maps_search_detail(waypoint_bus_station_poi_id)
            if waypoint_bus_station_detail.error or not waypoint_bus_station_detail.location:
                print(f"  验证失败: 无法获取快活林公交站坐标 - {waypoint_bus_station_detail.error if waypoint_bus_station_detail.error else '坐标为空'}")
                all_passed = False
                waypoint_bus_station_location = None
            else:
                waypoint_bus_station_location = waypoint_bus_station_detail.location
                print(f"  获取快活林公交站坐标: {waypoint_bus_station_location}")
        
        # 验证步骤14和15: 对每个途径点验证距离<300米且附近200米有餐厅
        waypoint_found = False
        for waypoint in waypoints:
            # 步骤14: 验证到快活林公交站距离<300米
            if waypoint_bus_station_location:
                waypoint_distance_result = maps_distance(waypoint, waypoint_bus_station_location)
                if waypoint_distance_result.error or not waypoint_distance_result.results:
                    continue
                
                waypoint_distance = waypoint_distance_result.results[0].distance_meters
                if waypoint_distance >= max_distance_to_waypoint_bus_station_meters:
                    continue
            else:
                continue
            
            # 步骤15: 验证附近200米有餐厅
            restaurant_result = maps_around_search(waypoint, restaurant_radius, restaurant_keywords)
            has_restaurant = not restaurant_result.error and restaurant_result.pois and len(restaurant_result.pois) > 0
            
            if has_restaurant:
                waypoint_found = True
                print(f"  验证通过: 途径点 {waypoint} 满足条件（距离快活林公交站 {waypoint_distance} 米，附近有餐厅）")
                break
        
        if not waypoint_found:
            print("  验证失败: 未找到满足条件的途径点（距离快活林公交站小于300米且附近200米有餐厅）")
            all_passed = False
    else:
        print("  验证失败: 无法获取途径点")
        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
