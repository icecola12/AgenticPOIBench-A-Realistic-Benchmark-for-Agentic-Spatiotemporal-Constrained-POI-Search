
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边候选集验证：以用户坐标(118.813815,35.180345)调用maps_around_search，radius=3000，keywords=咖啡；验证返回pois数量>=8，且目标poi_id(B0J2KL0BVP)在pois列表中。
2) POI信息获取：对目标poi_id调用maps_search_detail，获取其location(记为L_poi)。
3) 骑行时间与距离验证：调用maps_bicycling_by_coordinates(origin=用户坐标, destination=L_poi)，验证total_duration_seconds<=720(12分钟)且total_distance_meters<=2600。
4) 去火车站驾车时间验证：调用maps_text_search(keywords=莒南站, city=临沂)获取poi_id，再调用maps_search_detail(id=poi_id)得到L_station；再调用maps_driving_by_coordinates(origin=L_poi, destination=L_station)，验证total_duration_seconds<=360(6分钟)。
5) 排除半径验证：调用maps_text_search(keywords=莒南县人民医院, city=临沂)获取poi_id，再调用maps_search_detail(id=poi_id)得到L_hospital；调用maps_distance(origins=L_poi, destination=L_hospital)，验证distance_meters>500。
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
    maps_search_detail,
    maps_text_search,
    maps_distance,
    maps_bicycling_by_coordinates,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "118.813815,35.180345",
    search_radius: int = 3000,  # 3km
    keywords: str = "咖啡",
    min_poi_count: int = 8,
    max_bicycling_duration: int = 720,  # 12 minutes = 720 seconds
    max_bicycling_distance: int = 2600,  # 2600 meters
    station_address: str = "莒南站",
    station_city: str = "临沂",
    max_driving_to_station: int = 360,  # 6 minutes = 360 seconds
    hospital_address: str = "莒南县人民医院",
    hospital_city: str = "临沂",
    min_exclusion_distance: int = 500  # 500 meters
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边候选集验证：验证返回pois数量>=8，且目标poi_id在pois列表中
    2) POI信息获取：获取其location(记为L_poi)
    3) 骑行时间与距离验证：验证total_duration_seconds<=720(12分钟)且total_distance_meters<=2600
    4) 去火车站驾车时间验证：验证total_duration_seconds<=360(6分钟)
    5) 排除半径验证：验证distance_meters>500

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"118.813815,35.180345"
        search_radius: 搜索半径（米），默认3000（3公里）
        keywords: 搜索关键词，默认"咖啡"
        min_poi_count: 最少POI数量，默认8
        max_bicycling_duration: 最大骑行时长（秒），默认720（12分钟）
        max_bicycling_distance: 最大骑行距离（米），默认2600
        station_address: 火车站地址，默认"莒南站"
        station_city: 火车站所在城市，默认"临沂"
        max_driving_to_station: 到火车站的最大驾车时长（秒），默认360（6分钟）
        hospital_address: 医院地址，默认"莒南县人民医院"
        hospital_city: 医院所在城市，默认"临沂"
        min_exclusion_distance: 最小排除距离（米），默认500

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边候选集验证（附近3公里内的咖啡店）
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois or len(around_search_result.pois) == 0:
        print(f"❌ 未找到���合条件的POI")
        return False

    # 检查返回POI数量是否>=8
    poi_count = len(around_search_result.pois)
    if poi_count < min_poi_count:
        print(f"❌ 返回POI数量{poi_count}个，少于{min_poi_count}个")
        return False
    print(f"✅ 返回POI数量{poi_count}个，符合要求（>= {min_poi_count}个）")

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

    # 步骤2: POI信息获取
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 骑行时间与距离验证（<= 12分钟且<= 2600米）
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取骑行时长")
        return False

    bicycling_duration = bicycling_result.total_duration_seconds
    if bicycling_duration > max_bicycling_duration:
        print(f"❌ 骑行时长{bicycling_duration}秒，超过{max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 骑行时长{bicycling_duration}秒，符合要求（<= {max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")

    if bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取骑行距离")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米，超过{max_bicycling_distance}米")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米，符合要求（<= {max_bicycling_distance}米）")

    # 步骤4: 用 maps_text_search + maps_search_detail 获取火车站坐标，去火车站驾车时间验证（<= 6分钟）
    text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if text_search_result.error:
        print(f"❌ 获取{station_address}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{station_address}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{station_address}坐标失败: {detail_result.error or '无location'}")
        return False

    station_location = detail_result.location
    print(f"✅ 获取{station_address}坐标: {station_location}")

    # 验证驾车时间（<= 6分钟）
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算到{station_address}驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{station_address}驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_to_station:
        print(f"❌ 到{station_address}驾车时长{driving_duration}秒，超过{max_driving_to_station}秒（{max_driving_to_station // 60}分钟）")
        return False
    print(f"✅ 到{station_address}驾车时长{driving_duration}秒，符合要求（<= {max_driving_to_station}秒，即{max_driving_to_station // 60}分钟）")

    # 步骤5: 用 maps_text_search + maps_search_detail 获取医院坐标，排除半径验证（distance_meters > 500）
    text_search_result = maps_text_search(keywords=hospital_address, city=hospital_city)
    if text_search_result.error:
        print(f"❌ 获取{hospital_address}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{hospital_address}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{hospital_address}坐标失败: {detail_result.error or '无location'}")
        return False

    hospital_location = detail_result.location
    print(f"✅ 获取{hospital_address}坐标: {hospital_location}")

    # 验证距离（distance_meters > 500）
    distance_result = maps_distance(origins=poi_location, destination=hospital_location)
    if distance_result.error:
        print(f"❌ 计算到{hospital_address}距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取到{hospital_address}距离")
        return False

    distance_meters = distance_result.results[0].distance_meters
    if distance_meters <= min_exclusion_distance:
        print(f"❌ 到{hospital_address}距离{distance_meters}米，未超过{min_exclusion_distance}米")
        return False
    print(f"✅ 到{hospital_address}距离{distance_meters}米，符合要求（> {min_exclusion_distance}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 628.py 文件...\n")
    result = verify_poi(poi_id="B0J2KL0BVP")
    print(f"\n验证结果: {result}")
