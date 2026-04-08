"""
修改任务指令：你想在附近2000米内找一个博物馆，评分至少4.6。博物馆附近1500米内至少有个公交站满足步行过去不能超过1000米。你从家开车去博物馆的路线上的途径点中，需要至少存在一个途径点满足离快活林公交站直线距离要小于700米。博物馆离潘家大楼公交站的直线距离要小于300米，而且从博物馆步行到潘家大楼公交站不能超过10分钟。另外，你计划从济宁站出发，先去博物馆，再到济宁汽车北站，整个行程开车时间不能超过10分钟。你虽然心情不好，但仍然保持礼貌和独立的姿态。
输入：B021905525
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_search_detail('B021905525')获取博物馆评分，验证≥4.6
2. 调用maps_around_search('116.576351,35.406064', '博物馆', 2000)验证目标博物馆在搜索范围内
3. 调用maps_around_search('116.581734,35.410706', '公交站', 1500)获取博物馆附近公交站列表，对每个公交站调用maps_walking_by_coordinates计算步行距离，验证至少有一个公交站步行距离≤1000米（例如潘家大楼公交站）
4. 调用maps_driving_by_coordinates('116.576351,35.406064', '116.581734,35.410706')获取驾车步骤，遍历这些步骤，调用maps_distance计算各点到快活林公交站('116.575152,35.405247')的直线距离，验证至少存在一个途径点满足离快活林公交站直线距离要小于700米
5. 调用maps_distance计算博物馆('116.581734,35.410706')到潘家大楼公交站('116.580903,35.412635')的直线距离，验证<300米
6. 调用maps_walking_by_coordinates计算博物馆到潘家大楼公交站的步行时间，验证≤600秒（10分钟）
7. 调用maps_text_search('济宁站', '济宁')获取济宁站poi_id，maps_search_detail获取坐标；调用maps_text_search('济宁汽车北站', '济宁')获取汽车北站poi_id，maps_search_detail获取坐标；调用maps_driving_by_coordinates计算济宁站到博物馆的驾车时间t1，博物馆到汽车北站的驾车时间t2，验证t1+t2≤600秒（10分钟）
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
    target_poi_id: str = 'B021905525',
    user_location: str = '116.576351,35.406064',
    search_keywords: str = '博物馆',
    search_radius: str = '2000',
    bus_station_keywords: str = '公交站',
    bus_station_radius: str = '1500',
    min_rating: float = 4.6,
    max_walking_distance_meters: int = 1000,
    kuaihuolin_bus_station_keywords: str = '快活林公交站',
    kuaihuolin_city: str = '济宁',
    max_distance_to_kuaihuolin_meters: int = 700,
    panjiadlou_bus_station_keywords: str = '潘家大楼公交站',
    max_distance_to_panjiadlou_meters: int = 300,
    max_walking_time_seconds: int = 600,
    train_station_keywords: str = '济宁站',
    train_station_city: str = '济宁',
    bus_station_north_keywords: str = '济宁汽车北站',
    max_total_driving_time_seconds: int = 600
) -> bool:
    """
    验证POI是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID
        user_location: 用户位置坐标
        search_keywords: 搜索关键词
        search_radius: 搜索半径（米）
        bus_station_keywords: 公交站搜索关键词
        bus_station_radius: 公交站搜索半径（米）
        min_rating: 最小评分
        max_walking_distance_meters: 最大步行距离（米）
        kuaihuolin_bus_station_keywords: 快活林公交站搜索关键词
        kuaihuolin_city: 快活林公交站搜索城市
        max_distance_to_kuaihuolin_meters: 到快活林公交站的最大距离（米）
        panjiadlou_bus_station_keywords: 潘家大楼公交站搜索关键词
        max_distance_to_panjiadlou_meters: 到潘家大楼公交站的最大距离（米）
        max_walking_time_seconds: 最大步行时间（秒）
        train_station_keywords: 火车站搜索关键词
        train_station_city: 火车站搜索城市
        bus_station_north_keywords: 汽车北站搜索关键词
        max_total_driving_time_seconds: 最大总驾车时间（秒）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 获取博物馆评分，验证 >= 4.6
    print("验证步骤1: 验证评分 >= 4.6...")
    detail_result = maps_search_detail(target_poi_id)
    if detail_result.error:
        print(f"  验证失败: {detail_result.error}")
        all_passed = False
        target_poi_location = None
    else:
        # 获取目标POI坐标，后续步骤需要用到
        target_poi_location = detail_result.location
        if not target_poi_location:
            print("  验证失败: 无法获取目标博物馆坐标")
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
                if rating >= min_rating:
                    print(f"  验证通过: 评分 {rating} >= {min_rating}")
                else:
                    print(f"  验证失败: 评分 {rating} < {min_rating}")
                    all_passed = False
            else:
                print("  验证失败: 无法获取评分信息")
                all_passed = False
    
    # 验证步骤2: 验证目标博物馆在搜索范围内
    print("验证步骤2: 验证目标博物馆在搜索范围内...")
    around_result = maps_around_search(user_location, search_radius, search_keywords)
    if around_result.error:
        print(f"  验证失败: {around_result.error}")
        all_passed = False
    elif around_result.pois:
        poi_ids = [poi.id for poi in around_result.pois]
        if target_poi_id in poi_ids:
            print(f"  验证通过: 目标博物馆 {target_poi_id} 在搜索结果中")
        else:
            print(f"  验证失败: 目标博物馆 {target_poi_id} 不在搜索结果中")
            all_passed = False
    else:
        print("  验证失败: 搜索结果为空")
        all_passed = False
    
    # 验证步骤3: 获取博物馆附近公交站列表，验证至少有一个公交站步行距离 <= 1000米
    print("验证步骤3: 验证至少有一个公交站步行距离 <= 1000米...")
    if not target_poi_location:
        print("  验证失败: 目标博物馆坐标未获取")
        all_passed = False
        bus_stations = []
    else:
        bus_around_result = maps_around_search(target_poi_location, bus_station_radius, bus_station_keywords)
        if bus_around_result.error:
            print(f"  验证失败: {bus_around_result.error}")
            all_passed = False
            bus_stations = []
        elif bus_around_result.pois and len(bus_around_result.pois) > 0:
            bus_stations = bus_around_result.pois
            found_valid_bus_station = False
            for bus_station in bus_stations:
                if bus_station.location:
                    walking_result = maps_walking_by_coordinates(target_poi_location, bus_station.location)
                    if not walking_result.error and walking_result.total_distance_meters is not None:
                        distance = walking_result.total_distance_meters
                        if distance <= max_walking_distance_meters:
                            found_valid_bus_station = True
                            print(f"  验证通过: 找到公交站 {bus_station.name} 步行距离 {distance} 米 <= {max_walking_distance_meters} 米")
                            break
            
            if not found_valid_bus_station:
                print(f"  验证失败: 未找到步行距离 <= {max_walking_distance_meters} 米的公交站")
                all_passed = False
        else:
            print("  验证失败: 未找到公交站")
            all_passed = False
            bus_stations = []
    
    # 验证步骤4: 验证驾车路线途经点中至少有一个点距离快活林公交站 < 200米
    print("验证步骤4: 验证驾车路线途经点中至少有一个点距离快活林公交站 < 200米...")
    if not target_poi_location:
        print("  验证失败: 目标博物馆坐标未获取")
        all_passed = False
    else:
        # 先搜索快活林公交站
        kuaihuolin_search = maps_text_search(kuaihuolin_bus_station_keywords, kuaihuolin_city)
        if kuaihuolin_search.error or not kuaihuolin_search.pois or len(kuaihuolin_search.pois) == 0:
            print(f"  验证失败: 搜索快活林公交站失败 - {kuaihuolin_search.error if kuaihuolin_search.error else '未找到快活林公交站'}")
            all_passed = False
        else:
            kuaihuolin_poi_id = kuaihuolin_search.pois[0].id
            kuaihuolin_detail = maps_search_detail(kuaihuolin_poi_id)
            if kuaihuolin_detail.error or not kuaihuolin_detail.location:
                print(f"  验证失败: 获取快活林公交站坐标失败 - {kuaihuolin_detail.error if kuaihuolin_detail.error else '坐标为空'}")
                all_passed = False
            else:
                kuaihuolin_location = kuaihuolin_detail.location
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
                        distance_result = maps_distance(coord, kuaihuolin_location)
                        if not distance_result.error and distance_result.results:
                            distance = distance_result.results[0].distance_meters
                            if distance < max_distance_to_kuaihuolin_meters:
                                found_nearby_point = True
                                print(f"  验证通过: 找到途经点 {coord} 距离快活林公交站 {distance} 米 < {max_distance_to_kuaihuolin_meters} 米")
                                break
                            # else:
                            #     print(f" 途经点 {coord} 距离快活林公交站 {distance} 米 >= {max_distance_to_kuaihuolin_meters} 米")
                                
                        
                    
                    if not found_nearby_point:
                        print(f"  验证失败: 未找到距离快活林公交站 < {max_distance_to_kuaihuolin_meters} 米的途经点")
                        all_passed = False
    
    # 验证步骤5: 计算博物馆到潘家大楼公交站的直线距离，验证 < 300米
    print("验证步骤5: 验证博物馆到潘家大楼公交站的直线距离 < 300米...")
    if not target_poi_location:
        print("  验证失败: 目标博物馆坐标未获取")
        all_passed = False
        panjiadlou_location = None
    else:
        # 从公交站列表中查找潘家大楼公交站，如果没找到则搜索
        panjiadlou_location = None
        if bus_stations:
            for bus_station in bus_stations:
                if panjiadlou_bus_station_keywords in bus_station.name and bus_station.location:
                    panjiadlou_location = bus_station.location
                    break
        
        # 如果没找到，使用文本搜索
        if not panjiadlou_location:
            panjiadlou_search = maps_text_search(panjiadlou_bus_station_keywords, train_station_city)
            if panjiadlou_search.error or not panjiadlou_search.pois or len(panjiadlou_search.pois) == 0:
                print(f"  验证失败: 搜索潘家大楼公交站失败 - {panjiadlou_search.error if panjiadlou_search.error else '未找到潘家大楼公交站'}")
                all_passed = False
            else:
                panjiadlou_poi_id = panjiadlou_search.pois[0].id
                panjiadlou_detail = maps_search_detail(panjiadlou_poi_id)
                if panjiadlou_detail.error or not panjiadlou_detail.location:
                    print(f"  验证失败: 获取潘家大楼公交站坐标失败 - {panjiadlou_detail.error if panjiadlou_detail.error else '坐标为空'}")
                    all_passed = False
                else:
                    panjiadlou_location = panjiadlou_detail.location
        
        if panjiadlou_location:
            distance_result = maps_distance(target_poi_location, panjiadlou_location)
            if distance_result.error or not distance_result.results:
                print(f"  验证失败: 计算距离失败 - {distance_result.error if distance_result.error else '结果为空'}")
                all_passed = False
            else:
                distance = distance_result.results[0].distance_meters
                if distance < max_distance_to_panjiadlou_meters:
                    print(f"  验证通过: 距离 {distance} 米 < {max_distance_to_panjiadlou_meters} 米")
                else:
                    print(f"  验证失败: 距离 {distance} 米 >= {max_distance_to_panjiadlou_meters} 米")
                    all_passed = False
    
    # 验证步骤6: 计算博物馆到潘家大楼公交站的步行时间，验证 <= 600秒
    print("验证步骤6: 验证博物馆到潘家大楼公交站的步行时间 <= 600秒...")
    if not target_poi_location:
        print("  验证失败: 目标博物馆坐标未获取")
        all_passed = False
    elif not panjiadlou_location:
        print("  验证失败: 潘家大楼公交站坐标未获取")
        all_passed = False
    else:
        walking_result = maps_walking_by_coordinates(target_poi_location, panjiadlou_location)
        if walking_result.error or walking_result.total_duration_seconds is None:
            print(f"  验证失败: 计算步行时间失败 - {walking_result.error if walking_result.error else '时间为空'}")
            all_passed = False
        else:
            walking_time = walking_result.total_duration_seconds
            if walking_time <= max_walking_time_seconds:
                print(f"  验证通过: 步行时间 {walking_time} 秒 <= {max_walking_time_seconds} 秒")
            else:
                print(f"  验证失败: 步行时间 {walking_time} 秒 > {max_walking_time_seconds} 秒")
                all_passed = False
    
    # 验证步骤7: 计算济宁站到博物馆再到汽车北站的总驾车时间，验证 <= 600秒
    print("验证步骤7: 验证总驾车时间 <= 600秒（10分钟）...")
    if not target_poi_location:
        print("  验证失败: 目标博物馆坐标未获取")
        all_passed = False
    else:
        # 搜索济宁站
        train_station_search = maps_text_search(train_station_keywords, train_station_city)
        if train_station_search.error or not train_station_search.pois or len(train_station_search.pois) == 0:
            print(f"  验证失败: 搜索济宁站失败 - {train_station_search.error if train_station_search.error else '未找到济宁站'}")
            all_passed = False
        else:
            train_station_poi_id = train_station_search.pois[0].id
            train_station_detail = maps_search_detail(train_station_poi_id)
            if train_station_detail.error or not train_station_detail.location:
                print(f"  验证失败: 获取济宁站坐标失败 - {train_station_detail.error if train_station_detail.error else '坐标为空'}")
                all_passed = False
            else:
                train_station_location = train_station_detail.location
                # 搜索汽车北站
                bus_station_north_search = maps_text_search(bus_station_north_keywords, train_station_city)
                if bus_station_north_search.error or not bus_station_north_search.pois or len(bus_station_north_search.pois) == 0:
                    print(f"  验证失败: 搜索汽车北站失败 - {bus_station_north_search.error if bus_station_north_search.error else '未找到汽车北站'}")
                    all_passed = False
                else:
                    bus_station_north_poi_id = bus_station_north_search.pois[0].id
                    bus_station_north_detail = maps_search_detail(bus_station_north_poi_id)
                    if bus_station_north_detail.error or not bus_station_north_detail.location:
                        print(f"  验证失败: 获取汽车北站坐标失败 - {bus_station_north_detail.error if bus_station_north_detail.error else '坐标为空'}")
                        all_passed = False
                    else:
                        bus_station_north_location = bus_station_north_detail.location
                        # 计算济宁站到博物馆的驾车时间 t1
                        route1 = maps_driving_by_coordinates(train_station_location, target_poi_location)
                        if route1.error or route1.total_duration_seconds is None:
                            print(f"  验证失败: 计算济宁站到博物馆的驾车时间失败 - {route1.error if route1.error else '时间为空'}")
                            all_passed = False
                        else:
                            t1 = route1.total_duration_seconds
                            # 计算博物馆到汽车北站的驾车时间 t2
                            route2 = maps_driving_by_coordinates(target_poi_location, bus_station_north_location)
                            if route2.error or route2.total_duration_seconds is None:
                                print(f"  验证失败: 计算博物馆到汽车北站的驾车时间失败 - {route2.error if route2.error else '时间为空'}")
                                all_passed = False
                            else:
                                t2 = route2.total_duration_seconds
                                total_time = t1 + t2
                                if total_time <= max_total_driving_time_seconds:
                                    print(f"  验证通过: 总时间 {total_time} 秒 <= {max_total_driving_time_seconds} 秒 (t1={t1}秒, t2={t2}秒)")
                                else:
                                    print(f"  验证失败: 总时间 {total_time} 秒 > {max_total_driving_time_seconds} 秒 (t1={t1}秒, t2={t2}秒)")
                                    all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
