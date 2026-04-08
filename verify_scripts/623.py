
"""
修改任务指令：要找一个附近2.5km内的停车场，准备把车停好后再去办事。这个停车场周边300米内必须能找到ATM，方便你临时取点现金；而且从停车场步行到最近的公交站，距离不要超过150米。你还希望这个停车场不在"包公园"直线距离1.5km范围内，避免那一带周末太堵。你打算骑车过去，骑行时间必须在8分钟以内；另外你稍后要去赶高铁，所以从停车场开车到"合肥南站"的时间也得控制在15分钟内。你逻辑性强但没有耐心，希望高效沟通，讨厌废话。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束(附近2.5km内)：调用 maps_around_search(location=用户坐标117.277251,31.863669, radius=2500, keywords=停车场)，验证返回pois中包含目标poi_id=B0IKPHX7O1。
2) 目标POI基础信息：调用 maps_search_detail(id=B0IKPHX7O1) 获取目标停车场的location。
3) ATM邻近约束(300m内有ATM)：以目标停车场location为中心，调用 maps_around_search(location=目标location, radius=300, keywords=ATM)，验证结果pois数量>0。
4) 公交站邻近约束(150m)：以目标停车场location为中心，调用 maps_around_search(location=目标location, radius=150, keywords=公交站) 获取候选公交站，返回poi数量>0。
5) 排除半径约束(不在包公园1.5km内)：调用 maps_text_search(keywords=包公园, city=合肥) 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取包公园location；调用 maps_distance(origins=目标location, destination=包公园location)，验证distance_meters>1500。
6) 骑行时间约束(≤8分钟)：调用 maps_bicycling_by_coordinates(origin=用户坐标117.277251,31.863669, destination=目标location)，验证total_duration_seconds≤480。
7) 到高铁站驾车时间约束(≤15分钟到合肥南站)：调用 maps_text_search(keywords=合肥南站, city=合肥) 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取合肥南站location；调用 maps_driving_by_coordinates(origin=目标location, destination=合肥南站location)，验证total_duration_seconds≤900。
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
    user_location: str = "117.277251,31.863669",
    search_radius: int = 2500,  # 2.5km
    keywords: str = "停车场",
    atm_search_radius: int = 300,  # 300 meters
    atm_keywords: str = "ATM",
    bus_search_radius: int = 150,  # 150 meters
    bus_keywords: str = "公交站",
    exclusion_address: str = "包公园",
    exclusion_city: str = "合肥",
    min_exclusion_distance: int = 1500,  # 1.5km = 1500 meters
    max_bicycling_duration: int = 480,  # 8 minutes = 480 seconds
    station_address: str = "合肥南站",
    station_city: str = "合肥",
    max_driving_duration: int = 900  # 15 minutes = 900 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离约束(附近2.5km内)：验证返回pois中包含目标poi_id
    2) 目标POI基础信息：获取目标停车场的location
    3) ATM邻近约束(300m内有ATM)：验证结果pois数量>0
    4) 公交站邻近约束(150m)：验证返回poi数量>0
    5) 排除半径约束(不在包公园1.5km内)：调用 maps_text_search 获取 poi_id，再用 maps_search_detail 获取包公园坐标，验证distance_meters>1500
    6) 骑行时间约束(≤8分钟)：验证total_duration_seconds≤480
    7) 到高铁站驾车时间约束(≤15分钟到合肥南站)：调用 maps_text_search 获取 poi_id，再用 maps_search_detail 获取合肥南站坐标，验证total_duration_seconds≤900

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"117.277251,31.863669"
        search_radius: 搜索半径（米），默认2500（2.5公里）
        keywords: 搜索关键词，默认"停车场"
        atm_search_radius: ATM搜索半径（米），默认300
        atm_keywords: ATM搜索关键词，默认"ATM"
        bus_search_radius: 公交站搜索半径（米），默认150
        bus_keywords: 公交站搜索关键词，默认"公交站"
        exclusion_address: 排除区域地址，默认"包公园"
        exclusion_city: 排除区域所在城市，默认"合肥"
        min_exclusion_distance: 最小排除距离（米），默认1500（1.5公里）
        max_bicycling_duration: 最大骑行时长（秒），默认480（8分钟）
        station_address: 火车站地址，默认"合肥南站"
        station_city: 火车站所在城市，默认"合肥"
        max_driving_duration: 最大驾车时长（秒），默认900（15分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束(附近2.5km内的停车场)
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

    # 步骤2: 目标POI基础信息
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: ATM邻近约束(300m内有ATM)
    atm_search_result = maps_around_search(
        location=poi_location,
        radius=str(atm_search_radius),
        keywords=atm_keywords
    )
    if atm_search_result.error:
        print(f"❌ 搜索周边ATM失败: {atm_search_result.error}")
        return False

    if not atm_search_result.pois or len(atm_search_result.pois) == 0:
        print(f"❌ {atm_search_radius}米范围内未找到ATM")
        return False

    atm_count = len(atm_search_result.pois)
    print(f"✅ {atm_search_radius}米范围内找到{atm_count}个ATM，符合要求")

    # 步骤4: 公交站邻近约束(150m)
    bus_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_search_radius),
        keywords=bus_keywords
    )
    if bus_search_result.error:
        print(f"❌ 搜索周边公交站失败: {bus_search_result.error}")
        return False

    if not bus_search_result.pois or len(bus_search_result.pois) == 0:
        print(f"❌ {bus_search_radius}米范围内未找到公交站")
        return False

    bus_count = len(bus_search_result.pois)
    print(f"✅ {bus_search_radius}米范围内找到{bus_count}个公交站，符合要求")

    # 步骤5: 用 maps_text_search + maps_search_detail 获取包公园坐标，排除半径约束(不在包公园1.5km内)
    text_search_result = maps_text_search(keywords=exclusion_address, city=exclusion_city)
    if text_search_result.error:
        print(f"❌ 获取{exclusion_address}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{exclusion_address}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{exclusion_address}坐标失败: {detail_result.error or '无location'}")
        return False

    exclusion_location = detail_result.location
    print(f"✅ 获取{exclusion_address}坐标: {exclusion_location}")

    # 验证距离（distance_meters > 1500）
    distance_result = maps_distance(origins=poi_location, destination=exclusion_location)
    if distance_result.error:
        print(f"❌ 计算到{exclusion_address}距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取到{exclusion_address}距离")
        return False

    distance_meters = distance_result.results[0].distance_meters
    if distance_meters <= min_exclusion_distance:
        print(f"❌ 到{exclusion_address}距离{distance_meters}米，未超过{min_exclusion_distance}米（{min_exclusion_distance / 1000}公里）")
        return False
    print(f"✅ 到{exclusion_address}距离{distance_meters}米，符合要求（> {min_exclusion_distance}米，即{min_exclusion_distance / 1000}公里）")

    # 步骤6: 骑行时间约束(≤8分钟)
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

    # 步骤7: 用 maps_text_search + maps_search_detail 获取合肥南站坐标，到高铁站驾车时间约束(≤15分钟到合肥南站)
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

    # 验证驾车时间（<= 15分钟）
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算到{station_address}驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{station_address}驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到{station_address}驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_address}驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 623.py 文件...\n")
    result = verify_poi(poi_id="B0IKPHX7O1")
    print(f"\n验证结果: {result}")
