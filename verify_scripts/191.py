"""
修改任务指令：你想在附近1000米以内找一家酒吧。酒吧评分至少4.4分。酒吧附近500米至少需要存在一个公交站满足到酒吧的直线距离不超过300米。酒吧到八一南街和畅路口公交站的步行时间不超过10分钟。从你家出发，先去酒吧，再去金华火车站，整个路程的开车总时间不超过25分钟。另外，酒吧不能离农贸市场公交站500米以内。你想在附近1000米以内找一家酒吧。酒吧评分至少4.4分。酒吧附近500米至少需要存在一个公交站满足到酒吧的直线距离不超过300米。酒吧到八一南街和畅路口公交站的步行时间不超过10分钟。从你家出发，先去酒吧，再去金华火车站，整个路程的开车总时间不超过25分钟。另外，酒吧不能离农贸市场公交站500米以内。你思路混乱，可能会混淆信息，让对话难以跟进。
输入：B0KAMU2KE0
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用 maps_around_search('119.652598,29.058992', '酒吧', 1000) 检查目标酒吧是否在结果中。
2. 调用 maps_search_detail('B0KAMU2KE0') 获取酒吧评分，验证 rating ≥ 4.4。
3. 调用 maps_around_search('119.658420,29.061129', '公交站', 500) 验证附近有公交站。
4. 调用 maps_distance('119.658420,29.061129', '119.657588,29.062109') 计算酒吧到八一南街和畅路口公交站的直线距离，验证 ≤ 300 米。
5. 调用 maps_walking_by_coordinates('119.658420,29.061129', '119.657588,29.062109') 计算步行时间，验证 total_duration_seconds ≤ 600 秒（10分钟）。
6. 调用 maps_driving_by_coordinates('119.652598,29.058992', '119.658420,29.061129') 得到时间 t1，再调用 maps_driving_by_coordinates('119.658420,29.061129', '119.635860,29.110764') 得到时间 t2，验证 t1 + t2 ≤ 1500 秒（25分钟）。
7. 调用 maps_distance('119.658420,29.061129', '119.647855,29.060705') 计算酒吧到农贸市场公交站的直线距离，验证 ≥ 500 米。
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
    target_poi_id: str = 'B0KAMU2KE0',
    user_location: str = '119.652598,29.058992',
    search_keywords: str = '酒吧',
    search_radius: str = '1000',
    bus_station_keywords: str = '公交站',
    bus_station_radius: str = '500',
    min_rating: float = 4.4,
    max_distance_to_bus_station_meters: int = 300,
    max_walking_seconds: int = 600,
    max_total_driving_seconds: int = 1500,
    min_distance_to_nongmao_meters: int = 500,
    train_station_keywords: str = '金华火车站',
    train_station_city: str = '金华',
    nongmao_bus_station_keywords: str = '农贸市场公交站'
) -> bool:
    """
    验证POI是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID
        user_location: 用户位置坐标（可以写死）
        search_keywords: 搜索关键词
        search_radius: 搜索半径（米）
        bus_station_keywords: 公交站搜索关键词
        bus_station_radius: 公交站搜索半径（米）
        min_rating: 最小评分
        max_distance_to_bus_station_meters: 到公交站的最大距离（米）
        max_walking_seconds: 最大步行时间（秒）
        max_total_driving_seconds: 最大总驾车时间（秒）
        min_distance_to_nongmao_meters: 到农贸市场公交站的最小距离（米）
        train_station_keywords: 火车站搜索关键词
        train_station_city: 火车站搜索城市
        nongmao_bus_station_keywords: 农贸市场公交站搜索关键词
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 检查目标酒吧是否在周边搜索结果中
    print("验证步骤1: 检查目标酒吧是否在周边搜索结果中...")
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
    
    # 验证步骤2: 获取酒吧评分和坐标，验证 rating >= 4.4
    print("验证步骤2: 验证评分 >= 4.4...")
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
                if rating >= min_rating:
                    print(f"  验证通过: 评分 {rating} >= {min_rating}")
                else:
                    print(f"  验证失败: 评分 {rating} < {min_rating}")
                    all_passed = False
            else:
                print("  验证失败: 无法获取评分信息")
                all_passed = False
    
    # 验证步骤3: 验证酒吧附近有公交站
    print("验证步骤3: 验证酒吧附近有公交站...")
    if not target_poi_location:
        print("  验证失败: 目标酒吧坐标未获取")
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
            print(f"  验证通过: 找到 {len(bus_stations)} 个公交站")
        else:
            print("  验证失败: 未找到公交站")
            all_passed = False
            bus_stations = []
    
    # 验证步骤4: 计算酒吧到八一南街和畅路口公交站的直线距离，验证 <= 300 米
    print("验证步骤4: 验证酒吧到八一南街和畅路口公交站的直线距离 <= 300 米...")
    if not target_poi_location:
        print("  验证失败: 目标酒吧坐标未获取")
        all_passed = False
        bayi_bus_station_location = None
    elif not bus_stations:
        print("  验证失败: 未找到公交站列表")
        all_passed = False
        bayi_bus_station_location = None
    else:
        # 从公交站列表中查找名称包含"八一南街和畅路口"的公交站
        bayi_bus_station = None
        for bus_station in bus_stations:
            if '八一南街和畅路口' in bus_station.name:
                bayi_bus_station = bus_station
                break
        
        if not bayi_bus_station or not bayi_bus_station.location:
            print("  验证失败: 未找到八一南街和畅路口公交站")
            all_passed = False
            bayi_bus_station_location = None
        else:
            bayi_bus_station_location = bayi_bus_station.location
            distance_result = maps_distance(target_poi_location, bayi_bus_station_location)
            if distance_result.error or not distance_result.results:
                print(f"  验证失败: 计算距离失败 - {distance_result.error if distance_result.error else '结果为空'}")
                all_passed = False
            else:
                distance = distance_result.results[0].distance_meters
                if distance <= max_distance_to_bus_station_meters:
                    print(f"  验证通过: 距离 {distance} 米 <= {max_distance_to_bus_station_meters} 米")
                else:
                    print(f"  验证失败: 距离 {distance} 米 > {max_distance_to_bus_station_meters} 米")
                    all_passed = False
    
    # 验证步骤5: 计算酒吧到八一南街和畅路口公交站的步行时间，验证 <= 600 秒（10分钟）
    print("验证步骤5: 验证酒吧到八一南街和畅路口公交站的步行时间 <= 600 秒...")
    if not target_poi_location:
        print("  验证失败: 目标酒吧坐标未获取")
        all_passed = False
    elif not bayi_bus_station_location:
        print("  验证失败: 八一南街和畅路口公交站坐标未获取")
        all_passed = False
    else:
        walking_result = maps_walking_by_coordinates(target_poi_location, bayi_bus_station_location)
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
    
    # 验证步骤6: 计算从用户位置到酒吧再到金华火车站的总驾车时间，验证 <= 1500 秒（25分钟）
    print("验证步骤6: 验证总驾车时间 <= 1500 秒（25分钟）...")
    if not target_poi_location:
        print("  验证失败: 目标酒吧坐标未获取")
        all_passed = False
    else:
        # 搜索金华火车站
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
    
    # 验证步骤7: 计算酒吧到农贸市场公交站的直线距离，验证 >= 500 米
    print("验证步骤7: 验证酒吧到农贸市场公交站的直线距离 >= 500 米...")
    if not target_poi_location:
        print("  验证失败: 目标酒吧坐标未获取")
        all_passed = False
    else:
        # 使用 maps_text_search 搜索农贸市场公交站
        nongmao_search = maps_text_search(nongmao_bus_station_keywords, train_station_city)
        if nongmao_search.error or not nongmao_search.pois or len(nongmao_search.pois) == 0:
            print(f"  验证失败: 搜索农贸市场公交站失败 - {nongmao_search.error if nongmao_search.error else '未找到农贸市场公交站'}")
            all_passed = False
        else:
            nongmao_poi_id = nongmao_search.pois[0].id
            nongmao_detail = maps_search_detail(nongmao_poi_id)
            if nongmao_detail.error or not nongmao_detail.location:
                print(f"  验证失败: 获取农贸市场公交站坐标失败 - {nongmao_detail.error if nongmao_detail.error else '坐标为空'}")
                all_passed = False
            else:
                nongmao_bus_station_location = nongmao_detail.location
                distance_result = maps_distance(target_poi_location, nongmao_bus_station_location)
                if distance_result.error or not distance_result.results:
                    print(f"  验证失败: 计算距离失败 - {distance_result.error if distance_result.error else '结果为空'}")
                    all_passed = False
                else:
                    distance = distance_result.results[0].distance_meters
                    if distance >= min_distance_to_nongmao_meters:
                        print(f"  验证通过: 距离 {distance} 米 >= {min_distance_to_nongmao_meters} 米")
                    else:
                        print(f"  验证失败: 距离 {distance} 米 < {min_distance_to_nongmao_meters} 米")
                        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
