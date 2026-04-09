"""
修改任务指令：你想在附近1500米以内找一家自习室，评分要高于4.0。这家自习室不能离西安钟楼的直线距离需要大于500米。你去自习室的路线中的途径点中，存在一个离西北工业大学不到800米的地方。自习室附近1000米要有地铁站，而且到边家村地铁站的步行时间不能超过15分钟。另外，从自习室开车到西安北站的时间不能超过40分钟。你计划从西安北站先到自习室，然后再去机场，整个行程的驾车时间希望不超过90分钟。你善于使用强制和协商的策略来达到目的。
输入：B0I2LUETJL
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('108.922763,34.251579', '自习室', 1500)验证目标自习室在搜索结果中。
2. 调用maps_search_detail('B0I2LUETJL')获取评分，验证≥4.0。
3. 调用maps_text_search('西安钟楼', '西安')获取钟楼poi_id，调用maps_search_detail获取坐标，调用maps_distance计算自习室到钟楼距离，验证>500米。
4. 调用maps_walking_by_coordinates('108.922763,34.251579', '108.919625,34.251273')获取步行路线，取第一个途径点坐标(108.921611,34.248694)，调用maps_text_search('西北工业大学', '西安')获取西北工业大学poi_id，调用maps_search_detail获取坐标，调用maps_distance计算途径点到西北工业大学距离，验证<800米。
5. 调用maps_around_search('108.919625,34.251273', '地铁站', 1000)获取附近1000米的地铁站列表，验证返回列表不为空
6. 调用maps_walking_by_coordinates('108.919625,34.251273', '108.923387,34.241135')计算自习室到边家村地铁站步行时间，验证≤15分钟（900秒）。
7. 调用maps_driving_by_coordinates('108.919625,34.251273', '108.938757,34.376660')计算自习室到西安北站驾车时间，验证≤40分钟（2400秒）。
8. 调用maps_driving_by_coordinates('108.938757,34.376660', '108.919625,34.251273')计算西安北站到自习室驾车时间t1，调用maps_driving_by_coordinates('108.919625,34.251273', '108.768912,34.442341')计算自习室到机场驾车时间t2，验证t1+t2 ≤90分钟（5400秒）。
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
    target_poi_id: str = 'B0I2LUETJL',
    user_location: str = '108.922763,34.251579',
    study_room_keywords: str = '自习室',
    study_room_radius: str = '1500',
    min_rating: float = 4.0,
    bell_tower_keywords: str = '西安钟楼',
    bell_tower_city: str = '西安',
    min_distance_to_bell_tower: int = 500,
    university_keywords: str = '西北工业大学',
    university_city: str = '西安',
    max_distance_to_university: int = 800,
    subway_station_keywords: str = '地铁站',
    subway_station_radius: str = '1000',
    specific_subway_station_keywords: str = '边家村地铁站',
    specific_subway_station_city: str = '西安',
    max_walking_time_to_subway_seconds: int = 900,
    train_station_keywords: str = '西安北站',
    train_station_city: str = '西安',
    max_driving_time_to_train_station_seconds: int = 2400,
    airport_keywords: str = '机场',
    airport_city: str = '西安',
    max_total_driving_time_seconds: int = 5400
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID，默认值为 'B0I2LUETJL'
        user_location: 用户位置坐标，默认值为 '108.922763,34.251579'
        其他参数为验证步骤中需要的参数，使用验证步骤中的值作为默认值
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 调用maps_around_search验证目标自习室在搜索结果中
    print("验证步骤1: 检查目标自习室在用户位置1500米范围内")
    around_result = maps_around_search(user_location, study_room_radius, study_room_keywords)
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
        print("  验证失败: 目标自习室不在搜索结果中")
        all_passed = False
    else:
        print("  验证通过: 目标自习室在搜索结果中")
    
    # 验证步骤2: 调用maps_search_detail获取评分，验证>=4.0
    print("验证步骤2: 验证自习室评分>=4.0")
    study_room_detail = maps_search_detail(target_poi_id)
    if study_room_detail.error or not study_room_detail.location:
        print(f"  验证失败: 无法获取自习室信息 - {study_room_detail.error if study_room_detail.error else '坐标为空'}")
        return False
    
    study_room_location = study_room_detail.location
    print(f"  获取自习室坐标: {study_room_location}")
    
    # 检查评分
    rating = None
    if study_room_detail.biz_ext:
        rating_str = study_room_detail.biz_ext.get('rating', '')
        if rating_str:
            try:
                rating = float(rating_str)
            except ValueError:
                pass
    
    if rating is not None:
        if rating >= min_rating:
            print(f"  验证通过: 自习室评分 {rating} >= {min_rating}")
        else:
            print(f"  验证失败: 自习室评分 {rating} < {min_rating}")
            all_passed = False
    else:
        print("  验证失败: 无法获取评分信息")
        all_passed = False
    
    # 验证步骤3: 验证自习室到钟楼距离>500米
    print("验证步骤3: 验证自习室距离西安钟楼大于500米")
    bell_tower_search = maps_text_search(bell_tower_keywords, bell_tower_city)
    if bell_tower_search.error or not bell_tower_search.pois:
        print(f"  验证失败: 无法搜索到西安钟楼 - {bell_tower_search.error if bell_tower_search.error else '未找到结果'}")
        all_passed = False
    else:
        bell_tower_poi_id = bell_tower_search.pois[0].id
        bell_tower_detail = maps_search_detail(bell_tower_poi_id)
        if bell_tower_detail.error or not bell_tower_detail.location:
            print(f"  验证失败: 无法获取西安钟楼坐标 - {bell_tower_detail.error if bell_tower_detail.error else '坐标为空'}")
            all_passed = False
        else:
            bell_tower_location = bell_tower_detail.location
            distance_result = maps_distance(study_room_location, bell_tower_location)
            if distance_result.error or not distance_result.results:
                print(f"  验证失败: 无法计算距离 - {distance_result.error if distance_result.error else '未找到结果'}")
                all_passed = False
            else:
                distance = distance_result.results[0].distance_meters
                if distance > min_distance_to_bell_tower:
                    print(f"  验证通过: 自习室距离西安钟楼 {distance} 米，大于 {min_distance_to_bell_tower} 米")
                else:
                    print(f"  验证失败: 自习室距离西安钟楼 {distance} 米，不大于 {min_distance_to_bell_tower} 米")
                    all_passed = False
    
    # 验证步骤4: 获取步行路线第一个途径点，验证到西北工业大学距离<800米
    print("验证步骤4: 验证步行路线第一个途径点到西北工业大学距离小于800米")
    walking_route = maps_walking_by_coordinates(user_location, study_room_location)
    if walking_route.error or not walking_route.steps:
        print(f"  验证失败: 无法获取步行路线 - {walking_route.error if walking_route.error else '路线为空'}")
        all_passed = False
        waypoint = None
    else:
        # 取第一个途径点坐标（第一个步骤的终点）
        if len(walking_route.steps) > 0:
            waypoint = walking_route.steps[0].to_coordinates
            print(f"  获取第一个途径点坐标: {waypoint}")
        else:
            print("  验证失败: 步行路线步骤为空，无法提取途径点")
            all_passed = False
            waypoint = None
    
    if waypoint:
        university_search = maps_text_search(university_keywords, university_city)
        if university_search.error or not university_search.pois:
            print(f"  验证失败: 无法搜索到西北工业大学 - {university_search.error if university_search.error else '未找到结果'}")
            all_passed = False
        else:
            university_poi_id = university_search.pois[0].id
            university_detail = maps_search_detail(university_poi_id)
            if university_detail.error or not university_detail.location:
                print(f"  验证失败: 无法获取西北工业大学坐标 - {university_detail.error if university_detail.error else '坐标为空'}")
                all_passed = False
            else:
                university_location = university_detail.location
                waypoint_distance_result = maps_distance(waypoint, university_location)
                if waypoint_distance_result.error or not waypoint_distance_result.results:
                    print(f"  验证失败: 无法计算距离 - {waypoint_distance_result.error if waypoint_distance_result.error else '未找到结果'}")
                    all_passed = False
                else:
                    waypoint_distance = waypoint_distance_result.results[0].distance_meters
                    if waypoint_distance < max_distance_to_university:
                        print(f"  验证通过: 途径点到西北工业大学距离 {waypoint_distance} 米，小于 {max_distance_to_university} 米")
                    else:
                        print(f"  验证失败: 途径点到西北工业大学距离 {waypoint_distance} 米，不小于 {max_distance_to_university} 米")
                        all_passed = False
    
    # 验证步骤5: 验证自习室附近1000米有地铁站
    print("验证步骤5: 验证自习室附近1000米有地铁站")
    subway_around_result = maps_around_search(study_room_location, subway_station_radius, subway_station_keywords)
    if subway_around_result.error:
        print(f"  验证失败: {subway_around_result.error}")
        all_passed = False
    else:
        if subway_around_result.pois and len(subway_around_result.pois) > 0:
            print(f"  验证通过: 自习室附近1000米有地铁站，找到 {len(subway_around_result.pois)} 个")
        else:
            print("  验证失败: 自习室附近1000米没有地铁站")
            all_passed = False
    
    # 验证步骤6: 验证自习室到边家村地铁站步行时间<=900秒
    print("验证步骤6: 验证自习室到边家村地铁站步行时间不超过900秒")
    subway_station_search = maps_text_search(specific_subway_station_keywords, specific_subway_station_city)
    if subway_station_search.error or not subway_station_search.pois:
        print(f"  验证失败: 无法搜索到边家村地铁站 - {subway_station_search.error if subway_station_search.error else '未找到结果'}")
        all_passed = False
    else:
        subway_station_poi_id = subway_station_search.pois[0].id
        subway_station_detail = maps_search_detail(subway_station_poi_id)
        if subway_station_detail.error or not subway_station_detail.location:
            print(f"  验证失败: 无法获取边家村地铁站坐标 - {subway_station_detail.error if subway_station_detail.error else '坐标为空'}")
            all_passed = False
        else:
            subway_station_location = subway_station_detail.location
            walking_route_to_subway = maps_walking_by_coordinates(study_room_location, subway_station_location)
            if walking_route_to_subway.error:
                print(f"  验证失败: 无法获取步行路线时间 - {walking_route_to_subway.error}")
                all_passed = False
            else:
                walking_time = walking_route_to_subway.total_duration_seconds if walking_route_to_subway.total_duration_seconds else 0
                if walking_time <= max_walking_time_to_subway_seconds:
                    print(f"  验证通过: 步行时间 {walking_time} 秒，不超过 {max_walking_time_to_subway_seconds} 秒")
                else:
                    print(f"  验证失败: 步行时间 {walking_time} 秒，超过 {max_walking_time_to_subway_seconds} 秒")
                    all_passed = False
    
    # 验证步骤7: 验证自习室到西安北站驾车时间<=2400秒
    print("验证步骤7: 验证自习室到西安北站驾车时间不超过2400秒")
    train_station_search = maps_text_search(train_station_keywords, train_station_city)
    if train_station_search.error or not train_station_search.pois:
        print(f"  验证失败: 无法搜索到西安北站 - {train_station_search.error if train_station_search.error else '未找到结果'}")
        all_passed = False
        train_station_location = None
    else:
        train_station_poi_id = train_station_search.pois[0].id
        train_station_detail = maps_search_detail(train_station_poi_id)
        if train_station_detail.error or not train_station_detail.location:
            print(f"  验证失败: 无法获取西安北站坐标 - {train_station_detail.error if train_station_detail.error else '坐标为空'}")
            all_passed = False
            train_station_location = None
        else:
            train_station_location = train_station_detail.location
            print(f"  获取西安北站坐标: {train_station_location}")
    
    if train_station_location:
        driving_route_to_train = maps_driving_by_coordinates(study_room_location, train_station_location)
        if driving_route_to_train.error:
            print(f"  验证失败: 无法获取驾车路线时间 - {driving_route_to_train.error}")
            all_passed = False
        else:
            driving_time = driving_route_to_train.total_duration_seconds if driving_route_to_train.total_duration_seconds else 0
            if driving_time <= max_driving_time_to_train_station_seconds:
                print(f"  验证通过: 驾车时间 {driving_time} 秒，不超过 {max_driving_time_to_train_station_seconds} 秒")
            else:
                print(f"  验证失败: 驾车时间 {driving_time} 秒，超过 {max_driving_time_to_train_station_seconds} 秒")
                all_passed = False
    
    # 验证步骤8: 验证西安北站->自习室->机场的总时间<=5400秒
    if train_station_location:
        print("验证步骤8: 验证从西安北站到自习室再到机场的总时间不超过5400秒")
        airport_search = maps_text_search(airport_keywords, airport_city)
        if airport_search.error or not airport_search.pois:
            print(f"  验证失败: 无法搜索到机场 - {airport_search.error if airport_search.error else '未找到结果'}")
            all_passed = False
        else:
            airport_poi_id = airport_search.pois[0].id
            airport_detail = maps_search_detail(airport_poi_id)
            if airport_detail.error or not airport_detail.location:
                print(f"  验证失败: 无法获取机场坐标 - {airport_detail.error if airport_detail.error else '坐标为空'}")
                all_passed = False
            else:
                airport_location = airport_detail.location
                print(f"  获取机场坐标: {airport_location}")
                
                # 获取西安北站到自习室的驾车时间t1
                route1 = maps_driving_by_coordinates(train_station_location, study_room_location)
                # 获取自习室到机场的驾车时间t2
                route2 = maps_driving_by_coordinates(study_room_location, airport_location)
                
                if route1.error or route2.error:
                    print(f"  验证失败: 无法获取路线时间 - {route1.error if route1.error else route2.error}")
                    all_passed = False
                else:
                    t1 = route1.total_duration_seconds if route1.total_duration_seconds else 0
                    t2 = route2.total_duration_seconds if route2.total_duration_seconds else 0
                    total_time = t1 + t2
                    if total_time <= max_total_driving_time_seconds:
                        print(f"  验证通过: 总时间 {total_time} 秒，不超过 {max_total_driving_time_seconds} 秒")
                    else:
                        print(f"  验证失败: 总时间 {total_time} 秒，超过 {max_total_driving_time_seconds} 秒")
                        all_passed = False
    else:
        print("  验证失败: 无法获取西安北站坐标，跳过步骤8")
        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
