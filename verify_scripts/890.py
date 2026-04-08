"""
修改任务指令：你想在附近2000米内找一个图书馆。这个图书馆离台州图书大厦的直线距离需要大于500米。你从市民广场步行去图书馆的路线中，至少需要存在一个途径点，既满足离市图书馆公交站的直线距离不到600米，又满足附近200米内要有咖啡馆。你从台州西站开车到图书馆，然后步行到市民广场，整个过程不能超过45分钟。图书馆到市图书馆公交站的步行时间不能超过10分钟。另外，你开车从台州西站到图书馆的时间，要比朋友从市民广场步行到图书馆的时间多至少10分钟。你对服务和解决方案持怀疑态度。
输入：B0240051X3
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用 maps_around_search('121.423392,28.658937', '你想在附近2000米内找一个图书馆。这个图书馆离台州图书大厦的直线距离需要大于500米。你从市民广场步行去图书馆的路线中，至少需要存在一个途径点，既满足离市图书馆公交站的直线距离不到600米，又满足附近200米内要有咖啡馆。你从台州西站开车到图书馆，然后步行到市民广场，整个过程不能超过45分钟。图书馆到市图书馆公交站的步行时间不能超过10分钟。另外，你开车从台州西站到图书馆的时间，要比朋友从市民广场步行到图书馆的时间多至少10分钟。你对服务和解决方案持怀疑态度。', 2000) 验证目标图书馆在搜索范围内。
2. 调用 maps_search_detail('B0240051X3') 获取图书馆坐标和详细信息。
3. 调用 maps_distance('121.418293,28.658239', '121.437149,28.670150') 验证图书馆到台州图书大厦的直线距离 > 500 米。
4. 调用 maps_walking_by_coordinates('121.414311,28.655034', '121.418293,28.658239') 获取市民广场到图书馆的步行路线步骤。遍历这些步骤。对每个步骤的 from_coordinates 和 to_coordinates，调用 maps_distance(途经点坐标, '121.419174,28.658274') 计算直线距离，验证是否满足要求。并且调用 maps_around_search('121.418229,28.652952', '咖啡馆', 200) 验证该点附近 200 米内存在咖啡馆（如 UND cafe&taphouse）。
7. 调用 maps_driving_by_coordinates('121.289586,28.686064', '121.418293,28.658239') 获取台州西站到图书馆的驾车时间 T1。
8. 调用 maps_walking_by_coordinates('121.418293,28.658239', '121.414311,28.655034') 获取图书馆到市民广场的步行时间 T2。
9. 验证 (T1 + T2) ≤ 45 分钟。
10. 调用 maps_walking_by_coordinates('121.418293,28.658239', '121.419174,28.658274') 获取图书馆到市图书馆公交站的步行时间 T3，验证 T3 ≤ 10 分钟。
11. 调用 maps_walking_by_coordinates('121.414311,28.655034', '121.418293,28.658239') 获取市民广场到图书馆的步行时间 T4。
12. 验证 T1 - T4 > 10 分钟。
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
    target_poi_id: str = 'B0240051X3',
    user_location: str = '121.423392,28.658937',
    search_keywords: str = '图书馆',
    search_radius: str = '2000',
    bookstore_name: str = '台州图书大厦',
    bookstore_city: str = '台州',
    min_distance_to_bookstore_meters: int = 500,
    square_name: str = '市民广场',
    square_city: str = '台州',
    bus_station_name: str = '市图书馆公交站',
    bus_station_city: str = '台州',
    max_distance_to_bus_station_meters: int = 600,
    cafe_keywords: str = '咖啡馆',
    cafe_radius: str = '200',
    train_station_name: str = '台州西站',
    train_station_city: str = '台州',
    max_total_time_minutes: int = 45,
    max_walking_to_bus_station_minutes: int = 10,
    min_time_difference_minutes: int = 10
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: ""
        search_keywords: 搜索关键词
        search_radius: 搜索半径（米），字符串格式
        bookstore_name: 图书大厦名称
        bookstore_city: 图书大厦所在城市
        min_distance_to_bookstore_meters: 到图书大厦的最小距离（米）
        square_name: 广场名称
        square_city: 广场所在城市
        bus_station_name: 公交站名称
        bus_station_city: 公交站所在城市
        max_distance_to_bus_station_meters: 到公交站的最大距离（米）
        cafe_keywords: 咖啡馆搜索关键词
        cafe_radius: 咖啡馆搜索半径（米），字符串格式
        train_station_name: 火车站名称
        train_station_city: 火车站所在城市
        max_total_time_minutes: 最大总时间（分钟）
        max_walking_to_bus_station_minutes: 到公交站的最大步行时间（分钟）
        min_time_difference_minutes: 最小时间差（分钟）
    
    Returns:
        bool: True表示所有验证通过，False表示部分或全部验证失败
    """
    all_passed = True
    
    # 验证步骤1: 调用 maps_around_search 验证目标图书馆在搜索范围内
    print("验证步骤1: 验证目标图书馆在搜索范围内")
    around_search_result = maps_around_search(user_location, search_radius, search_keywords)
    if around_search_result.error:
        print(f"验证步骤1失败: {around_search_result.error}")
        all_passed = False
    elif not around_search_result.pois:
        print("验证步骤1失败: 未找到符合条件的POI")
        all_passed = False
    else:
        found = False
        for poi in around_search_result.pois:
            if poi.id == target_poi_id:
                found = True
                break
        if found:
            print(f"验证步骤1通过: 目标图书馆 {target_poi_id} 在搜索范围内")
        else:
            print(f"验证步骤1失败: 目标图书馆 {target_poi_id} 不在搜索范围内")
            all_passed = False
    
    # 验证步骤2: 调用 maps_search_detail 获取图书馆坐标和详细信息
    print("验证步骤2: 获取图书馆坐标和详细信息")
    poi_detail = maps_search_detail(target_poi_id)
    if poi_detail.error:
        print(f"验证步骤2失败: {poi_detail.error}")
        return False
    if not poi_detail.location:
        print("验证步骤2失败: 未获取到图书馆坐标")
        return False
    library_location = poi_detail.location
    print(f"验证步骤2通过: 成功获取图书馆坐标 {library_location}")
    
    # 验证步骤3: 验证图书馆到台州图书大厦的直线距离 > 500 米
    print("验证步骤3: 验证图书馆到台州图书大厦的直线距离 > 500 米")
    bookstore_search = maps_text_search(bookstore_name, bookstore_city)
    if bookstore_search.error:
        print(f"验证步骤3失败: 搜索台州图书大厦失败 - {bookstore_search.error}")
        all_passed = False
    elif not bookstore_search.pois or len(bookstore_search.pois) == 0:
        print("验证步骤3失败: 未找到台州图书大厦")
        all_passed = False
    else:
        bookstore_poi_id = bookstore_search.pois[0].id
        bookstore_detail = maps_search_detail(bookstore_poi_id)
        if bookstore_detail.error or not bookstore_detail.location:
            print(f"验证步骤3失败: 无法获取台州图书大厦坐标 - {bookstore_detail.error if bookstore_detail.error else '坐标为空'}")
            all_passed = False
        else:
            bookstore_location = bookstore_detail.location
            distance_result = maps_distance(library_location, bookstore_location)
            if distance_result.error or not distance_result.results:
                print(f"验证步骤3失败: 计算距离失败 - {distance_result.error if distance_result.error else '结果为空'}")
                all_passed = False
            else:
                distance = distance_result.results[0].distance_meters
                if distance > min_distance_to_bookstore_meters:
                    print(f"验证步骤3通过: 距离 {distance} 米 > {min_distance_to_bookstore_meters} 米")
                else:
                    print(f"验证步骤3失败: 距离 {distance} 米 <= {min_distance_to_bookstore_meters} 米")
                    all_passed = False
    
    # 验证步骤4: 获取市民广场到图书馆的步行路线步骤，验证途经点要求
    print("验证步骤4: 验证市民广场到图书馆的步行路线途经点要求")
    square_search = maps_text_search(square_name, square_city)
    if square_search.error:
        print(f"验证步骤4失败: 搜索市民广场失败 - {square_search.error}")
        all_passed = False
    elif not square_search.pois or len(square_search.pois) == 0:
        print("验证步骤4失败: 未找到市民广场")
        all_passed = False
    else:
        square_poi_id = square_search.pois[0].id
        square_detail = maps_search_detail(square_poi_id)
        if square_detail.error or not square_detail.location:
            print(f"验证步骤4失败: 无法获取市民广场坐标 - {square_detail.error if square_detail.error else '坐标为空'}")
            all_passed = False
        else:
            square_location = square_detail.location
            # 获取市图书馆公交站坐标
            bus_station_search = maps_text_search(bus_station_name, bus_station_city)
            if bus_station_search.error:
                print(f"验证步骤4失败: 搜索市图书馆公交站失败 - {bus_station_search.error}")
                all_passed = False
            elif not bus_station_search.pois or len(bus_station_search.pois) == 0:
                print("验证步骤4失败: 未找到市图书馆公交站")
                all_passed = False
            else:
                bus_station_poi_id = bus_station_search.pois[0].id
                bus_station_detail = maps_search_detail(bus_station_poi_id)
                if bus_station_detail.error or not bus_station_detail.location:
                    print(f"验证步骤4失败: 无法获取市图书馆公交站坐标 - {bus_station_detail.error if bus_station_detail.error else '坐标为空'}")
                    all_passed = False
                else:
                    bus_station_location = bus_station_detail.location
                    # 获取步行路线
                    walking_result = maps_walking_by_coordinates(square_location, library_location)
                    if walking_result.error or not walking_result.steps:
                        print(f"验证步骤4失败: 获取步行路线失败 - {walking_result.error if walking_result.error else 'steps为空'}")
                        all_passed = False
                    else:
                        found_valid_waypoint = False
                        # 遍历所有步骤的 from_coordinates 和 to_coordinates
                        waypoints_checked = set()
                        for step in walking_result.steps:
                            for waypoint_coord in [step.from_coordinates, step.to_coordinates]:
                                if waypoint_coord in waypoints_checked:
                                    continue
                                waypoints_checked.add(waypoint_coord)
                                
                                # 计算到市图书馆公交站的距离
                                waypoint_distance_result = maps_distance(waypoint_coord, bus_station_location)
                                if waypoint_distance_result.error or not waypoint_distance_result.results:
                                    continue
                                waypoint_distance = waypoint_distance_result.results[0].distance_meters
                                
                                # 验证距离要求
                                if waypoint_distance < max_distance_to_bus_station_meters:
                                    # 验证附近200米内是否有咖啡馆
                                    cafe_search_result = maps_around_search(waypoint_coord, cafe_radius, cafe_keywords)
                                    if not cafe_search_result.error and cafe_search_result.pois and len(cafe_search_result.pois) > 0:
                                        found_valid_waypoint = True
                                        print(f"验证步骤4通过: 找到满足条件的途经点 {waypoint_coord}（距离市图书馆公交站 {waypoint_distance} 米 < {max_distance_to_bus_station_meters} 米，附近200米内有咖啡馆）")
                                        break
                            
                            if found_valid_waypoint:
                                break
                        
                        if not found_valid_waypoint:
                            print(f"验证步骤4失败: 未找到满足条件的途经点（距离市图书馆公交站 < {max_distance_to_bus_station_meters} 米且附近200米内有咖啡馆）")
                            all_passed = False
    
    # 验证步骤7: 获取台州西站到图书馆的驾车时间 T1
    print("验证步骤7: 获取台州西站到图书馆的驾车时间 T1")
    train_station_search = maps_text_search(train_station_name, train_station_city)
    if train_station_search.error:
        print(f"验证步骤7失败: 搜索台州西站失败 - {train_station_search.error}")
        all_passed = False
        T1 = None
    elif not train_station_search.pois or len(train_station_search.pois) == 0:
        print("验证步骤7失败: 未找到台州西站")
        all_passed = False
        T1 = None
    else:
        train_station_poi_id = train_station_search.pois[0].id
        train_station_detail = maps_search_detail(train_station_poi_id)
        if train_station_detail.error or not train_station_detail.location:
            print(f"验证步骤7失败: 无法获取台州西站坐标 - {train_station_detail.error if train_station_detail.error else '坐标为空'}")
            all_passed = False
            T1 = None
        else:
            train_station_location = train_station_detail.location
            driving_result = maps_driving_by_coordinates(train_station_location, library_location)
            if driving_result.error or driving_result.total_duration_seconds is None:
                print(f"验证步骤7失败: 获取驾车时间失败 - {driving_result.error if driving_result.error else '时间为空'}")
                all_passed = False
                T1 = None
            else:
                T1 = driving_result.total_duration_seconds
                print(f"验证步骤7通过: 台州西站到图书馆的驾车时间 T1 = {T1} 秒（{T1 // 60} 分钟）")
    
    # 验证步骤8: 获取图书馆到市民广场的步行时间 T2
    print("验证步骤8: 获取图书馆到市民广场的步行时间 T2")
    if 'square_location' not in locals():
        print("验证步骤8失败: 市民广场坐标未获取")
        all_passed = False
        T2 = None
    else:
        walking_result2 = maps_walking_by_coordinates(library_location, square_location)
        if walking_result2.error or walking_result2.total_duration_seconds is None:
            print(f"验证步骤8失败: 获取步行时间失败 - {walking_result2.error if walking_result2.error else '时间为空'}")
            all_passed = False
            T2 = None
        else:
            T2 = walking_result2.total_duration_seconds
            print(f"验证步骤8通过: 图书馆到市民广场的步行时间 T2 = {T2} 秒（{T2 // 60} 分钟）")
    
    # 验证步骤9: 验证 (T1 + T2) ≤ 40 分钟
    print("验证步骤9: 验证 (T1 + T2) ≤ 40 分钟")
    if T1 is None or T2 is None:
        print("验证步骤9失败: T1 或 T2 未获取")
        all_passed = False
    else:
        total_time_seconds = T1 + T2
        total_time_minutes = total_time_seconds // 60
        max_total_time_seconds = max_total_time_minutes * 60
        if total_time_seconds <= max_total_time_seconds:
            print(f"验证步骤9通过: (T1 + T2) = {total_time_seconds} 秒（{total_time_minutes} 分钟） <= {max_total_time_seconds} 秒（{max_total_time_minutes} 分钟）")
        else:
            print(f"验证步骤9失败: (T1 + T2) = {total_time_seconds} 秒（{total_time_minutes} 分钟） > {max_total_time_seconds} 秒（{max_total_time_minutes} 分钟）")
            all_passed = False
    
    # 验证步骤10: 获取图书馆到市图书馆公交站的步行时间 T3，验证 T3 ≤ 10 分钟
    print("验证步骤10: 验证图书馆到市图书馆公交站的步行时间 T3 ≤ 10 分钟")
    if 'bus_station_location' not in locals():
        print("验证步骤10失败: 市图书馆公交站坐标未获取")
        all_passed = False
    else:
        walking_result3 = maps_walking_by_coordinates(library_location, bus_station_location)
        if walking_result3.error or walking_result3.total_duration_seconds is None:
            print(f"验证步骤10失败: 获取步行时间失败 - {walking_result3.error if walking_result3.error else '时间为空'}")
            all_passed = False
        else:
            T3 = walking_result3.total_duration_seconds
            max_walking_to_bus_station_seconds = max_walking_to_bus_station_minutes * 60
            if T3 <= max_walking_to_bus_station_seconds:
                print(f"验证步骤10通过: T3 = {T3} 秒（{T3 // 60} 分钟） <= {max_walking_to_bus_station_seconds} 秒（{max_walking_to_bus_station_minutes} 分钟）")
            else:
                print(f"验证步骤10失败: T3 = {T3} 秒（{T3 // 60} 分钟） > {max_walking_to_bus_station_seconds} 秒（{max_walking_to_bus_station_minutes} 分钟）")
                all_passed = False
    
    # 验证步骤11: 获取市民广场到图书馆的步行时间 T4
    print("验证步骤11: 获取市民广场到图书馆的步行时间 T4")
    if 'square_location' not in locals():
        print("验证步骤11失败: 市民广场坐标未获取")
        all_passed = False
        T4 = None
    else:
        walking_result4 = maps_walking_by_coordinates(square_location, library_location)
        if walking_result4.error or walking_result4.total_duration_seconds is None:
            print(f"验证步骤11失败: 获取步行时间失败 - {walking_result4.error if walking_result4.error else '时间为空'}")
            all_passed = False
            T4 = None
        else:
            T4 = walking_result4.total_duration_seconds
            print(f"验证步骤11通过: 市民广场到图书馆的步行时间 T4 = {T4} 秒（{T4 // 60} 分钟）")
    
    # 验证步骤12: 验证 T1 - T4 > 15 分钟
    print("验证步骤12: 验证 T1 - T4 > 15 分钟")
    if T1 is None or T4 is None:
        print("验证步骤12失败: T1 或 T4 未获取")
        all_passed = False
    else:
        time_difference_seconds = T1 - T4
        time_difference_minutes = time_difference_seconds // 60
        min_time_difference_seconds = min_time_difference_minutes * 60
        if time_difference_seconds > min_time_difference_seconds:
            print(f"验证步骤12通过: T1 - T4 = {time_difference_seconds} 秒（{time_difference_minutes} 分钟） > {min_time_difference_seconds} 秒（{min_time_difference_minutes} 分钟）")
        else:
            print(f"验证步骤12失败: T1 - T4 = {time_difference_seconds} 秒（{time_difference_minutes} 分钟） <= {min_time_difference_seconds} 秒（{min_time_difference_minutes} 分钟）")
            all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")
    return result  


if __name__ == "__main__":
    main()
