"""
修改任务指令：你打算在附近2000米内找一家网吧，评分不低于4.3分，人均消费不超过25元。这家网吧离济宁市政府的直线距离不少于500米。你从济宁站开车过去的路线中，希望至少存在一个途径点满足附近200米存在公交站。你从当前位置骑自行车到网吧的距离不能超过3公里。你同事从济宁市政府过来，你们在网吧会合后再一起去济宁站，整个开车行程不超过60分钟。网吧步行到东大寺公交站的时间要在10分钟以内。另外，从网吧开车到济宁站的时间不能超过10分钟。你健谈外向，乐观，乐于合作。
输入：B0JU59DEVD
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_search_detail('B0JU59DEVD')获取网吧详细信息，验证rating≥4.3，biz_ext.cost≤25
2. 调用maps_around_search('116.580274,35.412576', '网吧', 2000)验证目标网吧在搜索范围内
3. 调用maps_text_search('济宁市政府', '济宁')获取poi_id，再调用maps_search_detail获取坐标(116.587116,35.415117)
4. 调用maps_distance('116.587116,35.415117', '116.589865,35.406083')验证距离≥500米
5. 调用maps_text_search('济宁站', '济宁')获取poi_id，再调用maps_search_detail获取坐标(116.600756,35.392521)
6. 调用maps_driving_by_coordinates('116.600756,35.392521', '116.589865,35.406083')获取路线步骤，遍历途经点，调用maps_around_search('途径点坐标', '公交站', 200)验证存在一个途径点附近有公交站
9. 调用maps_bicycling_by_coordinates('116.580274,35.412576', '116.589865,35.406083')验证骑行距离≤3000米
10. 调用maps_driving_by_coordinates('116.587116,35.415117', '116.589865,35.406083')获取时间t1
11. 调用maps_driving_by_coordinates('116.589865,35.406083', '116.600756,35.392521')获取时间t2，验证t1+t2≤3600秒
12. 调用maps_walking_by_coordinates('116.589865,35.406083', '116.588880,35.404284')验证步行时间≤600秒
13. 调用maps_driving_by_coordinates('116.589865,35.406083', '116.600756,35.392521')验证驾车时间≤600秒
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
    target_poi_id: str = 'B0JU59DEVD',
    user_location: str = '116.580274,35.412576',
    government_name: str = '济宁市政府',
    city: str = '济宁',
    station_name: str = '济宁站',
    bus_station_name: str = '东大寺公交站'
) -> bool:
    """
    验证POI是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID，默认值为 'B0JU59DEVD'
        user_location: 用户位置坐标，默认值为 '116.580274,35.412576'
        government_name: 政府名称，默认值为 '济宁市政府'
        city: 城市名称，默认值为 '济宁'
        station_name: 车站名称，默认值为 '济宁站'
        bus_station_name: 公交站名称，默认值为 '东大寺公交站'
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 步骤1: 验证rating≥4.3，biz_ext.cost≤25
    print("步骤1: 验证POI评分和消费")
    detail_result = maps_search_detail(target_poi_id)
    if detail_result.error:
        print(f"  失败: 无法获取POI详情 - {detail_result.error}")
        return False
    
    # 获取rating和cost
    rating = None
    cost = None
    if detail_result.biz_ext:
        rating = detail_result.biz_ext.get('rating')
        cost = detail_result.biz_ext.get('cost')
    
    rating_ok = rating is not None and float(rating) >= 4.3
    cost_ok = cost is not None and float(cost) <= 25
    
    if rating_ok and cost_ok:
        print(f"  通过: rating={rating} >= 4.3, cost={cost} <= 25")
    else:
        print(f"  失败: rating={rating} (需要>=4.3), cost={cost} (需要<=25)")
        all_passed = False
    
    # 获取目标POI的坐标
    target_poi_location = detail_result.location
    if not target_poi_location:
        print("  失败: 无法获取目标POI坐标")
        return False
    
    # 步骤2: 验证目标网吧在搜索范围内（用户位置2000米内）
    print("步骤2: 验证目标POI在用户位置2000米范围内")
    around_result = maps_around_search(user_location, '2000', '网吧')
    if around_result.error:
        print(f"  失败: 无法进行周边搜索 - {around_result.error}")
        all_passed = False
    else:
        target_found = False
        if around_result.pois:
            for poi in around_result.pois:
                if poi.id == target_poi_id:
                    target_found = True
                    break
        
        if target_found:
            print(f"  通过: 目标POI在搜索范围内")
        else:
            print(f"  失败: 目标POI不在搜索范围内")
            all_passed = False
    
    # 步骤3: 获取济宁市政府的坐标
    print("步骤3: 获取政府坐标")
    government_search = maps_text_search(government_name, city)
    if government_search.error or not government_search.pois:
        print(f"  失败: 无法搜索到政府位置 - {government_search.error if government_search.error else '未找到结果'}")
        all_passed = False
        government_location = None
    else:
        government_poi_id = government_search.pois[0].id
        government_detail = maps_search_detail(government_poi_id)
        if government_detail.error or not government_detail.location:
            print(f"  失败: 无法获取政府坐标 - {government_detail.error if government_detail.error else '坐标为空'}")
            all_passed = False
            government_location = None
        else:
            government_location = government_detail.location
            print(f"  通过: 政府坐标 = {government_location}")
    
    # 步骤4: 验证网吧离济宁市政府的距离≥500米
    print("步骤4: 验证网吧离政府的距离>=500米")
    if government_location:
        distance_result = maps_distance(government_location, target_poi_location)
        if distance_result.error or not distance_result.results:
            print(f"  失败: 无法计算距离 - {distance_result.error if distance_result.error else '未找到结果'}")
            all_passed = False
        else:
            distance = distance_result.results[0].distance_meters
            if distance >= 500:
                print(f"  通过: 距离={distance}米 >= 500米")
            else:
                print(f"  失败: 距离={distance}米 < 500米")
                all_passed = False
    else:
        print("  跳过: 无法获取政府坐标")
        all_passed = False
    
    # 步骤5: 获取济宁站的坐标
    print("步骤5: 获取车站坐标")
    station_search = maps_text_search(station_name, city)
    if station_search.error or not station_search.pois:
        print(f"  失败: 无法搜索到车站位置 - {station_search.error if station_search.error else '未找到结果'}")
        all_passed = False
        station_location = None
    else:
        station_poi_id = station_search.pois[0].id
        station_detail = maps_search_detail(station_poi_id)
        if station_detail.error or not station_detail.location:
            print(f"  失败: 无法获取车站坐标 - {station_detail.error if station_detail.error else '坐标为空'}")
            all_passed = False
            station_location = None
        else:
            station_location = station_detail.location
            print(f"  通过: 车站坐标 = {station_location}")
    
    # 步骤6: 验证从济宁站到网吧的路线中，至少存在一个途径点附近有公交站
    print("步骤6: 验证从车站到网吧的路线中，至少存在一个途径点附近有公交站")
    waypoint_coord = None
    bus_station_coord = None
    if station_location:
        driving_result = maps_driving_by_coordinates(station_location, target_poi_location)
        if driving_result.error or not driving_result.steps:
            print(f"  失败: 无法获取驾车路线 - {driving_result.error if driving_result.error else '未找到路线步骤'}")
            all_passed = False
        else:
            waypoint_with_bus = False
            # 遍历所有步骤，跳过最后一个步骤（终点）
            for i, step in enumerate(driving_result.steps[:-1]):
                waypoint_coord = step.to_coordinates
                
                # 检查途径点附近200米是否有公交站
                bus_search = maps_around_search(waypoint_coord, '200', '公交站')
                if not bus_search.error and bus_search.pois:
                    waypoint_with_bus = True
                    bus_station_coord = bus_search.pois[0].location
                    print(f"  通过: 找到途径点 {waypoint_coord} 附近有公交站")
                    break
            
            if not waypoint_with_bus:
                print(f"  失败: 未找到满足条件的途径点")
                all_passed = False
    else:
        print("  跳过: 无法获取车站坐标")
        all_passed = False
    
    
    # 步骤9: 验证骑行距离≤3000米
    print("步骤9: 验证从用户位置到网吧的骑行距离<=3000米")
    bicycling_result = maps_bicycling_by_coordinates(user_location, target_poi_location)
    if bicycling_result.error:
        print(f"  失败: 无法获取骑行路线 - {bicycling_result.error}")
        all_passed = False
    else:
        if bicycling_result.total_distance_meters is not None:
            distance = bicycling_result.total_distance_meters
            if distance <= 3000:
                print(f"  通过: 骑行距离={distance}米 <= 3000米")
            else:
                print(f"  失败: 骑行距离={distance}米 > 3000米")
                all_passed = False
        else:
            print(f"  失败: 无法获取骑行距离")
            all_passed = False
    
    # 步骤10: 获取从济宁市政府到网吧的驾车时间t1
    print("步骤10: 获取从政府到网吧的驾车时间t1")
    if government_location:
        driving_t1_result = maps_driving_by_coordinates(government_location, target_poi_location)
        if driving_t1_result.error or driving_t1_result.total_duration_seconds is None:
            print(f"  失败: 无法获取驾车时间 - {driving_t1_result.error if driving_t1_result.error else '时间为空'}")
            all_passed = False
            t1 = None
        else:
            t1 = driving_t1_result.total_duration_seconds
            print(f"  通过: t1 = {t1}秒")
    else:
        print("  跳过: 无法获取政府坐标")
        all_passed = False
        t1 = None
    
    # 步骤11: 验证t1+t2≤3600秒（t2是从网吧到济宁站的时间）
    print("步骤11: 验证从政府到网吧再到车站的总时间<=3600秒")
    if station_location and t1 is not None:
        driving_t2_result = maps_driving_by_coordinates(target_poi_location, station_location)
        if driving_t2_result.error or driving_t2_result.total_duration_seconds is None:
            print(f"  失败: 无法获取驾车时间t2 - {driving_t2_result.error if driving_t2_result.error else '时间为空'}")
            all_passed = False
        else:
            t2 = driving_t2_result.total_duration_seconds
            total_time = t1 + t2
            if total_time <= 3600:
                print(f"  通过: t1+t2={total_time}秒 <= 3600秒")
            else:
                print(f"  失败: t1+t2={total_time}秒 > 3600秒")
                all_passed = False
    else:
        print("  跳过: 无法获取必要坐标或时间")
        all_passed = False
    
    # 步骤12: 验证步行时间≤600秒（从网吧到东大寺公交站）
    print("步骤12: 验证从网吧到公交站的步行时间<=600秒")
    bus_station_search = maps_text_search(bus_station_name, city)
    if bus_station_search.error or not bus_station_search.pois:
        print(f"  失败: 无法搜索到公交站位置 - {bus_station_search.error if bus_station_search.error else '未找到结果'}")
        all_passed = False
    else:
        bus_station_poi_id = bus_station_search.pois[0].id
        bus_station_detail = maps_search_detail(bus_station_poi_id)
        if bus_station_detail.error or not bus_station_detail.location:
            print(f"  失败: 无法获取公交站坐标 - {bus_station_detail.error if bus_station_detail.error else '坐标为空'}")
            all_passed = False
        else:
            bus_station_location = bus_station_detail.location
            walking_result = maps_walking_by_coordinates(target_poi_location, bus_station_location)
            if walking_result.error or walking_result.total_duration_seconds is None:
                print(f"  失败: 无法获取步行时间 - {walking_result.error if walking_result.error else '时间为空'}")
                all_passed = False
            else:
                walking_time = walking_result.total_duration_seconds
                if walking_time <= 600:
                    print(f"  通过: 步行时间={walking_time}秒 <= 600秒")
                else:
                    print(f"  失败: 步行时间={walking_time}秒 > 600秒")
                    all_passed = False
    
    # 步骤13: 验证驾车时间≤600秒（从网吧到济宁站）
    print("步骤13: 验证从网吧到车站的驾车时间<=600秒")
    if station_location:
        driving_time_result = maps_driving_by_coordinates(target_poi_location, station_location)
        if driving_time_result.error or driving_time_result.total_duration_seconds is None:
            print(f"  失败: 无法获取驾车时间 - {driving_time_result.error if driving_time_result.error else '时间为空'}")
            all_passed = False
        else:
            driving_time = driving_time_result.total_duration_seconds
            if driving_time <= 600:
                print(f"  通过: 驾车时间={driving_time}秒 <= 600秒")
            else:
                print(f"  失败: 驾车时间={driving_time}秒 > 600秒")
                all_passed = False
    else:
        print("  跳过: 无法获取车站坐标")
        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
