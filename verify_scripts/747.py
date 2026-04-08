"""
输入：B000A239E3
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边约束验证：调用 maps_around_search(location="116.351949,39.899529", radius="2000", keywords="医院")，验证返回pois中包含 target_poi_id=B000A239E3。
2) 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 POI坐标：调用 maps_search_detail(id="B000A239E3")，读取POI的location。
3) 用户到医院步行时长验证：调用 maps_walking_by_coordinates(origin="116.351949,39.899529", destination="116.340022,39.905587")，得到 total_duration_seconds=636，验证 636/60<=12。
4) 北京西站坐标：调用 maps_text_search(keywords="北京西站", city="北京") 取 poi_id，再 maps_search_detail(id=poi_id) 得到 location。
5) 医院到北京西站步行时长验证：调用 maps_walking_by_coordinates(origin="116.340022,39.905587", destination="116.322033,39.894912")，得到 total_duration_seconds=1543，验证 1543/60<=26。
6) 医院到北京西站直线距离验证：调用 maps_distance(origins="116.340022,39.905587", destination="116.322033,39.894912")，得到 distance_meters=1942，验证 1942<=2000。
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
    target_poi_id: str = "B000A239E3",
    user_location: str = "116.351949,39.899529",
    search_radius: str = "2000",
    search_keywords: str = "医院",
    max_walking_time_to_poi_minutes: int = 12,
    station_address: str = "北京西站",
    station_city: str = "北京",
    max_walking_time_to_station_minutes: int = 26,
    max_distance_to_station_meters: int = 2000
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        search_radius: 搜索半径（米）
        search_keywords: 搜索关键词
        max_walking_time_to_poi_minutes: 用户到POI的最大步行时间（分钟）
        station_address: 车站地址
        station_city: 车站城市
        max_walking_time_to_station_minutes: POI到车站的最大步行时间（分钟）
        max_distance_to_station_meters: POI到车站的最大直线距离（米）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 周边约束验证
    print(f"验证步骤1: 周边约束验证 - 搜索位置 {user_location} 半径 {search_radius}米内的 {search_keywords}")
    around_result = maps_around_search(
        location=user_location,
        radius=search_radius,
        keywords=search_keywords
    )
    if around_result.error:
        print(f"  验证失败: {around_result.error}")
        all_passed = False
    else:
        poi_ids = [poi.id for poi in around_result.pois] if around_result.pois else []
        if target_poi_id in poi_ids:
            print(f"  验证通过: POI {target_poi_id} 在搜索结果中")
        else:
            print(f"  验证失败: POI {target_poi_id} 不在搜索结果中")
            all_passed = False
    
    # 验证步骤2: 获取POI坐标
    print(f"验证步骤2: 获取POI坐标 - 查询POI {target_poi_id} 的详细信息")
    poi_detail_result = maps_search_detail(id=target_poi_id)
    if poi_detail_result.error:
        print(f"  验证失败: {poi_detail_result.error}")
        all_passed = False
        return False  # 无法获取POI坐标，后续验证无法进行
    poi_location = poi_detail_result.location
    if not poi_location:
        print(f"  验证失败: 无法获取POI坐标")
        all_passed = False
        return False  # 无法获取POI坐标，后续验证无法进行
    print(f"  验证通过: POI坐标为 {poi_location}")
    
    # 验证步骤3: 用户到医院步行时长验证
    print(f"验证步骤3: 用户到医院步行时长验证 - 从 {user_location} 到 {poi_location}")
    walking_result1 = maps_walking_by_coordinates(
        origin=user_location,
        destination=poi_location
    )
    if walking_result1.error:
        print(f"  验证失败: {walking_result1.error}")
        all_passed = False
    else:
        duration_seconds = walking_result1.total_duration_seconds
        duration_minutes = duration_seconds / 60
        if duration_minutes <= max_walking_time_to_poi_minutes:
            print(f"  验证通过: 步行时长 {duration_seconds}秒 ({duration_minutes:.2f}分钟) <= {max_walking_time_to_poi_minutes}分钟")
        else:
            print(f"  验证失败: 步行时长 {duration_seconds}秒 ({duration_minutes:.2f}分钟) > {max_walking_time_to_poi_minutes}分钟")
            all_passed = False
    
    # 验证步骤4: 北京西站坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
    print(f"验证步骤4: 获取车站坐标 - 查询 {station_address} 在 {station_city} 的坐标")
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"  验证失败: {station_text_result.error}")
        all_passed = False
        return False  # 无法获取车站坐标，后续验证无法进行
    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"  验证失败: 未找到车站坐标")
        all_passed = False
        return False  # 无法获取车站坐标，后续验证无法进行
    first_poi_id = station_text_result.pois[0].id
    station_detail_result = maps_search_detail(id=first_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取坐标失败: {station_detail_result.error}")
        all_passed = False
        return False
    if not station_detail_result.location:
        print("❌ 未获取到坐标")
        all_passed = False
        return False
    station_location = station_detail_result.location
    print(f"  验证通过: 车站坐标为 {station_location}")
    
    # 验证步骤5: 医院到北京西站步行时长验证
    print(f"验证步骤5: 医院到车站步行时长验证 - 从 {poi_location} 到 {station_location}")
    walking_result2 = maps_walking_by_coordinates(
        origin=poi_location,
        destination=station_location
    )
    if walking_result2.error:
        print(f"  验证失败: {walking_result2.error}")
        all_passed = False
    else:
        duration_seconds = walking_result2.total_duration_seconds
        duration_minutes = duration_seconds / 60
        if duration_minutes <= max_walking_time_to_station_minutes:
            print(f"  验证通过: 步行时长 {duration_seconds}秒 ({duration_minutes:.2f}分钟) <= {max_walking_time_to_station_minutes}分钟")
        else:
            print(f"  验证失败: 步行时长 {duration_seconds}秒 ({duration_minutes:.2f}分钟) > {max_walking_time_to_station_minutes}分钟")
            all_passed = False
    
    # 验证步骤6: 医院到北京西站直线距离验证
    print(f"验证步骤6: 医院到车站直线距离验证 - 从 {poi_location} 到 {station_location}")
    distance_result = maps_distance(
        origins=poi_location,
        destination=station_location
    )
    if distance_result.error:
        print(f"  验证失败: {distance_result.error}")
        all_passed = False
    else:
        if not distance_result.results or len(distance_result.results) == 0:
            print(f"  验证失败: 未找到距离结果")
            all_passed = False
        else:
            distance_meters = distance_result.results[0].distance_meters
            if distance_meters <= max_distance_to_station_meters:
                print(f"  验证通过: 直线距离 {distance_meters}米 <= {max_distance_to_station_meters}米")
            else:
                print(f"  验证失败: 直线距离 {distance_meters}米 > {max_distance_to_station_meters}米")
                all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")
    print(f"返回值: {result}")


if __name__ == "__main__":
    main()
