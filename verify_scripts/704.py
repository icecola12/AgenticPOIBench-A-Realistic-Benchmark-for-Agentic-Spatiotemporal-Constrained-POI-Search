"""
修改任务指令：你要在附近2500米内找一家咖啡厅。你打算骑车过去，骑行距离不能超过2000米、骑行时间不能超过10分钟。你还要赶去长治东站，这家咖啡厅到长治东站的驾车时间必须小于15分钟。另外，这家咖啡厅500米范围内必须能找到公交站。你思路混乱，可能会混淆信息，让对话难以跟进。
输入：B0LR79JK3Z
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用maps_search_detail(target_poi_id) 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 目标POI的location。
2) 调用maps_around_search(location=用户坐标113.120387,36.205043, radius=2500, keywords=咖啡厅)，验证返回pois中包含target_poi_id（满足“附近2500米内”）。
3) 调用maps_bicycling_by_coordinates(origin=用户坐标, destination=目标POI坐标)，验证total_distance_meters<=2000且total_duration_seconds<=600（骑行距离/时间约束）。
4) 调用maps_text_search(keywords=长治东站, city=长治, citylimit=true)并选取pois中“长治东站”(id=B0FFLBBHNQ)，再调用maps_search_detail(B0FFLBBHNQ)获取长治东站location。
5) 调用maps_driving_by_coordinates(origin=目标POI坐标, destination=长治东站坐标)，验证total_duration_seconds<900（到高铁站驾车时间约束）。
6) 调用maps_around_search(location=目标POI坐标, radius=500, keywords=公交站)，验证返回pois非空（500米内存在公交站）。
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
    maps_driving_by_coordinates ,
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
    target_poi_id: str = "B0LR79JK3Z",
    user_location: str = "113.120387,36.205043",
    around_search_radius: str = "2500",
    around_search_keywords: str = "咖啡厅",
    max_bicycling_distance_meters: int = 2000,
    max_bicycling_duration_seconds: int = 600,
    station_keywords: str = "长治东站",
    station_city: str = "长治",
    station_citylimit: str = "true",
    station_poi_id: str = "B0FFLBBHNQ",
    max_driving_duration_seconds: int = 900,
    bus_station_search_radius: str = "500",
    bus_station_search_keywords: str = "公交站"
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    验证步骤：
    1) 获取目标POI的location
    2) 周边搜索验证：验证目标POI是否在用户附近2500米内的咖啡厅列表中
    3) 骑行距离/时间验证：验证从用户位置到POI的骑行距离<=2000米且骑行时间<=600秒
    4) 获取长治东站坐标
    5) 驾车时间验证：验证从POI到长治东站的驾车时间<900秒
    6) 公交站验证：验证POI周围500米内存在公交站
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        around_search_radius: 周边搜索半径
        around_search_keywords: 周边搜索关键词
        max_bicycling_distance_meters: 最大骑行距离（米）
        max_bicycling_duration_seconds: 最大骑行时间（秒），10分钟=600秒
        station_keywords: 车站搜索关键词
        station_city: 车站所在城市
        station_citylimit: 车站搜索城市限制
        station_poi_id: 车站POI ID（如果maps_text_search获取失败则使用此默认值）
        max_driving_duration_seconds: 最大驾车时间（秒），15分钟=900秒（注意验证条件是<900）
        bus_station_search_radius: 公交站搜索半径
        bus_station_search_keywords: 公交站搜索关键词
    
    Returns:
        bool: 完全满足所有验证条件返回True，否则返回False
    """
    passed_count = 0
    total_count = 6
    
    # 实际用于后续计算的POI坐标，从POI详情中获取
    actual_poi_location = None
    
    # 验证步骤1: 获取目标POI的location
    print("验证步骤1: 获取目标POI的location")
    print(f"调用 maps_search_detail(id=\"{target_poi_id}\")")
    detail_result = maps_search_detail(id=target_poi_id)
    
    if detail_result.error:
        print(f"POI详情查询失败: {detail_result.error}")
        print("验证步骤1: 未通过")
    else:
        if detail_result.location:
            actual_poi_location = detail_result.location
            print(f"验证步骤1: 通过 - 获取到POI坐标: {actual_poi_location}")
            passed_count += 1
        else:
            print("验证步骤1: 未通过 - 无法获取POI坐标信息")
    
    # 验证步骤2: 周边搜索验证
    print("\n验证步骤2: 周边搜索验证")
    print(f"调用 maps_around_search(location=\"{user_location}\", radius=\"{around_search_radius}\", keywords=\"{around_search_keywords}\")")
    around_result = maps_around_search(
        location=user_location,
        radius=around_search_radius,
        keywords=around_search_keywords
    )
    
    if around_result.error:
        print(f"周边搜索失败: {around_result.error}")
        print("验证步骤2: 未通过")
    else:
        poi_found = False
        if around_result.pois:
            for poi in around_result.pois:
                if poi.id == target_poi_id:
                    poi_found = True
                    break
        
        if poi_found:
            print(f"验证步骤2: 通过 - 在周边搜索结果中找到目标POI ID: {target_poi_id}")
            passed_count += 1
        else:
            print(f"验证步骤2: 未通过 - 在周边搜索结果中未找到目标POI ID: {target_poi_id}")
    
    # 验证步骤3: 骑行距离/时间验证
    print("\n验证步骤3: 骑行距离/时间验证")
    if not actual_poi_location:
        print("验证步骤3: 未通过 - 无法获取POI坐标，无法规划骑行路线")
    else:
        print(f"调用 maps_bicycling_by_coordinates(origin=\"{user_location}\", destination=\"{actual_poi_location}\")")
        bicycling_result = maps_bicycling_by_coordinates(
            origin=user_location,
            destination=actual_poi_location
        )
        
        if bicycling_result.error:
            print(f"骑行路线规划失败: {bicycling_result.error}")
            print("验证步骤3: 未通过")
        else:
            distance_ok = False
            duration_ok = False
            
            if bicycling_result.total_distance_meters is not None:
                distance = bicycling_result.total_distance_meters
                if distance <= max_bicycling_distance_meters:
                    print(f"验证步骤3-距离: 通过 - 骑行距离 {distance}米 <= {max_bicycling_distance_meters}米")
                    distance_ok = True
                else:
                    print(f"验证步骤3-距离: 未通过 - 骑行距离 {distance}米 > {max_bicycling_distance_meters}米")
            else:
                print("验证步骤3-距离: 未通过 - 无法获取骑行距离")
            
            if bicycling_result.total_duration_seconds is not None:
                duration = bicycling_result.total_duration_seconds
                if duration <= max_bicycling_duration_seconds:
                    print(f"验证步骤3-时间: 通过 - 骑行时间 {duration}秒 <= {max_bicycling_duration_seconds}秒")
                    duration_ok = True
                else:
                    print(f"验证步骤3-时间: 未通过 - 骑行时间 {duration}秒 > {max_bicycling_duration_seconds}秒")
            else:
                print("验证步骤3-时间: 未通过 - 无法获取骑行时间")
            
            if distance_ok and duration_ok:
                print("验证步骤3: 通过 - 骑行距离和时间均满足要求")
                passed_count += 1
            else:
                print("验证步骤3: 未通过 - 骑行距离或时间不满足要求")
    
    # 验证步骤4: 获取长治东站坐标
    print("\n验证步骤4: 获取长治东站坐标")
    print(f"调用 maps_text_search(keywords=\"{station_keywords}\", city=\"{station_city}\", citylimit=\"{station_citylimit}\")")
    station_search_result = maps_text_search(
        keywords=station_keywords,
        city=station_city,
        citylimit=station_citylimit
    )
    
    station_location = None
    if station_search_result.error:
        print(f"文本搜索失败: {station_search_result.error}")
        print("验证步骤4: 未通过")
    else:
        station_id = None
        if station_search_result.pois:
            # 查找期望的车站POI ID
            for poi in station_search_result.pois:
                if poi.id == station_poi_id:
                    station_id = poi.id
                    break
            
            # 如果没找到期望的ID，使用第一个结果
            if not station_id and len(station_search_result.pois) > 0:
                station_id = station_search_result.pois[0].id
                print(f"未找到期望的车站ID {station_poi_id}，使用搜索结果中的第一个POI ID: {station_id}")
        
        if station_id:
            print(f"获取到车站POI ID: {station_id}")
            print(f"调用 maps_search_detail(id=\"{station_id}\")")
            station_detail_result = maps_search_detail(id=station_id)
            
            if station_detail_result.error:
                print(f"车站详情查询失败: {station_detail_result.error}")
                print("验证步骤4: 未通过")
            else:
                if station_detail_result.location:
                    station_location = station_detail_result.location
                    print(f"验证步骤4: 通过 - 获取到长治东站坐标: {station_location}")
                    passed_count += 1
                else:
                    print("验证步骤4: 未通过 - 无法获取车站坐标信息")
        else:
            print("验证步骤4: 未通过 - 未找到车站POI")
    
    # 验证步骤5: 驾车时间验证
    print("\n验证步骤5: 驾车时间验证")
    if not actual_poi_location:
        print("验证步骤5: 未通过 - 无法获取POI坐标，无法规划驾车路线")
    elif not station_location:
        print("验证步骤5: 未通过 - 无法获取车站坐标，无法规划驾车路线")
    else:
        print(f"调用 maps_driving_by_coordinates(origin=\"{actual_poi_location}\", destination=\"{station_location}\")")
        driving_result = maps_driving_by_coordinates(
            origin=actual_poi_location,
            destination=station_location
        )
        
        if driving_result.error:
            print(f"驾车路线规划失败: {driving_result.error}")
            print("验证步骤5: 未通过")
        else:
            if driving_result.total_duration_seconds is not None:
                duration = driving_result.total_duration_seconds
                # 注意：验证条件是 < 900，不是 <= 900
                if duration < max_driving_duration_seconds:
                    print(f"验证步骤5: 通过 - 驾车时间 {duration}秒 < {max_driving_duration_seconds}秒")
                    passed_count += 1
                else:
                    print(f"验证步骤5: 未通过 - 驾车时间 {duration}秒 >= {max_driving_duration_seconds}秒")
            else:
                print("验证步骤5: 未通过 - 无法获取驾车时间")
    
    # 验证步骤6: 公交站验证
    print("\n验证步骤6: 公交站验证")
    if not actual_poi_location:
        print("验证步骤6: 未通过 - 无法获取POI坐标，无法搜索公交站")
    else:
        print(f"调用 maps_around_search(location=\"{actual_poi_location}\", radius=\"{bus_station_search_radius}\", keywords=\"{bus_station_search_keywords}\")")
        bus_station_result = maps_around_search(
            location=actual_poi_location,
            radius=bus_station_search_radius,
            keywords=bus_station_search_keywords
        )
        
        if bus_station_result.error:
            print(f"公交站搜索失败: {bus_station_result.error}")
            print("验证步骤6: 未通过")
        else:
            if bus_station_result.pois and len(bus_station_result.pois) > 0:
                print(f"验证步骤6: 通过 - 在POI周围{bus_station_search_radius}米内找到 {len(bus_station_result.pois)} 个公交站")
                passed_count += 1
            else:
                print(f"验证步骤6: 未通过 - 在POI周围{bus_station_search_radius}米内未找到公交站")
    
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
