"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
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
根据给定的验证方法验证POI是否符合要求。
输入：B02140255A
输出：True

验证方法：
1) 距离约束（附近2.5km）：调用 maps_around_search(location='120.410971,36.071445', radius='2500', keywords='图书馆')，验证返回pois中包含目标poi_id=B02140255A。
2) 到医院驾车时间≤15分钟：调用 maps_text_search(keywords='青岛大学附属医院(市南院区)', city='青岛') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取医院坐标H；再调用 maps_driving_by_coordinates(origin=目标POI.location, destination=H)，验证 total_duration_seconds ≤ 900。
3) 到青岛站直线距离≤9公里：调用 maps_text_search(keywords='青岛站', city='青岛') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取青岛站坐标Q；再调用 maps_distance(origins=目标POI.location, destination=Q)，验证 distance_meters ≤ 9000。
"""
def verify_poi(
    target_poi_id: str = "B02140255A",
    user_location: str = "120.410971,36.071445",
    search_radius: str = "2500",
    search_keywords: str = "图书馆",
    hospital_address: str = "青岛大学附属医院(市南院区)",
    hospital_city: str = "青岛",
    max_driving_seconds: int = 900,
    station_address: str = "青岛站",
    station_city: str = "青岛",
    max_distance_meters: int = 9000
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID，默认值为 "B02140255A"
        user_location: 用户位置坐标，格式为"经度,纬度"，默认值为 "120.410971,36.071445"
        search_radius: 搜索半径（米），默认值为 "2500"
        search_keywords: 搜索关键词，默认值为 "图书馆"
        hospital_address: 医院地址，默认值为 "青岛大学附属医院(市南院区)"
        hospital_city: 医院所在城市，默认值为 "青岛"
        max_driving_seconds: 最大驾车时间（秒），默认值为 900（15分钟）
        station_address: 车站地址，默认值为 "青岛站"
        station_city: 车站所在城市，默认值为 "青岛"
        max_distance_meters: 最大直线距离（米），默认值为 9000（9公里）
    
    Returns:
        bool: 所有验证条件都满足返回True，否则返回False
    """
    all_passed = True
    
    # 步骤1：距离约束（附近2.5km）
    print(f"步骤1：验证目标是否在附近{int(search_radius)/1000}公里内")
    around_result = maps_around_search(
        location=user_location,
        radius=search_radius,
        keywords=search_keywords
    )
    
    if around_result.error:
        print(f"  验证失败：周边搜索出错 - {around_result.error}")
        return False
    
    if not around_result.pois:
        print(f"  验证失败：未找到任何POI")
        return False
    
    # 检查返回的pois列表中是否包含target_poi_id
    poi_ids = [poi.id for poi in around_result.pois]
    if target_poi_id in poi_ids:
        print(f"  验证通过：POI {target_poi_id} 在附近{int(search_radius)/1000}公里内")
    else:
        print(f"  验证失败：POI {target_poi_id} 不在附近{int(search_radius)/1000}公里内")
        all_passed = False
    
    # 步骤2：到医院驾车时间≤15分钟
    print(f"步骤2：验证到医院驾车时间不超过{max_driving_seconds//60}分钟")
    
    # 获取目标POI的坐标
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"  验证失败：获取POI详情出错 - {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"  验证失败：无法获取POI坐标")
        return False
    
    poi_location = poi_detail.location
    
    # 用 maps_text_search + maps_search_detail 获取医院坐标
    text_search_result = maps_text_search(keywords=hospital_address, city=hospital_city)
    if text_search_result.error:
        print(f"  验证失败：获取医院坐标出错 - {text_search_result.error}")
        return False
    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"  验证失败：未找到医院坐标")
        return False
    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"  验证失败：获取医院坐标出错 - {detail_result.error or '无location'}")
        return False
    hospital_location = detail_result.location
    
    # 计算驾车时间
    driving_result = maps_driving_by_coordinates(
        origin=poi_location,
        destination=hospital_location
    )
    
    if driving_result.error:
        print(f"  验证失败：驾车路线规划出错 - {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"  验证失败：无法获取驾车时长")
        return False
    
    t_drive_seconds = driving_result.total_duration_seconds
    
    if t_drive_seconds <= max_driving_seconds:
        print(f"  验证通过：驾车时间 {t_drive_seconds//60}分{t_drive_seconds%60}秒 <= {max_driving_seconds//60}分钟")
    else:
        print(f"  验证失败：驾车时间 {t_drive_seconds//60}分{t_drive_seconds%60}秒 > {max_driving_seconds//60}分钟")
        all_passed = False
    
    # 步骤3：到青岛站直线距离≤9公里
    print(f"步骤3：验证到车站直线距离不超过{max_distance_meters/1000}公里")
    
    # 用 maps_text_search + maps_search_detail 获取车站坐标
    text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if text_search_result.error:
        print(f"  验证失败：获取车站坐标出错 - {text_search_result.error}")
        return False
    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"  验证失败：未找到车站坐标")
        return False
    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"  验证失败：获取车站坐标出错 - {detail_result.error or '无location'}")
        return False
    station_location = detail_result.location
    
    # 计算直线距离
    distance_result = maps_distance(
        origins=poi_location,
        destination=station_location
    )
    
    if distance_result.error:
        print(f"  验证失败：距离计算出错 - {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"  验证失败：无法获取距离信息")
        return False
    
    distance_meters = distance_result.results[0].distance_meters
    
    if distance_meters <= max_distance_meters:
        print(f"  验证通过：直线距离 {distance_meters/1000:.2f}公里 <= {max_distance_meters/1000}公里")
    else:
        print(f"  验证失败：直线距离 {distance_meters/1000:.2f}公里 > {max_distance_meters/1000}公里")
        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '不通过'}")
    return result


if __name__ == "__main__":
    main()
