"""
修改任务指令：你想在附近1200米以内找一个展览馆。这个展览馆到西单地铁站的直线距离不能超过500米。展览馆附近1000米内至少要存在一个地铁站满足到当前位置的直线距离小于1000米。展览馆到西单路口东公交站的直线距离不能超过2000米。从展览馆步行到灵境胡同地铁站的时间不能超过10分钟。你计划从家出发，先步行去展览馆，然后开车去北京北站，整个行程的时间不能超过25分钟。而且，这样绕路去展览馆所增加的时间，相比直接开车去北京北站，不能超过15分钟。你说话简短急促，希望快速完成所有事。
输入：B0LKZPEEQS
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('116.370966,39.913557', '展览馆', 1200)验证目标展览馆在搜索结果中
2. 调用maps_search_detail('B0LKZPEEQS')获取目标展览馆坐标
3. 调用maps_text_search('西单地铁站', '北京')获取西单地铁站poi_id，再调用maps_search_detail获取坐标，计算展览馆到西单地铁站的直线距离，验证>500米
4. 调用maps_around_search(展览馆坐标, '地铁站', 1000)，验证返回列表不为空。遍历返回的列表，调用maps_search_detail获取坐标，计算展览馆到地铁站的直线距离，验证存在一个满足<1000米的
5. 调用maps_text_search('西单路口东公交站', '北京')获取公交站poi_id，再调用maps_search_detail获取坐标，计算展览馆到西单路口东公交站的直线距离，验证<2000米
6. 调用maps_walking_by_coordinates('116.372484,39.923573', '116.373696,39.916055')计算展览馆到灵境胡同地铁站的步行时间，验证<600秒
7. 调用maps_walking_by_coordinates('116.370966,39.913557', '116.372484,39.923573')计算家到展览馆的步行时间t1
8. 调用maps_driving_by_coordinates('116.372484,39.923573', '116.353464,39.944699')计算展览馆到北京北站的驾车时间t2
9. 计算总时间t1+t2，验证<1500秒（25分钟）
10. 调用maps_driving_by_coordinates('116.370966,39.913557', '116.353464,39.944699')计算家到北京北站的直接驾车时间t3
11. 验证(t1+t2) - t3 < 900秒（15分钟）
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
    target_poi_id: str = "B0LKZPEEQS",
    user_location: str = "116.370966,39.913557",
    around_search_radius: str = "1200",
    around_search_keywords: str = "展览馆",
    xidan_metro_keywords: str = "西单地铁站",
    xidan_metro_city: str = "北京",
    min_distance_to_xidan_metro_meters: int = 500,
    metro_search_radius: str = "1000",
    metro_search_keywords: str = "地铁站",
    max_distance_to_metro_meters: int = 1000,
    bus_station_keywords: str = "西单路口东公交站",
    bus_station_city: str = "北京",
    max_distance_to_bus_station_meters: int = 2000,
    lingjing_metro_keywords: str = "灵境胡同地铁站",
    lingjing_metro_city: str = "北京",
    max_walking_to_lingjing_seconds: int = 600,
    beijing_north_station_keywords: str = "北京北站",
    beijing_north_station_city: str = "北京",
    max_total_time_seconds: int = 1500,
    max_detour_time_seconds: int = 900
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标，格式为"经度,纬度"
        around_search_radius: 周边搜索半径（米）
        around_search_keywords: 周边搜索关键词
        xidan_metro_keywords: 西单地铁站搜索关键词
        xidan_metro_city: 西单地铁站所在城市
        min_distance_to_xidan_metro_meters: 到西单地铁站的最小直线距离（米）
        metro_search_radius: 地铁站搜索半径（米）
        metro_search_keywords: 地铁站搜索关键词
        max_distance_to_metro_meters: 到地铁站的最大直线距离（米）
        bus_station_keywords: 公交站搜索关键词
        bus_station_city: 公交站所在城市
        max_distance_to_bus_station_meters: 到公交站的最大直线距离（米）
        lingjing_metro_keywords: 灵境胡同地铁站搜索关键词
        lingjing_metro_city: 灵境胡同地铁站所在城市
        max_walking_to_lingjing_seconds: 到灵境胡同地铁站的最大步行时间（秒）
        beijing_north_station_keywords: 北京北站搜索关键词
        beijing_north_station_city: 北京北站所在城市
        max_total_time_seconds: 最大总时间（秒）
        max_detour_time_seconds: 最大绕路时间（秒）
    
    Returns:
        bool: True表示所有验证都通过，False表示有验证未通过
    """
    all_passed = True
    
    # 验证步骤1: 调用maps_around_search验证目标展览馆在搜索结果中
    print("=" * 50)
    print("验证步骤1: 验证目标展览馆在搜索结果中")
    print(f"调用 maps_around_search(location='{user_location}', radius='{around_search_radius}', keywords='{around_search_keywords}')")
    around_result = maps_around_search(location=user_location, radius=around_search_radius, keywords=around_search_keywords)
    
    if around_result.error:
        print(f"验证步骤1: 未通过 - 周边搜索失败: {around_result.error}")
        all_passed = False
    elif not around_result.pois:
        print("验证步骤1: 未通过 - 周边搜索未找到POI")
        all_passed = False
    else:
        poi_ids = [poi.id for poi in around_result.pois]
        if target_poi_id in poi_ids:
            print(f"验证步骤1: 通过 - target_poi_id {target_poi_id} 在周边POI列表中（共{len(poi_ids)}个POI）")
        else:
            print(f"验证步骤1: 未通过 - target_poi_id {target_poi_id} 不在周边POI列表中")
            all_passed = False
    
    # 验证步骤2: 调用maps_search_detail获取目标展览馆坐标
    print("=" * 50)
    print("验证步骤2: 获取目标展览馆坐标")
    print(f"调用 maps_search_detail(id='{target_poi_id}')")
    detail_result = maps_search_detail(id=target_poi_id)
    
    if detail_result.error:
        print(f"验证步骤2: 未通过 - POI详情查询失败: {detail_result.error}")
        all_passed = False
        return False
    
    if not detail_result.location:
        print("验证步骤2: 未通过 - 无法获取POI坐标，后续验证无法进行")
        return False
    
    poi_location = detail_result.location
    print(f"验证步骤2: 通过 - 获取到POI坐标: {poi_location}")
    
    # 验证步骤3: 获取西单地铁站坐标，计算展览馆到西单地铁站的直线距离，验证>500米
    print("=" * 50)
    print("验证步骤3: 验证展览馆到西单地铁站的直线距离>500米")
    print(f"调用 maps_text_search(keywords='{xidan_metro_keywords}', city='{xidan_metro_city}')")
    xidan_metro_result = maps_text_search(keywords=xidan_metro_keywords, city=xidan_metro_city)
    
    if xidan_metro_result.error or not xidan_metro_result.pois or len(xidan_metro_result.pois) == 0:
        print(f"验证步骤3: 未通过 - 无法获取西单地铁站POI: {xidan_metro_result.error if xidan_metro_result.error else '未找到POI'}")
        all_passed = False
    else:
        xidan_metro_id = xidan_metro_result.pois[0].id
        print(f"获取到西单地铁站POI ID: {xidan_metro_id}")
        print(f"调用 maps_search_detail(id='{xidan_metro_id}')")
        xidan_metro_detail = maps_search_detail(id=xidan_metro_id)
        
        if xidan_metro_detail.error or not xidan_metro_detail.location:
            print(f"验证步骤3: 未通过 - 无法获取西单地铁站坐标: {xidan_metro_detail.error if xidan_metro_detail.error else '无坐标信息'}")
            all_passed = False
        else:
            xidan_metro_location = xidan_metro_detail.location
            print(f"获取到西单地铁站坐标: {xidan_metro_location}")
            print(f"调用 maps_distance(origins='{poi_location}', destination='{xidan_metro_location}')")
            distance_result = maps_distance(origins=poi_location, destination=xidan_metro_location)
            
            if distance_result.error or not distance_result.results:
                print(f"验证步骤3: 未通过 - 距离计算失败: {distance_result.error if distance_result.error else '无结果'}")
                all_passed = False
            else:
                distance = distance_result.results[0].distance_meters
                if distance > min_distance_to_xidan_metro_meters:
                    print(f"验证步骤3: 通过 - 直线距离 {distance}米 > {min_distance_to_xidan_metro_meters}米")
                else:
                    print(f"验证步骤3: 未通过 - 直线距离 {distance}米 <= {min_distance_to_xidan_metro_meters}米")
                    all_passed = False
    
    # 验证步骤4: 调用maps_around_search(展览馆坐标, '地铁站', 1000)，验证返回列表不为空。遍历返回的列表，调用maps_search_detail获取坐标，计算展览馆到地铁站的直线距离，验证存在一个满足<1000米的
    print("=" * 50)
    print("验证步骤4: 验证展览馆附近1000米内存在一个地铁站满足到展览馆的直线距离<1000米")
    print(f"调用 maps_around_search(location='{poi_location}', radius='{metro_search_radius}', keywords='{metro_search_keywords}')")
    metro_around_result = maps_around_search(location=poi_location, radius=metro_search_radius, keywords=metro_search_keywords)
    
    if metro_around_result.error:
        print(f"验证步骤4: 未通过 - 周边搜索失败: {metro_around_result.error}")
        all_passed = False
    elif not metro_around_result.pois or len(metro_around_result.pois) == 0:
        print("验证步骤4: 未通过 - 周边搜索未找到地铁站")
        all_passed = False
    else:
        found_valid_metro = False
        print(f"找到{len(metro_around_result.pois)}个地铁站，开始验证...")
        for metro_poi in metro_around_result.pois:
            metro_id = metro_poi.id
            print(f"检查地铁站: {metro_poi.name} (ID: {metro_id})")
            print(f"调用 maps_search_detail(id='{metro_id}')")
            metro_detail = maps_search_detail(id=metro_id)
            
            if metro_detail.error or not metro_detail.location:
                print(f"  跳过 - 无法获取坐标: {metro_detail.error if metro_detail.error else '无坐标信息'}")
                continue
            
            metro_location = metro_detail.location
            print(f"  地铁站坐标: {metro_location}")
            print(f"  调用 maps_distance(origins='{poi_location}', destination='{metro_location}')")
            metro_distance_result = maps_distance(origins=poi_location, destination=metro_location)
            
            if metro_distance_result.error or not metro_distance_result.results:
                print(f"  跳过 - 距离计算失败: {metro_distance_result.error if metro_distance_result.error else '无结果'}")
                continue
            
            metro_distance = metro_distance_result.results[0].distance_meters
            print(f"  直线距离: {metro_distance}米")
            
            if metro_distance < max_distance_to_metro_meters:
                print(f"  找到满足条件的地铁站: 直线距离 {metro_distance}米 < {max_distance_to_metro_meters}米")
                found_valid_metro = True
                break
        
        if found_valid_metro:
            print(f"验证步骤4: 通过 - 找到至少一个地铁站满足直线距离<{max_distance_to_metro_meters}米")
        else:
            print(f"验证步骤4: 未通过 - 未找到满足直线距离<{max_distance_to_metro_meters}米的地铁站")
            all_passed = False
    
    # 验证步骤5: 调用maps_text_search('西单路口东公交站', '北京')获取公交站poi_id，再调用maps_search_detail获取坐标，计算展览馆到西单路口东公交站的直线距离，验证<2000米
    print("=" * 50)
    print("验证步骤5: 验证展览馆到西单路口东公交站的直线距离<2000米")
    print(f"调用 maps_text_search(keywords='{bus_station_keywords}', city='{bus_station_city}')")
    bus_station_result = maps_text_search(keywords=bus_station_keywords, city=bus_station_city)
    
    if bus_station_result.error or not bus_station_result.pois or len(bus_station_result.pois) == 0:
        print(f"验证步骤5: 未通过 - 无法获取公交站POI: {bus_station_result.error if bus_station_result.error else '未找到POI'}")
        all_passed = False
    else:
        bus_station_id = bus_station_result.pois[0].id
        print(f"获取到公交站POI ID: {bus_station_id}")
        print(f"调用 maps_search_detail(id='{bus_station_id}')")
        bus_station_detail = maps_search_detail(id=bus_station_id)
        
        if bus_station_detail.error or not bus_station_detail.location:
            print(f"验证步骤5: 未通过 - 无法获取公交站坐标: {bus_station_detail.error if bus_station_detail.error else '无坐标信息'}")
            all_passed = False
        else:
            bus_station_location = bus_station_detail.location
            print(f"获取到公交站坐标: {bus_station_location}")
            print(f"调用 maps_distance(origins='{poi_location}', destination='{bus_station_location}')")
            bus_distance_result = maps_distance(origins=poi_location, destination=bus_station_location)
            
            if bus_distance_result.error or not bus_distance_result.results:
                print(f"验证步骤5: 未通过 - 距离计算失败: {bus_distance_result.error if bus_distance_result.error else '无结果'}")
                all_passed = False
            else:
                bus_distance = bus_distance_result.results[0].distance_meters
                if bus_distance < max_distance_to_bus_station_meters:
                    print(f"验证步骤5: 通过 - 直线距离 {bus_distance}米 < {max_distance_to_bus_station_meters}米")
                else:
                    print(f"验证步骤5: 未通过 - 直线距离 {bus_distance}米 >= {max_distance_to_bus_station_meters}米")
                    all_passed = False
    
    # 验证步骤6: 调用maps_walking_by_coordinates计算展览馆到灵境胡同地铁站的步行时间，验证<600秒
    print("=" * 50)
    print("验证步骤6: 验证展览馆到灵境胡同地铁站的步行时间<600秒")
    print(f"调用 maps_text_search(keywords='{lingjing_metro_keywords}', city='{lingjing_metro_city}')")
    lingjing_metro_result = maps_text_search(keywords=lingjing_metro_keywords, city=lingjing_metro_city)
    
    if lingjing_metro_result.error or not lingjing_metro_result.pois or len(lingjing_metro_result.pois) == 0:
        print(f"验证步骤6: 未通过 - 无法获取灵境胡同地铁站POI: {lingjing_metro_result.error if lingjing_metro_result.error else '未找到POI'}")
        all_passed = False
    else:
        lingjing_metro_id = lingjing_metro_result.pois[0].id
        print(f"获取到灵境胡同地铁站POI ID: {lingjing_metro_id}")
        print(f"调用 maps_search_detail(id='{lingjing_metro_id}')")
        lingjing_metro_detail = maps_search_detail(id=lingjing_metro_id)
        
        if lingjing_metro_detail.error or not lingjing_metro_detail.location:
            print(f"验证步骤6: 未通过 - 无法获取灵境胡同地铁站坐标: {lingjing_metro_detail.error if lingjing_metro_detail.error else '无坐标信息'}")
            all_passed = False
        else:
            lingjing_metro_location = lingjing_metro_detail.location
            print(f"获取到灵境胡同地铁站坐标: {lingjing_metro_location}")
            print(f"调用 maps_walking_by_coordinates(origin='{poi_location}', destination='{lingjing_metro_location}')")
            walking_result = maps_walking_by_coordinates(origin=poi_location, destination=lingjing_metro_location)
            
            if walking_result.error or walking_result.total_duration_seconds is None:
                print(f"验证步骤6: 未通过 - 步行路线规划失败: {walking_result.error if walking_result.error else '无时间信息'}")
                all_passed = False
            else:
                walking_time = walking_result.total_duration_seconds
                if walking_time < max_walking_to_lingjing_seconds:
                    print(f"验证步骤6: 通过 - 步行时间 {walking_time}秒 < {max_walking_to_lingjing_seconds}秒")
                else:
                    print(f"验证步骤6: 未通过 - 步行时间 {walking_time}秒 >= {max_walking_to_lingjing_seconds}秒")
                    all_passed = False
    
    # 验证步骤7: 调用maps_walking_by_coordinates计算家到展览馆的步行时间t1
    print("=" * 50)
    print("验证步骤7: 计算家到展览馆的步行时间t1")
    print(f"调用 maps_walking_by_coordinates(origin='{user_location}', destination='{poi_location}')")
    walking_result_t1 = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    
    if walking_result_t1.error or walking_result_t1.total_duration_seconds is None:
        print(f"验证步骤7: 未通过 - 步行路线规划失败: {walking_result_t1.error if walking_result_t1.error else '无时间信息'}")
        all_passed = False
        t1 = None
    else:
        t1 = walking_result_t1.total_duration_seconds
        print(f"验证步骤7: 通过 - 家到展览馆步行时间t1: {t1}秒")
    
    # 验证步骤8: 调用maps_driving_by_coordinates计算展览馆到北京北站的驾车时间t2
    print("=" * 50)
    print("验证步骤8: 计算展览馆到北京北站的驾车时间t2")
    print(f"调用 maps_text_search(keywords='{beijing_north_station_keywords}', city='{beijing_north_station_city}')")
    station_result = maps_text_search(keywords=beijing_north_station_keywords, city=beijing_north_station_city)
    
    if station_result.error or not station_result.pois or len(station_result.pois) == 0:
        print(f"验证步骤8: 未通过 - 无法获取北京北站POI: {station_result.error if station_result.error else '未找到POI'}")
        all_passed = False
        t2 = None
        station_location = None
    else:
        station_id = station_result.pois[0].id
        print(f"获取到北京北站POI ID: {station_id}")
        print(f"调用 maps_search_detail(id='{station_id}')")
        station_detail = maps_search_detail(id=station_id)
        
        if station_detail.error or not station_detail.location:
            print(f"验证步骤8: 未通过 - 无法获取北京北站坐标: {station_detail.error if station_detail.error else '无坐标信息'}")
            all_passed = False
            t2 = None
            station_location = None
        else:
            station_location = station_detail.location
            print(f"获取到北京北站坐标: {station_location}")
            print(f"调用 maps_driving_by_coordinates(origin='{poi_location}', destination='{station_location}')")
            driving_result_t2 = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
            
            if driving_result_t2.error or driving_result_t2.total_duration_seconds is None:
                print(f"验证步骤8: 未通过 - 驾车路线规划失败: {driving_result_t2.error if driving_result_t2.error else '无时间信息'}")
                all_passed = False
                t2 = None
            else:
                t2 = driving_result_t2.total_duration_seconds
                print(f"验证步骤8: 通过 - 展览馆到北京北站驾车时间t2: {t2}秒")
    
    # 验证步骤9: 计算总时间t1+t2，验证<1500秒（25分钟）
    print("=" * 50)
    print("验证步骤9: 验证总时间t1+t2 < 1500秒（25分钟）")
    if t1 is None or t2 is None:
        print("验证步骤9: 未通过 - 无法计算总时间（t1或t2缺失）")
        all_passed = False
    else:
        total_time = t1 + t2
        if total_time < max_total_time_seconds:
            print(f"验证步骤9: 通过 - 总时间 {total_time}秒 < {max_total_time_seconds}秒")
        else:
            print(f"验证步骤9: 未通过 - 总时间 {total_time}秒 >= {max_total_time_seconds}秒")
            all_passed = False
    
    # 验证步骤10: 调用maps_driving_by_coordinates计算家到北京北站的直接驾车时间t3
    print("=" * 50)
    print("验证步骤10: 计算家到北京北站的直接驾车时间t3")
    if station_location is None:
        print("验证步骤10: 未通过 - 无法获取北京北站坐标")
        all_passed = False
        t3 = None
    else:
        print(f"调用 maps_driving_by_coordinates(origin='{user_location}', destination='{station_location}')")
        driving_result_t3 = maps_driving_by_coordinates(origin=user_location, destination=station_location)
        
        if driving_result_t3.error or driving_result_t3.total_duration_seconds is None:
            print(f"验证步骤10: 未通过 - 驾车路线规划失败: {driving_result_t3.error if driving_result_t3.error else '无时间信息'}")
            all_passed = False
            t3 = None
        else:
            t3 = driving_result_t3.total_duration_seconds
            print(f"验证步骤10: 通过 - 家到北京北站直接驾车时间t3: {t3}秒")
    
    # 验证步骤11: 验证(t1+t2) - t3 < 900秒（15分钟）
    print("=" * 50)
    print("验证步骤11: 验证(t1+t2) - t3 < 900秒（15分钟）")
    if t1 is None or t2 is None or t3 is None:
        print("验证步骤11: 未通过 - 无法计算绕路时间（t1、t2或t3缺失）")
        all_passed = False
    else:
        detour_time = (t1 + t2) - t3
        if detour_time < max_detour_time_seconds:
            print(f"验证步骤11: 通过 - 绕路时间 {detour_time}秒 < {max_detour_time_seconds}秒")
        else:
            print(f"验证步骤11: 未通过 - 绕路时间 {detour_time}秒 >= {max_detour_time_seconds}秒")
            all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
