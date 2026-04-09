
"""
修改任务指令：你要在附近3000米以内找一家酒店。你打算开车过去，所以从你这里到酒店的驾车距离不能超过2公里，同时你也可能骑共享单车过去，骑行距离也得不超过2000米。酒店离"双鸭山火车站(公交站)"的直线距离要在350米以内。并且酒店周围1500米范围内的公交站里，离酒店走路最近公交站的步行距离不能超过1700米，同时酒店到这些公交站的最近直线距离不能超过50米。你健谈外向，乐观，乐于合作。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近3000米以内（周边搜到即满足）：调用 maps_around_search(location='131.146615,46.657504', radius='3000', keywords='酒店')，验证返回pois中包含 target_poi_id=B0LGV7UPS6。
2) 驾车距离≤2公里：调用 maps_search_detail('B0LGV7UPS6') 取location=L；调用 maps_driving_by_coordinates(origin='131.146615,46.657504', destination=L)，验证 total_distance_meters ≤ 2000。
3) 骑行距离≤2000米：调用 maps_bicycling_by_coordinates(origin='131.146615,46.657504', destination=L)，验证 total_distance_meters ≤ 2000。
4) 到指定公交站" 双鸭山火车站(公交站) "直线距离≤350米：调用 maps_text_search(keywords='双鸭山火车站(公交站)', city='双鸭山') 取 poi_id，再 maps_search_detail(id=poi_id) 得到 S；调用 maps_distance(origins=L, destination=S)，验证 distance_meters ≤ 350。
5) 酒店周围1500米内公交站的最近步行距离≤1700米：调用 maps_around_search(location=L, radius='1500', keywords='公交站') 得到一组站点{Pi}；对每个Pi调用 maps_walking_by_coordinates(origin=L, destination=Pi.location) 得到 poi_id，再 maps_search_detail(id=poi_id) 得到 步行距离di，取 min(di) ≤ 1700。
6) 酒店到上述1500米内公交站的最近直线距离≤50米：对同一组{Pi}，对每个Pi调用 maps_distance(origins=L, destination=Pi.location) 得到直线距离ei，取 min(ei) ≤ 50。
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
    maps_driving_by_coordinates,
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "131.146615,46.657504",
    search_radius: int = 3000,
    keywords: str = "酒店",
    max_driving_distance: int = 2000,  # 2 km = 2000 meters
    max_bicycling_distance: int = 2000,  # 2000 meters
    specific_bus_stop_name: str = "双鸭山火车站(公交站)",
    specific_bus_stop_city: str = "双鸭山",
    max_specific_bus_stop_distance: int = 350,  # 350 meters
    bus_stop_search_radius: int = 1500,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_walking_distance: int = 1700,  # 1700 meters
    max_bus_stop_straight_distance: int = 50  # 50 meters
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近3000米以内：调用 maps_around_search，验证返回pois中包含target_poi_id。
    2) 驾车距离≤2公里：调用 maps_search_detail 取location，调用 maps_driving_by_coordinates，验证 total_distance_meters ≤ 2000。
    3) 骑行距离≤2000米：调用 maps_bicycling_by_coordinates，验证 total_distance_meters ≤ 2000。
    4) 到指定公交站直线距离≤350米：调用得到公交站坐标，调用 maps_distance，验证 distance_meters ≤ 350。
    5) 酒店周围1500米内公交站的最近步行距离≤1700米：调用 maps_around_search 得到公交站列表，对每个调用 maps_walking_by_coordinates，取最小值，验证 ≤ 1700。
    6) 酒店到上述1500米内公交站的最近直线距离≤50米：对同一组公交站，对每个调用 maps_distance，取最小值，验证 ≤ 50。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"131.146615,46.657504"
        search_radius: 搜索半径（米），默认3000
        keywords: 搜索关键词，默认"酒店"
        max_driving_distance: 最大驾车距离（米），默认2000
        max_bicycling_distance: 最大骑行距离（米），默认2000
        specific_bus_stop_name: 指定公交站名称，默认"双鸭山火车站(公交站)"
        specific_bus_stop_city: 指定公交站所在城市，默认"双鸭山"
        max_specific_bus_stop_distance: 到指定公交站最大直线距离（米），默认350
        bus_stop_search_radius: 公交站搜索半径（米），默认1500
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_walking_distance: 到公交站最大步行距离（米），默认1700
        max_bus_stop_straight_distance: 到公交站最大直线距离（米），默认50

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近3000米以内
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

    # 步骤2: 获取目标POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 驾车距离≤2公里
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False

    driving_distance = driving_result.total_distance_meters
    if driving_distance > max_driving_distance:
        print(f"❌ 驾车距离{driving_distance}米，超过{max_driving_distance}米")
        return False
    print(f"✅ 驾车距离{driving_distance}米，符合要求（<= {max_driving_distance}米）")

    # 步骤4: 骑行距离≤2000米
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取骑行距离")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米，超过{max_bicycling_distance}米")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米，符合要求（<= {max_bicycling_distance}米）")

    # 步骤5: 到指定公交站"双鸭山火车站(公交站)"直线距离≤350米
    bus_stop_text_result = maps_text_search(keywords=specific_bus_stop_name, city=specific_bus_stop_city)
    if bus_stop_text_result.error:
        print(f"❌ 获取{specific_bus_stop_name}坐标失败: {bus_stop_text_result.error}")
        return False

    if not bus_stop_text_result.pois or len(bus_stop_text_result.pois) == 0:
        print(f"❌ 未找到{specific_bus_stop_name}坐标")
        return False

    first_poi_id = bus_stop_text_result.pois[0].id

    detail_result = maps_search_detail(id=first_poi_id)

    if detail_result.error:

        print(f"❌ 获取坐标失败: {detail_result.error}")

        return False

    if not detail_result.location:

        print("❌ 未获取到坐标")

        return False

    specific_bus_stop_location = detail_result.location
    print(f"✅ 获取{specific_bus_stop_name}坐标: {specific_bus_stop_location}")

    specific_distance_result = maps_distance(origins=poi_location, destination=specific_bus_stop_location)
    if specific_distance_result.error:
        print(f"❌ 计算到{specific_bus_stop_name}距离失败: {specific_distance_result.error}")
        return False

    if not specific_distance_result.results or len(specific_distance_result.results) == 0:
        print(f"❌ 未获取到到{specific_bus_stop_name}的距离信息")
        return False

    specific_distance = specific_distance_result.results[0].distance_meters
    if specific_distance > max_specific_bus_stop_distance:
        print(f"❌ 到{specific_bus_stop_name}直线距离{specific_distance}米，超过{max_specific_bus_stop_distance}米")
        return False
    print(f"✅ 到{specific_bus_stop_name}直线距离{specific_distance}米，符合要求（<= {max_specific_bus_stop_distance}米）")

    # 步骤6: 酒店周围1500米内公交站的最近步行距离≤1700米
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到公交站")
        return False

    print(f"✅ 找到{len(bus_stop_search_result.pois)}个公交站")

    # 计算到每个公交站的步行距离，找到最小值
    min_bus_stop_walking_distance = None
    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        bus_stop_walking_result = maps_walking_by_coordinates(
            origin=poi_location,
            destination=bus_stop.location
        )
        if bus_stop_walking_result.error or bus_stop_walking_result.total_distance_meters is None:
            continue

        distance = bus_stop_walking_result.total_distance_meters
        if min_bus_stop_walking_distance is None or distance < min_bus_stop_walking_distance:
            min_bus_stop_walking_distance = distance

    if min_bus_stop_walking_distance is None:
        print(f"❌ 无法计算到公交站的步行距离")
        return False

    if min_bus_stop_walking_distance > max_bus_stop_walking_distance:
        print(f"❌ 到最近公交站步行距离{min_bus_stop_walking_distance}米，超过{max_bus_stop_walking_distance}米")
        return False
    print(f"✅ 到最近公交站步行距离{min_bus_stop_walking_distance}米，符合要求（<= {max_bus_stop_walking_distance}米）")

    # 步骤7: 酒店到上述1500米内公交站的最近直线距离≤50米
    min_bus_stop_straight_distance = None
    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        bus_stop_distance_result = maps_distance(
            origins=poi_location,
            destination=bus_stop.location
        )
        if bus_stop_distance_result.error or not bus_stop_distance_result.results or len(bus_stop_distance_result.results) == 0:
            continue

        distance = bus_stop_distance_result.results[0].distance_meters
        if min_bus_stop_straight_distance is None or distance < min_bus_stop_straight_distance:
            min_bus_stop_straight_distance = distance

    if min_bus_stop_straight_distance is None:
        print(f"❌ 无法计算到公交站的直线距离")
        return False

    if min_bus_stop_straight_distance > max_bus_stop_straight_distance:
        print(f"❌ 到最近公交站直线距离{min_bus_stop_straight_distance}米，超过{max_bus_stop_straight_distance}米")
        return False
    print(f"✅ 到最近公交站直线距离{min_bus_stop_straight_distance}米，符合要求（<= {max_bus_stop_straight_distance}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 822.py 文件...\n")
    result = verify_poi(poi_id="B0LGV7UPS6")
    print(f"\n验证结果: {result}")
