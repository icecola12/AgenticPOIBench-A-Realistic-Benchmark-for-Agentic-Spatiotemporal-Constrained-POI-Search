
"""
修改任务指令：你要去附近8公里内找一个政务服务中心。你打算办完事后马上打车去泰州站赶火车，所以从这个政务服务中心开车到泰州站的时间不能超过12分钟。为了省事，你还要求这个地方不能在"泰州市人民政府"直线距离500米范围内。你害羞且缺乏安全感，说话犹豫，不自信。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围验证：调用 maps_around_search，以用户坐标(119.990747,32.473663)为中心，radius=8000，keywords=政务服务中心；验证返回pois数量>0，且目标poi_id(B0JDD5WJIC)在pois列表中。同时获取目标POI的location。
2) 到火车站时间验证：调用 maps_text_search(keywords='泰州站', city='泰州') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取泰州站location_station；再调用 maps_driving_by_coordinates(origin=目标POI.location, destination=location_station)，验证总驾车时长<=12分钟(720秒)。
3) 排除半径验证：调用 maps_text_search(keywords='泰州市人民政府', city='泰州') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取location_gov；调用 maps_distance(origins=location_gov, destination=目标POI.location)，验证直线距离>500米。
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
    maps_driving_by_coordinates,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "119.990747,32.473663",
    search_radius: int = 8000,  # 8km
    keywords: str = "政务服务中心",
    station_address: str = "泰州站",
    station_city: str = "泰州",
    max_driving_duration_to_station: int = 720,  # 12 minutes = 720 seconds
    government_address: str = "泰州市人民政府",
    government_city: str = "泰州",
    min_distance_from_government: int = 500  # 500 meters
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边范围验证：调用 maps_around_search，验证返回pois数量>0，且目标poi_id在pois列表中。同时获取目标POI的location。
    2) 到火车站时间验证：调用 maps_text_search 获取 poi_id，再用 maps_search_detail 获取泰州站location；再调用 maps_driving_by_coordinates，验证总驾车时长<=12分钟(720秒)。
    3) 排除半径验证：调用 maps_text_search 获取 poi_id，再用 maps_search_detail 获取泰州市人民政府location；调用 maps_distance，验证直线距离>500米。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"119.990747,32.473663"
        search_radius: 搜索半径（米），默认8000（8公里）
        keywords: 搜索关键词，默认"政务服务中心"
        station_address: 火车站地址，默认"泰州站"
        station_city: 火车站所在城市，默认"泰州"
        max_driving_duration_to_station: 到火车站的最大驾车时长（秒），默认720（12分钟）
        government_address: 政府地址，默认"泰州市人民政府"
        government_city: 政府所在城市，默认"泰州"
        min_distance_from_government: 与政府的最小直线距离（米），默认500

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围验证（8公里内的政务服务中心）
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
    target_poi = None
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            target_poi = poi
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break

    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False

    # 获取目标POI的location
    if not target_poi.location:
        print(f"❌ 目标POI没有location信息")
        return False

    poi_location = target_poi.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤2: 到火车站时间验证
    text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if text_search_result.error:
        print(f"❌ 获取火车站坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到火车站坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取火车站坐标失败: {detail_result.error or '无location'}")
        return False

    station_location = detail_result.location
    print(f"✅ 获取火车站坐标: {station_location} ({station_address})")

    driving_result_to_station = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result_to_station.error:
        print(f"❌ 计算到火车站的驾车路线失败: {driving_result_to_station.error}")
        return False

    if driving_result_to_station.total_duration_seconds is None:
        print(f"❌ 无法获取到火车站的驾车时长")
        return False

    driving_duration_to_station = driving_result_to_station.total_duration_seconds
    if driving_duration_to_station > max_driving_duration_to_station:
        print(f"❌ 到火车站的驾车时长{driving_duration_to_station}秒，超过{max_driving_duration_to_station}秒（{max_driving_duration_to_station // 60}分钟）")
        return False
    print(f"✅ 到火车站的驾车时长{driving_duration_to_station}秒，符合要求（<= {max_driving_duration_to_station}秒，即{max_driving_duration_to_station // 60}分钟）")

    # 步骤3: 排除半径验证（不在泰州市人民政府500米范围内）
    text_search_result = maps_text_search(keywords=government_address, city=government_city)
    if text_search_result.error:
        print(f"❌ 获取政府坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到政府坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取政府坐标失败: {detail_result.error or '无location'}")
        return False

    government_location = detail_result.location
    print(f"✅ 获取政府坐标: {government_location} ({government_address})")

    distance_result = maps_distance(origins=government_location, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取直线距离")
        return False

    distance_from_government = distance_result.results[0].distance_meters
    if distance_from_government <= min_distance_from_government:
        print(f"❌ 与政府的直线距离{distance_from_government}米，不满足要求（必须>{min_distance_from_government}米）")
        return False
    print(f"✅ 与政府的直线距离{distance_from_government}米，符合要求（> {min_distance_from_government}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 710.py 文件...\n")
    result = verify_poi(poi_id="B0JDD5WJIC")
    print(f"\n验证结果: {result}")
