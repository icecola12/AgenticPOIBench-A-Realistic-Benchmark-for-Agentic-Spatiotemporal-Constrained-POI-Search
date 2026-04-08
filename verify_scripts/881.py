"""
修改任务指令：你想在附近2000米内找一个展览馆，评分至少4.0分。这个展览馆不能离惠州科技馆太近，直线距离至少500米以外。你开车去展览馆的路线上，至少需要存在一个途径点，满足那里附近200米内得有便利店，而且1000米内得有加油站。展览馆附近500米内至少要存在公交站满足步行过去距离不超过1500米，步行时间要在15分钟以内。之后你还要去科技馆，所以从家出发，先到展览馆再到科技馆的总开车时间不能超过10分钟，而且绕道展览馆比直接去科技馆多花的时间不能超过2分钟。你对服务和解决方案持怀疑态度。
输入：B0JGXZ2289
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('114.444347,23.119259', '展览馆', 2000)验证目标展览馆在搜索范围内。
2. 调用maps_search_detail('B0JGXZ2289')获取评分，验证≥4.0。
3. 调用maps_text_search('惠州科技馆', '惠州')获取科技馆poi_id B02F000VJY，再调用maps_search_detail('B02F000VJY')获取坐标114.416714,23.108054。调用maps_distance('114.429370,23.115085', '114.416714,23.108054')验证距离>500米。
4. 调用maps_driving_by_coordinates('114.444347,23.119259', '114.429370,23.115085')获取驾车路线步骤，遍历步骤作为途径点
5. 调用maps_around_search(途径点坐标, '便利店', 200），验证返回结果不为空。调用maps_around_search(途径点坐标, '加油站', 1000），验证返回结果不为空。
7. 调用maps_around_search('114.429370,23.115085', '公交站', 500)验证存在公交站(如供水公司(西行) BV09089274)。
8. 调用maps_walking_by_coordinates('114.429370,23.115085', '114.428522,23.114558')验证步行距离<1500米，步行时间要在15分钟以内
9. 调用maps_driving_by_coordinates('114.444347,23.119259', '114.429370,23.115085')获取时间t1，调用maps_driving_by_coordinates('114.429370,23.115085', '114.416714,23.108054')获取时间t2，计算总时间t1+t2，验证≤10分钟。
10. 调用maps_driving_by_coordinates('114.444347,23.119259', '114.416714,23.108054')获取直接驾车时间t3，验证(t1+t2)-t3 ≤ 2分钟。
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
    target_poi_id: str = 'B0JGXZ2289',
    user_location: str = '114.444347,23.119259',
    search_keywords: str = '展览馆',
    search_radius: str = '2000',
    min_rating: float = 4.0,
    kejiguan_keywords: str = '惠州科技馆',
    kejiguan_city: str = '惠州',
    min_distance_to_kejiguan_meters: int = 500,
    convenience_store_keywords: str = '便利店',
    convenience_store_radius: str = '200',
    gas_station_keywords: str = '加油站',
    gas_station_radius: str = '1000',
    bus_station_keywords: str = '公交站',
    bus_station_radius: str = '500',
    max_walking_distance_meters: int = 1500,
    max_walking_seconds: int = 900,
    max_total_driving_seconds: int = 600,
    max_detour_seconds: int = 120
) -> bool:
    """
    验证POI是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID
        user_location: 用户位置坐标（写死）
        search_keywords: 搜索关键词
        search_radius: 搜索半径（米）
        min_rating: 最小评分
        kejiguan_keywords: 科技馆搜索关键词
        kejiguan_city: 科技馆搜索城市
        min_distance_to_kejiguan_meters: 到科技馆的最小距离（米）
        convenience_store_keywords: 便利店搜索关键词
        convenience_store_radius: 便利店搜索半径（米）
        gas_station_keywords: 加油站搜索关键词
        gas_station_radius: 加油站搜索半径（米）
        bus_station_keywords: 公交站搜索关键词
        bus_station_radius: 公交站搜索半径（米）
        max_walking_distance_meters: 最大步行距离（米）
        max_walking_seconds: 最大步行时间（秒）
        max_total_driving_seconds: 最大总驾车时间（秒）
        max_detour_seconds: 最大绕路时间（秒）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 检查目标展览馆是否在周边搜索结果中
    print("验证步骤1: 检查目标展览馆是否在周边搜索结果中...")
    around_result = maps_around_search(user_location, search_radius, search_keywords)
    if around_result.error:
        print(f"  验证失败: {around_result.error}")
        all_passed = False
    elif around_result.pois:
        poi_ids = [poi.id for poi in around_result.pois]
        if target_poi_id in poi_ids:
            print(f"  验证通过: 目标展览馆 {target_poi_id} 在搜索结果中")
        else:
            print(f"  验证失败: 目标展览馆 {target_poi_id} 不在搜索结果中")
            all_passed = False
    else:
        print("  验证失败: 搜索结果为空")
        all_passed = False
    
    # 验证步骤2: 获取评分和坐标，验证 rating >= 4.0
    print("验证步骤2: 验证评分 >= 4.0...")
    detail_result = maps_search_detail(target_poi_id)
    if detail_result.error:
        print(f"  验证失败: {detail_result.error}")
        all_passed = False
        target_poi_location = None
    else:
        # 获取目标POI坐标，后续步骤需要用到
        target_poi_location = detail_result.location
        if not target_poi_location:
            print("  验证失败: 无法获取目标展览馆坐标")
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
    
    # 验证步骤3: 验证到科技馆的距离 > 500 米
    print("验证步骤3: 验证到科技馆的距离 > 500 米...")
    if not target_poi_location:
        print("  验证失败: 目标展览馆坐标未获取")
        all_passed = False
        kejiguan_location = None
    else:
        kejiguan_search_result = maps_text_search(kejiguan_keywords, kejiguan_city)
        if kejiguan_search_result.error:
            print(f"  验证失败: 搜索科技馆失败 - {kejiguan_search_result.error}")
            all_passed = False
            kejiguan_location = None
        elif not kejiguan_search_result.pois or len(kejiguan_search_result.pois) == 0:
            print("  验证失败: 未找到科技馆 POI")
            all_passed = False
            kejiguan_location = None
        else:
            kejiguan_poi_id = kejiguan_search_result.pois[0].id
            kejiguan_detail = maps_search_detail(kejiguan_poi_id)
            if kejiguan_detail.error or not kejiguan_detail.location:
                print(f"  验证失败: 无法获取科技馆坐标 - {kejiguan_detail.error if kejiguan_detail.error else '坐标为空'}")
                all_passed = False
                kejiguan_location = None
            else:
                kejiguan_location = kejiguan_detail.location
                distance_result = maps_distance(target_poi_location, kejiguan_location)
                if distance_result.error or not distance_result.results:
                    print(f"  验证失败: 计算距离失败 - {distance_result.error if distance_result.error else '结果为空'}")
                    all_passed = False
                else:
                    distance = distance_result.results[0].distance_meters
                    if distance > min_distance_to_kejiguan_meters:
                        print(f"  验证通过: 距离 {distance} 米 > {min_distance_to_kejiguan_meters} 米")
                    else:
                        print(f"  验证失败: 距离 {distance} 米 <= {min_distance_to_kejiguan_meters} 米")
                        all_passed = False
    
    # 验证步骤4和5: 验证驾车路线途经点中至少有一个点满足附近200米内有便利店且1000米内有加油站
    print("验证步骤4和5: 验证驾车路线途经点中至少有一个点满足附近200米内有便利店且1000米内有加油站...")
    if not target_poi_location:
        print("  验证失败: 目标展览馆坐标未获取")
        all_passed = False
    else:
        driving_result = maps_driving_by_coordinates(user_location, target_poi_location)
        if driving_result.error or not driving_result.steps:
            print(f"  验证失败: 获取驾车路线失败 - {driving_result.error if driving_result.error else 'steps为空'}")
            all_passed = False
        else:
            found_valid_waypoint = False
            # 遍历steps，对from_coordinates 和 to_coordinates（不包括起点和终点）
            all_coords = set()
            for i, step in enumerate(driving_result.steps):
                # 不包括起点和终点
                if i > 0:  # from_coordinates 不是起点
                    all_coords.add(step.from_coordinates)
                if i < len(driving_result.steps) - 1:  # to_coordinates 不是终点
                    all_coords.add(step.to_coordinates)
            
            for coord in all_coords:
                # 检查附近200米内是否有便利店
                convenience_result = maps_around_search(coord, convenience_store_radius, convenience_store_keywords)
                has_convenience_store = not convenience_result.error and convenience_result.pois and len(convenience_result.pois) > 0
                
                # 检查附近1000米内是否有加油站
                gas_result = maps_around_search(coord, gas_station_radius, gas_station_keywords)
                has_gas_station = not gas_result.error and gas_result.pois and len(gas_result.pois) > 0
                
                if has_convenience_store and has_gas_station:
                    found_valid_waypoint = True
                    print(f"  验证通过: 找到途经点 {coord} 满足条件（附近有便利店和加油站）")
                    break
            
            if not found_valid_waypoint:
                print("  验证失败: 未找到满足条件的途经点（附近200米内有便利店且1000米内有加油站）")
                all_passed = False
    
    # 验证步骤7和8: 验证展览馆附近500米内有公交站，且至少有一个公交站满足步行距离<1500米，步行时间<15分钟
    print("验证步骤7和8: 验证展览馆附近500米内有公交站，且至少有一个公交站满足步行距离<1500米，步行时间<15分钟...")
    if not target_poi_location:
        print("  验证失败: 目标展览馆坐标未获取")
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
                # 计算步行距离和时间
                walking_result = maps_walking_by_coordinates(target_poi_location, bus_station_location)
                if not walking_result.error and walking_result.total_distance_meters is not None and walking_result.total_duration_seconds is not None:
                    walking_distance = walking_result.total_distance_meters
                    walking_time = walking_result.total_duration_seconds
                    if walking_distance < max_walking_distance_meters and walking_time < max_walking_seconds:
                        found_valid_bus_station = True
                        print(f"  验证通过: 找到公交站 {bus_station.name} ({bus_station.id}) 满足条件（步行距离 {walking_distance} 米 < {max_walking_distance_meters} 米，步行时间 {walking_time} 秒 < {max_walking_seconds} 秒）")
                        break
            
            if not found_valid_bus_station:
                print("  验证失败: 未找到满足条件的公交站（步行距离<1500米且步行时间<15分钟）")
                all_passed = False
    
    # 验证步骤9: 验证从用户位置到展览馆再到科技馆的总驾车时间 <= 10分钟（600秒）
    print("验证步骤9: 验证从用户位置到展览馆再到科技馆的总驾车时间 <= 10分钟（600秒）...")
    if not target_poi_location:
        print("  验证失败: 目标展览馆坐标未获取")
        all_passed = False
    elif not kejiguan_location:
        print("  验证失败: 科技馆坐标未获取")
        all_passed = False
    else:
        # 计算用户位置到展览馆的驾车时间 t1
        route1 = maps_driving_by_coordinates(user_location, target_poi_location)
        if route1.error or route1.total_duration_seconds is None:
            print(f"  验证失败: 计算用户位置到展览馆的驾车时间失败 - {route1.error if route1.error else '时间为空'}")
            all_passed = False
        else:
            t1 = route1.total_duration_seconds
            # 计算展览馆到科技馆的驾车时间 t2
            route2 = maps_driving_by_coordinates(target_poi_location, kejiguan_location)
            if route2.error or route2.total_duration_seconds is None:
                print(f"  验证失败: 计算展览馆到科技馆的驾车时间失败 - {route2.error if route2.error else '时间为空'}")
                all_passed = False
            else:
                t2 = route2.total_duration_seconds
                total_time = t1 + t2
                if total_time <= max_total_driving_seconds:
                    print(f"  验证通过: 总时间 {total_time} 秒 <= {max_total_driving_seconds} 秒 (t1={t1}秒, t2={t2}秒)")
                else:
                    print(f"  验证失败: 总时间 {total_time} 秒 > {max_total_driving_seconds} 秒 (t1={t1}秒, t2={t2}秒)")
                    all_passed = False
    
    # 验证步骤10: 验证绕道展览馆比直接去科技馆多花的时间 <= 2分钟（120秒）
    print("验证步骤10: 验证绕道展览馆比直接去科技馆多花的时间 <= 2分钟（120秒）...")
    if not target_poi_location:
        print("  验证失败: 目标展览馆坐标未获取")
        all_passed = False
    elif not kejiguan_location:
        print("  验证失败: 科技馆坐标未获取")
        all_passed = False
    else:
        # 需要先获取 t1 和 t2（从步骤9）
        route1 = maps_driving_by_coordinates(user_location, target_poi_location)
        if route1.error or route1.total_duration_seconds is None:
            print(f"  验证失败: 计算用户位置到展览馆的驾车时间失败 - {route1.error if route1.error else '时间为空'}")
            all_passed = False
        else:
            t1 = route1.total_duration_seconds
            route2 = maps_driving_by_coordinates(target_poi_location, kejiguan_location)
            if route2.error or route2.total_duration_seconds is None:
                print(f"  验证失败: 计算展览馆到科技馆的驾车时间失败 - {route2.error if route2.error else '时间为空'}")
                all_passed = False
            else:
                t2 = route2.total_duration_seconds
                # 计算直接到科技馆的时间 t3
                route3 = maps_driving_by_coordinates(user_location, kejiguan_location)
                if route3.error or route3.total_duration_seconds is None:
                    print(f"  验证失败: 计算用户位置直接到科技馆的驾车时间失败 - {route3.error if route3.error else '时间为空'}")
                    all_passed = False
                else:
                    t3 = route3.total_duration_seconds
                    detour_time = (t1 + t2) - t3
                    if detour_time <= max_detour_seconds:
                        print(f"  验证通过: 绕路时间 {detour_time} 秒 <= {max_detour_seconds} 秒 (t1={t1}秒, t2={t2}秒, t3={t3}秒)")
                    else:
                        print(f"  验证失败: 绕路时间 {detour_time} 秒 > {max_detour_seconds} 秒 (t1={t1}秒, t2={t2}秒, t3={t3}秒)")
                        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
