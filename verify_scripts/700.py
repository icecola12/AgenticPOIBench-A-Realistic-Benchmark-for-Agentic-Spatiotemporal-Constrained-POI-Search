"""
输入：B0JK4SNRYN
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离(附近2.5公里内)：调用 maps_around_search(location=115.922307,28.706842, radius=2500, keywords=干洗店)，验证返回pois中包含 target_poi_id=B0JK4SNRYN。
2) 骑行路程<=3公里、骑行时间<=12分钟：先调用 maps_search_detail(id=B0JK4SNRYN) 取得目标location=115.922404,28.706882；再调用 maps_bicycling_by_coordinates(origin=115.922307,28.706842, destination=115.922404,28.706882)，验证 total_distance_meters<=3000 且 total_duration_seconds<=720。
3) 到“青山路口(公交站)”直线距离<=3.1公里：调用 maps_text_search(keywords=青山路口公交站, city=南昌, citylimit=true) 获取公交站poi（取BV10272830）；调用 maps_search_detail(id=BV10272830) 得到公交站location=115.900896,28.687729；再调用 maps_distance(origins=115.900896,28.687729, destination=115.922404,28.706882)，验证 distance_meters<=3100。
4) 干洗店->南昌火车站 驾车<=15分钟：调用 maps_text_search(keywords=南昌火车站, city=南昌) 获取 poi_id，再调用 maps_search_detail(id=poi_id) 得到火车站location；调用 maps_driving_by_coordinates(origin=115.922404,28.706882, destination=火车站location)，验证 total_duration_seconds<=900。
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
    target_poi_id: str = "B0JK4SNRYN",
    user_location: str = "115.922307,28.706842",
    around_search_radius: str = "2500",
    around_search_keywords: str = "干洗店",
    max_bicycling_distance_meters: int = 3000,
    max_bicycling_duration_seconds: int = 720,
    bus_station_keywords: str = "青山路口公交站",
    bus_station_city: str = "南昌",
    bus_station_citylimit: str = "true",
    expected_bus_station_id: str = "BV10272830",
    max_distance_to_bus_station_meters: int = 3100,
    train_station_address: str = "南昌火车站",
    train_station_city: str = "南昌",
    max_driving_duration_seconds: int = 900
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    验证步骤：
    1) 距离(附近2.5公里内)：验证目标POI是否在附近2.5公里内的干洗店列表中
    2) 骑行路程<=3公里、骑行时间<=12分钟：验证从用户位置到POI的骑行距离和时间是否满足要求
    3) 到"青山路口(公交站)"直线距离<=3.1公里：验证POI到公交站的直线距离是否满足要求
    4) 干洗店->南昌火车站 驾车<=15分钟：验证从POI到南昌火车站的驾车时间是否满足要求
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        around_search_radius: 周边搜索半径
        around_search_keywords: 周边搜索关键词
        max_bicycling_distance_meters: 最大骑行距离（米），3公里=3000米
        max_bicycling_duration_seconds: 最大骑行时间（秒），12分钟=720秒
        bus_station_keywords: 公交站搜索关键词
        bus_station_city: 公交站所在城市
        bus_station_citylimit: 是否限制在城市范围内搜索
        expected_bus_station_id: 期望的公交站POI ID
        max_distance_to_bus_station_meters: 到公交站的最大直线距离（米），3.1公里=3100米
        train_station_address: 火车站地址
        train_station_city: 火车站所在城市
        max_driving_duration_seconds: 最大驾车时间（秒），15分钟=900秒
    
    Returns:
        bool: 完全满足所有验证条件返回True，否则返回False
    """
    passed_count = 0
    total_count = 4
    
    # 实际用于后续计算的POI坐标，从POI详情中获取
    actual_poi_location = None
    
    # 验证步骤1: 距离(附近2.5公里内)验证
    print("验证步骤1: 距离(附近2.5公里内)验证")
    print(f"调用 maps_around_search(location=\"{user_location}\", radius=\"{around_search_radius}\", keywords=\"{around_search_keywords}\")")
    around_result = maps_around_search(
        location=user_location,
        radius=around_search_radius,
        keywords=around_search_keywords
    )
    
    if around_result.error:
        print(f"周边搜索失败: {around_result.error}")
        print("验证步骤1: 未通过")
    else:
        poi_found = False
        if around_result.pois:
            for poi in around_result.pois:
                if poi.id == target_poi_id:
                    poi_found = True
                    break
        
        if poi_found:
            print(f"验证步骤1: 通过 - 在周边搜索结果中找到目标POI ID: {target_poi_id}")
            passed_count += 1
        else:
            print(f"验证步骤1: 未通过 - 在周边搜索结果中未找到目标POI ID: {target_poi_id}")
    
    # 验证步骤2: 骑行路程<=3公里、骑行时间<=12分钟验证
    print("\n验证步骤2: 骑行路程<=3公里、骑行时间<=12分钟验证")
    print(f"调用 maps_search_detail(id=\"{target_poi_id}\")")
    detail_result = maps_search_detail(id=target_poi_id)
    
    if detail_result.error:
        print(f"POI详情查询失败: {detail_result.error}")
        print("验证步骤2: 未通过")
    else:
        if detail_result.location:
            actual_poi_location = detail_result.location
            print(f"获取到POI坐标: {actual_poi_location}")
            
            print(f"调用 maps_bicycling_by_coordinates(origin=\"{user_location}\", destination=\"{actual_poi_location}\")")
            bicycling_result = maps_bicycling_by_coordinates(
                origin=user_location,
                destination=actual_poi_location
            )
            
            if bicycling_result.error:
                print(f"骑行路线规划失败: {bicycling_result.error}")
                print("验证步骤2: 未通过")
            else:
                distance_ok = False
                duration_ok = False
                
                if bicycling_result.total_distance_meters is not None:
                    if bicycling_result.total_distance_meters <= max_bicycling_distance_meters:
                        print(f"骑行距离验证通过 - 骑行距离 {bicycling_result.total_distance_meters}米 <= {max_bicycling_distance_meters}米")
                        distance_ok = True
                    else:
                        print(f"骑行距离验证未通过 - 骑行距离 {bicycling_result.total_distance_meters}米 > {max_bicycling_distance_meters}米")
                else:
                    print("骑行距离验证未通过 - 无法获取骑行距离")
                
                if bicycling_result.total_duration_seconds is not None:
                    if bicycling_result.total_duration_seconds <= max_bicycling_duration_seconds:
                        print(f"骑行时间验证通过 - 骑行时间 {bicycling_result.total_duration_seconds}秒 <= {max_bicycling_duration_seconds}秒")
                        duration_ok = True
                    else:
                        print(f"骑行时间验证未通过 - 骑行时间 {bicycling_result.total_duration_seconds}秒 > {max_bicycling_duration_seconds}秒")
                else:
                    print("骑行时间验证未通过 - 无法获取骑行时间")
                
                if distance_ok and duration_ok:
                    print("验证步骤2: 通过 - 骑行距离和时间均满足要求")
                    passed_count += 1
                else:
                    print("验证步骤2: 未通过 - 骑行距离或时间不满足要求")
        else:
            print("验证步骤2: 未通过 - 无法获取POI坐标信息")
    
    # 验证步骤3: 到"青山路口(公交站)"直线距离<=3.1公里验证
    print("\n验证步骤3: 到\"青山路口(公交站)\"直线距离<=3.1公里验证")
    if not actual_poi_location:
        print("验证步骤3: 未通过 - 无法获取POI坐标，无法计算距离")
    else:
        print(f"调用 maps_text_search(keywords=\"{bus_station_keywords}\", city=\"{bus_station_city}\", citylimit=\"{bus_station_citylimit}\")")
        text_search_result = maps_text_search(
            keywords=bus_station_keywords,
            city=bus_station_city,
            citylimit=bus_station_citylimit
        )
        
        if text_search_result.error:
            print(f"文本搜索失败: {text_search_result.error}")
            print("验证步骤3: 未通过")
        else:
            bus_station_id = None
            if text_search_result.pois:
                # 查找期望的公交站POI ID
                for poi in text_search_result.pois:
                    if poi.id == expected_bus_station_id:
                        bus_station_id = poi.id
                        break
                
                # 如果没找到期望的ID，使用第一个结果
                if not bus_station_id and len(text_search_result.pois) > 0:
                    bus_station_id = text_search_result.pois[0].id
                    print(f"未找到期望的公交站ID {expected_bus_station_id}，使用搜索结果中的第一个POI ID: {bus_station_id}")
            
            if not bus_station_id:
                print("未找到公交站POI")
                print("验证步骤3: 未通过")
            else:
                print(f"获取到公交站POI ID: {bus_station_id}")
                print(f"调用 maps_search_detail(id=\"{bus_station_id}\")")
                bus_detail_result = maps_search_detail(id=bus_station_id)
                
                if bus_detail_result.error:
                    print(f"公交站详情查询失败: {bus_detail_result.error}")
                    print("验证步骤3: 未通过")
                else:
                    if bus_detail_result.location:
                        bus_station_location = bus_detail_result.location
                        print(f"获取到公交站坐标: {bus_station_location}")
                        print(f"调用 maps_distance(origins=\"{bus_station_location}\", destination=\"{actual_poi_location}\")")
                        distance_result = maps_distance(
                            origins=bus_station_location,
                            destination=actual_poi_location
                        )
                        
                        if distance_result.error:
                            print(f"距离计算失败: {distance_result.error}")
                            print("验证步骤3: 未通过")
                        else:
                            if distance_result.results and len(distance_result.results) > 0:
                                distance_meters = distance_result.results[0].distance_meters
                                if distance_meters <= max_distance_to_bus_station_meters:
                                    print(f"验证步骤3: 通过 - 与公交站的直线距离 {distance_meters}米 <= {max_distance_to_bus_station_meters}米")
                                    passed_count += 1
                                else:
                                    print(f"验证步骤3: 未通过 - 与公交站的直线距离 {distance_meters}米 > {max_distance_to_bus_station_meters}米")
                            else:
                                print("验证步骤3: 未通过 - 未获取到距离结果")
                    else:
                        print("验证步骤3: 未通过 - 无法获取公交站坐标信息")
    
    # 验证步骤4: 干洗店->南昌火车站 驾车<=15分钟验证
    print("\n验证步骤4: 干洗店->南昌火车站 驾车<=15分钟验证")
    if not actual_poi_location:
        print("验证步骤4: 未通过 - 无法获取POI坐标，无法规划驾车路线")
    else:
        print(f"调用 maps_text_search(keywords=\"{train_station_address}\", city=\"{train_station_city}\") 获取 poi_id，再 maps_search_detail 获取坐标")
        text_search_result = maps_text_search(keywords=train_station_address, city=train_station_city)
        if text_search_result.error:
            print(f"文本搜索失败: {text_search_result.error}")
            print("验证步骤4: 未通过")
        elif not text_search_result.pois or len(text_search_result.pois) == 0:
            print("未找到火车站的坐标")
            print("验证步骤4: 未通过")
        else:
            first_poi_id = text_search_result.pois[0].id
            detail_result = maps_search_detail(id=first_poi_id)
            if detail_result.error or not detail_result.location:
                print(f"获取详情失败: {detail_result.error or '无location'}")
                print("验证步骤4: 未通过")
            else:
                train_station_location = detail_result.location
                print(f"获取到火车站坐标: {train_station_location}")
                print(f"调用 maps_driving_by_coordinates(origin=\"{actual_poi_location}\", destination=\"{train_station_location}\")")
                driving_result = maps_driving_by_coordinates(
                    origin=actual_poi_location,
                    destination=train_station_location
                )
                
                if driving_result.error:
                    print(f"驾车路线规划失败: {driving_result.error}")
                    print("验证步骤4: 未通过")
                else:
                    if driving_result.total_duration_seconds is not None:
                        duration = driving_result.total_duration_seconds
                        if duration <= max_driving_duration_seconds:
                            print(f"验证步骤4: 通过 - 驾车时间 {duration}秒 <= {max_driving_duration_seconds}秒")
                            passed_count += 1
                        else:
                            print(f"验证步骤4: 未通过 - 驾车时间 {duration}秒 > {max_driving_duration_seconds}秒")
                    else:
                        print("验证步骤4: 未通过 - 无法获取驾车时间")
    
    # 输出最终结果
    print(f"\n验证完成: 通过 {passed_count}/{total_count} 项验证")
    if passed_count == total_count:
        print("最终验证结果: True (完全满足所有验证条件)")
        return True
    else:
        print("最终验证结果: False (部分满足或不满足验证条件)")
        return False


def main():
    result = verify_poi()
    print(f"\n函数返回值: {result}")  


if __name__ == "__main__":
    main()
