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
    maps_driving_by_coordinates ,
    maps_walking_by_coordinates,
    maps_text_search,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search

"""
根据给定的验证方法验证POI是否符合要求。
输入：B038200F2B
输出：True

验证方法：
步骤1：验证目标是否在“附近2公里内”
- 调用 maps_around_search(location="110.354229,20.069141", radius="2000", keywords="医院")
- 验证返回的pois列表中包含 target_poi_id = B038200F2B。

步骤2：验证“步行到医院不超过20分钟”
- 调用 maps_search_detail(id="B038200F2B") 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 医院坐标 location = L_hospital。
- 调用 maps_walking_by_coordinates(origin="110.354229,20.069141", destination=L_hospital)，得到步行总时长 t_walk_seconds。
- 验证 t_walk_seconds <= 20 * 60。

步骤3：验证“医院到海口东站驾车不超过25分钟”
- 调用 maps_search_detail(id="B038202YP2") 获取海口东站坐标 location = L_station。
- 调用 maps_driving_by_coordinates(origin=L_hospital, destination=L_station)，得到驾车总时长 t_drive_seconds。
- 验证 t_drive_seconds <= 25 * 60。
"""
def verify_poi(
    target_poi_id: str = "B038200F2B",
    user_location: str = "110.354229,20.069141",
    search_radius: str = "2000",
    search_keywords: str = "医院",
    max_walking_minutes: int = 20,
    station_poi_id: str = "B038202YP2",
    max_driving_minutes: int = 25
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID，默认值为 "B038200F2B"
        user_location: 用户位置坐标，格式为"经度,纬度"，默认值为 "110.354229,20.069141"
        search_radius: 搜索半径（米），默认值为 "2000"
        search_keywords: 搜索关键词，默认值为 "医院"
        max_walking_minutes: 最大步行时间（分钟），默认值为 20
        station_poi_id: 车站POI ID，默认值为 "B038202YP2"
        max_driving_minutes: 最大驾车时间（分钟），默认值为 25
    
    Returns:
        bool: 所有验证条件都满足返回True，否则返回False
    """
    all_passed = True
    
    # 步骤1：验证目标是否在"附近2公里内"
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
    
    # 步骤2：验证"步行到医院不超过max_walking_minutes分钟"
    print(f"步骤2：验证步行到医院不超过{max_walking_minutes}分钟")
    hospital_detail = maps_search_detail(id=target_poi_id)
    
    if hospital_detail.error:
        print(f"  验证失败：获取医院详情出错 - {hospital_detail.error}")
        return False
    
    if not hospital_detail.location:
        print(f"  验证失败：无法获取医院坐标")
        return False
    
    L_hospital = hospital_detail.location
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=L_hospital
    )
    
    if walking_result.error:
        print(f"  验证失败：步行路线规划出错 - {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"  验证失败：无法获取步行时长")
        return False
    
    t_walk_seconds = walking_result.total_duration_seconds
    max_walk_seconds = max_walking_minutes * 60
    
    if t_walk_seconds <= max_walk_seconds:
        print(f"  验证通过：步行时间 {t_walk_seconds//60}分{t_walk_seconds%60}秒 <= {max_walking_minutes}分钟")
    else:
        print(f"  验证失败：步行时间 {t_walk_seconds//60}分{t_walk_seconds%60}秒 > {max_walking_minutes}分钟")
        all_passed = False
    
    # 步骤3：验证"医院到海口东站驾车不超过max_driving_minutes分钟"
    print(f"步骤3：验证医院到车站驾车不超过{max_driving_minutes}分钟")
    station_detail = maps_search_detail(id=station_poi_id)
    
    if station_detail.error:
        print(f"  验证失败：获取车站详情出错 - {station_detail.error}")
        return False
    
    if not station_detail.location:
        print(f"  验证失败：无法获取车站坐标")
        return False
    
    L_station = station_detail.location
    driving_result = maps_driving_by_coordinates(
        origin=L_hospital,
        destination=L_station
    )
    
    if driving_result.error:
        print(f"  验证失败：驾车路线规划出错 - {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"  验证失败：无法获取驾车时长")
        return False
    
    t_drive_seconds = driving_result.total_duration_seconds
    max_drive_seconds = max_driving_minutes * 60
    
    if t_drive_seconds <= max_drive_seconds:
        print(f"  验证通过：驾车时间 {t_drive_seconds//60}分{t_drive_seconds%60}秒 <= {max_driving_minutes}分钟")
    else:
        print(f"  验证失败：驾车时间 {t_drive_seconds//60}分{t_drive_seconds%60}秒 > {max_driving_minutes}分钟")
        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '不通过'}")
    return result


if __name__ == "__main__":
    main()
