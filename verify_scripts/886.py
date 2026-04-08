"""
修改任务指令：你想在附近1500米内找一家酒吧，评分要高于4.2分。你不想找离济宁市博物馆太近的酒吧，希望酒吧与博物馆的直线距离要大于500米。你开车从家去酒吧的路线中，需要至少存在一个途径点满足离深科广场的直线距离不能超过300米。你计划之后去济宁站接人，所以从家到酒吧再到济宁站的总时间不能超过15分钟。另外，你希望酒吧到和欣家园公交站的步行时间在10分钟以内。最后，你两个朋友分别从济宁市第一人民医院总院区和济宁市人民政府出发，一个开车一个走路，他们到酒吧的时间差要大于5分钟。你健谈外向，乐观，乐于合作。
输入：B0G3TUO5AB
输出：bool值（True表示验证通过，False表示验证失败）
验证方法：
1. 调用 maps_search_detail('B0G3TUO5AB') 获取酒吧评分，验证 rating > 4.2
2. 调用 maps_around_search('116.573083,35.397125', '酒吧', 1500) 验证目标酒吧在搜索范围内
3. 调用 maps_distance('116.573083,35.397125', '116.576389,35.404459') 验证直线距离 ≤ 1500米
4. 调用 maps_distance('116.576389,35.404459', '116.581734,35.410706') 验证酒吧到济宁市博物馆距离 > 500米
5. 调用 maps_driving_by_coordinates('116.573083,35.397125', '116.576389,35.404459') 获取驾车路线步骤，遍历这些步骤，逐个调用 maps_distance('116.578485,35.400549', 途径点坐标) 验证到深科广场直线距离 ≤ 300米
6. 调用 maps_driving_by_coordinates('116.573083,35.397125', '116.576389,35.404459') 获取第一段行程时间 t1，调用 maps_driving_by_coordinates('116.576389,35.404459', '116.600756,35.392521') 获取第二段行程时间 t2，验证 t1 + t2 ≤ 900秒 (15分钟)
7. 调用 maps_walking_by_coordinates('116.576389,35.404459', '116.573416,35.401506') 获取酒吧到和欣家园公交站的步行时间，验证 ≤ 600秒 (10分钟)
8. 调用 maps_driving_by_coordinates('116.593269,35.398729', '116.576389,35.404459') 获取人民医院到酒吧驾车时间 t3，调用 maps_walking_by_coordinates('116.587116,35.415117', '116.576389,35.404459') 获取市政府到酒吧步行时间 t4，验证 |t3 - t4| > 300秒 (5分钟)
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
    target_poi_id: str = 'B0G3TUO5AB',
    user_location: str = '116.573083,35.397125',
    search_keywords: str = '酒吧',
    search_radius: str = '1500',
    min_rating: float = 4.2,
    max_distance_to_user_meters: int = 1500,
    museum_keywords: str = '济宁市博物馆',
    museum_city: str = '济宁',
    min_distance_to_museum_meters: int = 500,
    shenke_keywords: str = '深科广场',
    shenke_city: str = '济宁',
    max_distance_to_shenke_meters: int = 300,
    train_station_keywords: str = '济宁站',
    train_station_city: str = '济宁',
    max_total_driving_seconds: int = 900,
    bus_station_keywords: str = '和欣家园公交站',
    bus_station_city: str = '济宁',
    max_walking_seconds: int = 600,
    hospital_keywords: str = '济宁市第一人民医院总院区',
    hospital_city: str = '济宁',
    government_keywords: str = '济宁市人民政府',
    government_city: str = '济宁',
    min_time_diff_seconds: int = 300
) -> bool:
    """
    验证POI是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID
        user_location: 用户位置坐标（写死）
        search_keywords: 搜索关键词
        search_radius: 搜索半径（米）
        min_rating: 最小评分
        max_distance_to_user_meters: 到用户位置的最大距离（米）
        museum_keywords: 博物馆搜索关键词
        museum_city: 博物馆搜索城市
        min_distance_to_museum_meters: 到博物馆的最小距离（米）
        shenke_keywords: 深科广场搜索关键词
        shenke_city: 深科广场搜索城市
        max_distance_to_shenke_meters: 到深科广场的最大距离（米）
        train_station_keywords: 火车站搜索关键词
        train_station_city: 火车站搜索城市
        max_total_driving_seconds: 最大总驾车时间（秒）
        bus_station_keywords: 公交站搜索关键词
        bus_station_city: 公交站搜索城市
        max_walking_seconds: 最大步行时间（秒）
        hospital_keywords: 医院搜索关键词
        hospital_city: 医院搜索城市
        government_keywords: 市政府搜索关键词
        government_city: 市政府搜索城市
        min_time_diff_seconds: 最小时间差（秒）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 获取酒吧评分，验证 rating > 4.2
    print("验证步骤1: 验证评分 > 4.2...")
    detail_result = maps_search_detail(target_poi_id)
    if detail_result.error:
        print(f"  验证失败: {detail_result.error}")
        all_passed = False
        target_poi_location = None
    else:
        # 获取目标POI坐标，后续步骤需要用到
        target_poi_location = detail_result.location
        if not target_poi_location:
            print("  验证失败: 无法获取目标酒吧坐标")
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
    
    # 验证步骤2: 验证目标酒吧在搜索范围内
    print("验证步骤2: 验证目标酒吧在搜索范围内...")
    around_result = maps_around_search(user_location, search_radius, search_keywords)
    if around_result.error:
        print(f"  验证失败: {around_result.error}")
        all_passed = False
    elif around_result.pois:
        poi_ids = [poi.id for poi in around_result.pois]
        if target_poi_id in poi_ids:
            print(f"  验证通过: 目标酒吧 {target_poi_id} 在搜索结果中")
        else:
            print(f"  验证失败: 目标酒吧 {target_poi_id} 不在搜索结果中")
            all_passed = False
    else:
        print("  验证失败: 搜索结果为空")
        all_passed = False
    
    # 验证步骤3: 验证用户位置到酒吧的直线距离 <= 1500米
    print("验证步骤3: 验证用户位置到酒吧的直线距离 <= 1500米...")
    if not target_poi_location:
        print("  验证失败: 目标酒吧坐标未获取")
        all_passed = False
    else:
        distance_result = maps_distance(user_location, target_poi_location)
        if distance_result.error or not distance_result.results:
            print(f"  验证失败: 计算距离失败 - {distance_result.error if distance_result.error else '结果为空'}")
            all_passed = False
        else:
            distance = distance_result.results[0].distance_meters
            if distance <= max_distance_to_user_meters:
                print(f"  验证通过: 距离 {distance} 米 <= {max_distance_to_user_meters} 米")
            else:
                print(f"  验证失败: 距离 {distance} 米 > {max_distance_to_user_meters} 米")
                all_passed = False
    
    # 验证步骤4: 验证酒吧到济宁市博物馆距离 > 500米
    print("验证步骤4: 验证酒吧到济宁市博物馆距离 > 500米...")
    if not target_poi_location:
        print("  验证失败: 目标酒吧坐标未获取")
        all_passed = False
    else:
        museum_search_result = maps_text_search(museum_keywords, museum_city)
        if museum_search_result.error:
            print(f"  验证失败: 搜索博物馆失败 - {museum_search_result.error}")
            all_passed = False
        elif not museum_search_result.pois or len(museum_search_result.pois) == 0:
            print("  验证失败: 未找到博物馆 POI")
            all_passed = False
        else:
            museum_poi_id = museum_search_result.pois[0].id
            museum_detail = maps_search_detail(museum_poi_id)
            if museum_detail.error or not museum_detail.location:
                print(f"  验证失败: 无法获取博物馆坐标 - {museum_detail.error if museum_detail.error else '坐标为空'}")
                all_passed = False
            else:
                museum_location = museum_detail.location
                distance_result = maps_distance(target_poi_location, museum_location)
                if distance_result.error or not distance_result.results:
                    print(f"  验证失败: 计算距离失败 - {distance_result.error if distance_result.error else '结果为空'}")
                    all_passed = False
                else:
                    distance = distance_result.results[0].distance_meters
                    if distance > min_distance_to_museum_meters:
                        print(f"  验证通过: 距离 {distance} 米 > {min_distance_to_museum_meters} 米")
                    else:
                        print(f"  验证失败: 距离 {distance} 米 <= {min_distance_to_museum_meters} 米")
                        all_passed = False
    
    # 验证步骤5: 验证驾车路线途经点中至少有一个点距离深科广场 <= 300米
    print("验证步骤5: 验证驾车路线途经点中至少有一个点距离深科广场 <= 300米...")
    if not target_poi_location:
        print("  验证失败: 目标酒吧坐标未获取")
        all_passed = False
    else:
        # 先搜索深科广场
        shenke_search_result = maps_text_search(shenke_keywords, shenke_city)
        if shenke_search_result.error:
            print(f"  验证失败: 搜索深科广场失败 - {shenke_search_result.error}")
            all_passed = False
        elif not shenke_search_result.pois or len(shenke_search_result.pois) == 0:
            print("  验证失败: 未找到深科广场 POI")
            all_passed = False
        else:
            shenke_poi_id = shenke_search_result.pois[0].id
            shenke_detail = maps_search_detail(shenke_poi_id)
            if shenke_detail.error or not shenke_detail.location:
                print(f"  验证失败: 无法获取深科广场坐标 - {shenke_detail.error if shenke_detail.error else '坐标为空'}")
                all_passed = False
            else:
                shenke_location = shenke_detail.location
                # 获取驾车路线
                driving_result = maps_driving_by_coordinates(user_location, target_poi_location)
                if driving_result.error or not driving_result.steps:
                    print(f"  验证失败: 获取驾车路线失败 - {driving_result.error if driving_result.error else 'steps为空'}")
                    all_passed = False
                else:
                    found_nearby_point = False
                    # 遍历steps，对from_coordinates 和 to_coordinates（不包括起点和终点）
                    all_coords = set()
                    for i, step in enumerate(driving_result.steps):
                        # 不包括起点和终点
                        if i > 0:  # from_coordinates 不是起点
                            all_coords.add(step.from_coordinates)
                        if i < len(driving_result.steps) - 1:  # to_coordinates 不是终点
                            all_coords.add(step.to_coordinates)
                    
                    for coord in all_coords:
                        distance_result = maps_distance(shenke_location, coord)
                        if not distance_result.error and distance_result.results:
                            distance = distance_result.results[0].distance_meters
                            if distance <= max_distance_to_shenke_meters:
                                found_nearby_point = True
                                print(f"  验证通过: 找到途经点 {coord} 距离深科广场 {distance} 米 <= {max_distance_to_shenke_meters} 米")
                                break
                    
                    if not found_nearby_point:
                        print("  验证失败: 未找到距离深科广场 <= 300米的途经点")
                        all_passed = False
    
    # 验证步骤6: 验证从用户位置到酒吧再到济宁站的总时间 <= 900秒（15分钟）
    print("验证步骤6: 验证从用户位置到酒吧再到济宁站的总时间 <= 900秒（15分钟）...")
    if not target_poi_location:
        print("  验证失败: 目标酒吧坐标未获取")
        all_passed = False
    else:
        # 搜索济宁站
        train_station_search = maps_text_search(train_station_keywords, train_station_city)
        if train_station_search.error or not train_station_search.pois or len(train_station_search.pois) == 0:
            print(f"  验证失败: 搜索火车站失败 - {train_station_search.error if train_station_search.error else '未找到火车站'}")
            all_passed = False
        else:
            train_station_poi_id = train_station_search.pois[0].id
            train_station_detail = maps_search_detail(train_station_poi_id)
            if train_station_detail.error or not train_station_detail.location:
                print(f"  验证失败: 获取火车站坐标失败 - {train_station_detail.error if train_station_detail.error else '坐标为空'}")
                all_passed = False
            else:
                train_station_location = train_station_detail.location
                # 计算用户位置到酒吧的驾车时间 t1
                route1 = maps_driving_by_coordinates(user_location, target_poi_location)
                if route1.error or route1.total_duration_seconds is None:
                    print(f"  验证失败: 计算用户位置到酒吧的驾车时间失败 - {route1.error if route1.error else '时间为空'}")
                    all_passed = False
                else:
                    t1 = route1.total_duration_seconds
                    # 计算酒吧到火车站的驾车时间 t2
                    route2 = maps_driving_by_coordinates(target_poi_location, train_station_location)
                    if route2.error or route2.total_duration_seconds is None:
                        print(f"  验证失败: 计算酒吧到火车站的驾车时间失败 - {route2.error if route2.error else '时间为空'}")
                        all_passed = False
                    else:
                        t2 = route2.total_duration_seconds
                        total_time = t1 + t2
                        if total_time <= max_total_driving_seconds:
                            print(f"  验证通过: 总时间 {total_time} 秒 <= {max_total_driving_seconds} 秒 (t1={t1}秒, t2={t2}秒)")
                        else:
                            print(f"  验证失败: 总时间 {total_time} 秒 > {max_total_driving_seconds} 秒 (t1={t1}秒, t2={t2}秒)")
                            all_passed = False
    
    # 验证步骤7: 验证酒吧到和欣家园公交站的步行时间 <= 600秒（10分钟）
    print("验证步骤7: 验证酒吧到和欣家园公交站的步行时间 <= 600秒（10分钟）...")
    if not target_poi_location:
        print("  验证失败: 目标酒吧坐标未获取")
        all_passed = False
    else:
        # 搜索和欣家园公交站
        bus_station_search = maps_text_search(bus_station_keywords, bus_station_city)
        if bus_station_search.error or not bus_station_search.pois or len(bus_station_search.pois) == 0:
            print(f"  验证失败: 搜索公交站失败 - {bus_station_search.error if bus_station_search.error else '未找到公交站'}")
            all_passed = False
        else:
            bus_station_poi_id = bus_station_search.pois[0].id
            bus_station_detail = maps_search_detail(bus_station_poi_id)
            if bus_station_detail.error or not bus_station_detail.location:
                print(f"  验证失败: 获取公交站坐标失败 - {bus_station_detail.error if bus_station_detail.error else '坐标为空'}")
                all_passed = False
            else:
                bus_station_location = bus_station_detail.location
                walking_result = maps_walking_by_coordinates(target_poi_location, bus_station_location)
                if walking_result.error or walking_result.total_duration_seconds is None:
                    print(f"  验证失败: 计算步行时间失败 - {walking_result.error if walking_result.error else '时间为空'}")
                    all_passed = False
                else:
                    walking_time = walking_result.total_duration_seconds
                    if walking_time <= max_walking_seconds:
                        print(f"  验证通过: 步行时间 {walking_time} 秒 <= {max_walking_seconds} 秒")
                    else:
                        print(f"  验证失败: 步行时间 {walking_time} 秒 > {max_walking_seconds} 秒")
                        all_passed = False
    
    # 验证步骤8: 验证人民医院到酒吧驾车时间与市政府到酒吧步行时间的差值 > 300秒（5分钟）
    print("验证步骤8: 验证人民医院到酒吧驾车时间与市政府到酒吧步行时间的差值 > 300秒（5分钟）...")
    if not target_poi_location:
        print("  验证失败: 目标酒吧坐标未获取")
        all_passed = False
    else:
        # 搜索济宁市第一人民医院总院区
        hospital_search = maps_text_search(hospital_keywords, hospital_city)
        if hospital_search.error or not hospital_search.pois or len(hospital_search.pois) == 0:
            print(f"  验证失败: 搜索医院失败 - {hospital_search.error if hospital_search.error else '未找到医院'}")
            all_passed = False
        else:
            hospital_poi_id = hospital_search.pois[0].id
            hospital_detail = maps_search_detail(hospital_poi_id)
            if hospital_detail.error or not hospital_detail.location:
                print(f"  验证失败: 获取医院坐标失败 - {hospital_detail.error if hospital_detail.error else '坐标为空'}")
                all_passed = False
            else:
                hospital_location = hospital_detail.location
                # 搜索济宁市人民政府
                government_search = maps_text_search(government_keywords, government_city)
                if government_search.error or not government_search.pois or len(government_search.pois) == 0:
                    print(f"  验证失败: 搜索市政府失败 - {government_search.error if government_search.error else '未找到市政府'}")
                    all_passed = False
                else:
                    government_poi_id = government_search.pois[0].id
                    government_detail = maps_search_detail(government_poi_id)
                    if government_detail.error or not government_detail.location:
                        print(f"  验证失败: 获取市政府坐标失败 - {government_detail.error if government_detail.error else '坐标为空'}")
                        all_passed = False
                    else:
                        government_location = government_detail.location
                        # 计算人民医院到酒吧的驾车时间 t3
                        route3 = maps_driving_by_coordinates(hospital_location, target_poi_location)
                        if route3.error or route3.total_duration_seconds is None:
                            print(f"  验证失败: 计算医院到酒吧的驾车时间失败 - {route3.error if route3.error else '时间为空'}")
                            all_passed = False
                        else:
                            t3 = route3.total_duration_seconds
                            # 计算市政府到酒吧的步行时间 t4
                            route4 = maps_walking_by_coordinates(government_location, target_poi_location)
                            if route4.error or route4.total_duration_seconds is None:
                                print(f"  验证失败: 计算市政府到酒吧的步行时间失败 - {route4.error if route4.error else '时间为空'}")
                                all_passed = False
                            else:
                                t4 = route4.total_duration_seconds
                                time_diff = abs(t3 - t4)
                                if time_diff > min_time_diff_seconds:
                                    print(f"  验证通过: 时间差 {time_diff} 秒 > {min_time_diff_seconds} 秒 (t3={t3}秒, t4={t4}秒)")
                                else:
                                    print(f"  验证失败: 时间差 {time_diff} 秒 <= {min_time_diff_seconds} 秒 (t3={t3}秒, t4={t4}秒)")
                                    all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
