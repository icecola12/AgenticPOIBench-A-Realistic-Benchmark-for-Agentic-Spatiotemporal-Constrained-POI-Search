
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束（附近3公里）：调用 maps_around_search(location='119.672754,29.0578', radius='3000', keywords='公园')，验证返回pois中包含目标poi_id=B0IR475D59。
2) 步行时间不超过20分钟：调用 maps_search_detail('B0IR475D59') 获取目标location；再调用 maps_walking_by_coordinates(origin='119.672754,29.0578', destination=目标location)，验证 total_duration_seconds <= 1200。
3) 从金华市中心医院开车不超过12分钟：调用 maps_text_search(keywords='金华市中心医院', city='金华') 取 poi_id，再 maps_search_detail(id=poi_id) 获取医院 location_H；调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 720。
4) 远离湖海塘公园至少2公里（直线）：调用 maps_text_search(keywords='湖海塘公园', city='金华') 取 poi_id，再 maps_search_detail(id=poi_id) 获取 location_L；调用 maps_distance，验证 distance_meters >= 2000。
"""

import os
import sys

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 导入高德地图工具函数
from tools.amap_tools import (
    maps_text_search,
    maps_search_detail ,
    maps_distance,
    maps_walking_by_coordinates,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "119.672754,29.0578",
    search_radius: int = 3000,  # 3km
    keywords: str = "公园",
    max_walking_duration: int = 1200,  # 20 minutes = 1200 seconds
    hospital_address: str = "金华市中心医院",
    hospital_city: str = "金华",
    max_driving_from_hospital: int = 720,  # 12 minutes = 720 seconds
    exclusion_park_address: str = "湖海塘公园",
    exclusion_park_city: str = "金华",
    min_distance_from_exclusion: int = 2000  # 2km = 2000 meters
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离约束（附近3公里）：验证返回pois中包含目标poi_id
    2) 步行时间不超过20分钟：验证 total_duration_seconds <= 1200
    3) 从金华市中心医院开车不超过12分钟：验证 total_duration_seconds <= 720
    4) 远离湖海塘公园至少2公里（直线）：验证 distance_meters >= 2000

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"119.672754,29.0578"
        search_radius: 搜索半径（米），默认3000（3公里）
        keywords: 搜索关键词，默认"公园"
        max_walking_duration: 最大步行时长（秒），默认1200（20分钟）
        hospital_address: 医院地址，默认"金华市中心医院"
        hospital_city: 医院所在城市，默认"金华"
        max_driving_from_hospital: 从医院的最大驾车时长（秒），默认720（12分钟）
        exclusion_park_address: 排除公园地址，默认"湖海塘公园"
        exclusion_park_city: 排除公园所在城市，默认"金华"
        min_distance_from_exclusion: 到排除公园的最小距离（米），默认2000（2公里）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（附近3公里内的公园）
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois or len(around_search_result.pois) == 0:
        print(f"❌ 未找到符合条件的POI")
        return False

    # 检查返回列表中是否包含目标POI ID
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break

    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False

    # 步骤2: 步行时间不超过20分钟
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证步行时间（<= 20分钟）
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    # 步骤3: 从金华市中心医院开车不超过12分钟（用 maps_text_search + maps_search_detail 替代 maps_geo）
    hospital_text_result = maps_text_search(keywords=hospital_address, city=hospital_city)
    if hospital_text_result.error:
        print(f"❌ 获取{hospital_address}坐标失败: {hospital_text_result.error}")
        return False

    if not hospital_text_result.pois or len(hospital_text_result.pois) == 0:
        print(f"❌ 未找到{hospital_address}坐标")
        return False

    first_poi_id = hospital_text_result.pois[0].id
    hospital_detail_result = maps_search_detail(id=first_poi_id)
    if hospital_detail_result.error:
        print(f"❌ 获取坐标失败: {hospital_detail_result.error}")
        return False
    if not hospital_detail_result.location:
        print("❌ 未获取到坐标")
        return False

    hospital_location = hospital_detail_result.location
    print(f"✅ 获取{hospital_address}坐标: {hospital_location}")

    # 验证从医院驾车时间（<= 12分钟）
    driving_result = maps_driving_by_coordinates(origin=hospital_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算从{hospital_address}驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取从{hospital_address}驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_from_hospital:
        print(f"❌ 从{hospital_address}驾车时长{driving_duration}秒，超过{max_driving_from_hospital}秒（{max_driving_from_hospital // 60}分钟）")
        return False
    print(f"✅ 从{hospital_address}驾车时长{driving_duration}秒，符合要求（<= {max_driving_from_hospital}秒，即{max_driving_from_hospital // 60}分钟）")

    # 步骤4: 远离湖海塘公园至少2公里（直线）（用 maps_text_search + maps_search_detail 替代 maps_geo）
    exclusion_park_text_result = maps_text_search(keywords=exclusion_park_address, city=exclusion_park_city)
    if exclusion_park_text_result.error:
        print(f"❌ 获取{exclusion_park_address}坐标失败: {exclusion_park_text_result.error}")
        return False

    if not exclusion_park_text_result.pois or len(exclusion_park_text_result.pois) == 0:
        print(f"❌ 未找到{exclusion_park_address}坐标")
        return False

    first_poi_id = exclusion_park_text_result.pois[0].id
    exclusion_park_detail_result = maps_search_detail(id=first_poi_id)
    if exclusion_park_detail_result.error:
        print(f"❌ 获取坐标失败: {exclusion_park_detail_result.error}")
        return False
    if not exclusion_park_detail_result.location:
        print("❌ 未获取到坐标")
        return False

    exclusion_park_location = exclusion_park_detail_result.location
    print(f"✅ 获取{exclusion_park_address}坐标: {exclusion_park_location}")

    # 验证距离（distance_meters >= 2000）
    distance_result = maps_distance(origins=poi_location, destination=exclusion_park_location)
    if distance_result.error:
        print(f"❌ 计算到{exclusion_park_address}距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取到{exclusion_park_address}距离")
        return False

    distance_meters = distance_result.results[0].distance_meters
    if distance_meters < min_distance_from_exclusion:
        print(f"❌ 到{exclusion_park_address}距离{distance_meters}米，未达到{min_distance_from_exclusion}米（{min_distance_from_exclusion / 1000}公里）")
        return False
    print(f"✅ 到{exclusion_park_address}距离{distance_meters}米，符合要求（>= {min_distance_from_exclusion}米，即{min_distance_from_exclusion / 1000}公里）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 639.py 文件...\n")
    result = verify_poi(poi_id="B0IR475D59")
    print(f"\n验证结果: {result}")
