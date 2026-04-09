"""
输入：B0HK1U9581
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边数量验证：调用 maps_around_search(location='109.483392,30.309778', radius='8000', keywords='图书馆')，验证目标poi_id在pois中出现。
2) 目标类型验证：从步骤1的pois中确认目标POI为图书馆（由keywords=图书馆检索得到）。
3) 骑行距离上限：调用 maps_bicycling_by_coordinates(origin='109.483392,30.309778', destination=目标POI.location)，验证 total_distance_meters ≤ 1200。
4) 公交站候选集：调用 maps_around_search(location=目标POI.location, radius='1500', keywords='公交站') 获取公交站列表。
5) 公交站最小直线距离上限：对步骤4每个公交站，调用 maps_distance(origins=目标POI.location, destination=公交站.location)；取最小 distance_meters，验证 ≤ 200。
6) 公交站最小步行距离上限：对步骤4每个公交站，调用 maps_walking_by_coordinates(origin=目标POI.location, destination=公交站.location)；取最小 total_distance_meters，验证 ≤ 2200。
7) 到机场驾车时间上限：调用 maps_geo(address='恩施许家坪机场', city='恩施') 获取机场坐标 airport_loc；再调用 maps_driving_by_coordinates(origin=目标POI.location, destination=airport_loc)，验证 total_duration_seconds ≤ 480（8分钟）。
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
    maps_geo,
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
    target_poi_id: str = "B0HK1U9581",
    user_location: str = "109.483392,30.309778",
    radius: str = "8000",
    keywords: str = "图书馆",
    max_bicycling_distance: int = 1200,
    bus_search_radius: str = "1500",
    bus_keywords: str = "公交站",
    max_distance_to_bus: int = 200,
    max_walking_distance_to_bus: int = 2200,
    airport_address: str = "恩施许家坪机场",
    airport_city: str = "恩施",
    max_driving_time_to_airport: int = 480
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        max_bicycling_distance: 最大骑行距离（米）
        bus_search_radius: 公交站搜索半径（米）
        bus_keywords: 公交站搜索关键词
        max_distance_to_bus: 到最近公交站的最大直线距离（米）
        max_walking_distance_to_bus: 到最近公交站的最大步行距离（米）
        airport_address: 机场地址
        airport_city: 机场所在城市
        max_driving_time_to_airport: 到机场的最大驾车时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 周边数量验证
    print(f"步骤1: 验证附近{radius}米内的周边搜索约束 - 查询POI ID: {target_poi_id}")
    around_result = maps_around_search(
        location=user_location,
        radius=radius,
        keywords=keywords
    )

    if around_result.error:
        print(f"步骤1失败: {around_result.error}")
        return False

    if not around_result.pois:
        print("步骤1失败: 未找到任何POI")
        return False

    # 检查是否包含目标POI
    poi_ids = [poi.id for poi in around_result.pois]
    if target_poi_id not in poi_ids:
        print(f"步骤1失败: POI列表不包含目标POI ID '{target_poi_id}'")
        all_passed = False
    else:
        print(f"步骤1通过: POI列表中包含目标POI ID '{target_poi_id}'")

    # 步骤2: 目标类型验证
    print(f"\n步骤2: 验证目标POI为{keywords}类型")
    # 由于POI来自图书馆关键词检索，类型视为满足
    print(f"步骤2通过: 目标POI来自'{keywords}'关键词检索，类型验证通过")

    # 获取POI坐标（后续步骤需要）
    print(f"\n获取POI坐标 - 查询POI ID: {target_poi_id}")
    poi_detail = maps_search_detail(id=target_poi_id)

    if poi_detail.error:
        print(f"获取POI坐标失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print("获取POI坐标失败: 未获取到POI坐标")
        return False

    poi_location = poi_detail.location
    print(f"POI坐标: {poi_location}")

    # 步骤3: 骑行距离上限
    print(f"\n步骤3: 验证骑行距离不超过{max_bicycling_distance}米")
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if bicycling_result.error:
        print(f"步骤3失败: {bicycling_result.error}")
        all_passed = False
    else:
        if bicycling_result.total_distance_meters is None:
            print("步骤3失败: 未获取到骑行距离")
            all_passed = False
        else:
            bicycling_distance = bicycling_result.total_distance_meters
            if bicycling_distance > max_bicycling_distance:
                print(f"步骤3失败: 骑行距离{bicycling_distance}米超过要求{max_bicycling_distance}米")
                all_passed = False
            else:
                print(f"步骤3通过: 骑行距离{bicycling_distance}米，满足要求（<={max_bicycling_distance}米）")

    # 步骤4: 公交站候选集
    print(f"\n步骤4: 获取公交站候选集")
    bus_around_result = maps_around_search(
        location=poi_location,
        radius=bus_search_radius,
        keywords=bus_keywords
    )

    if bus_around_result.error:
        print(f"步骤4失败: {bus_around_result.error}")
        all_passed = False
        bus_pois = []
    else:
        bus_pois = bus_around_result.pois if bus_around_result.pois else []
        bus_count = len(bus_pois)
        print(f"步骤4通过: 找到{bus_count}个{bus_keywords}")

    # 步骤5: 公交站最小直线距离上限
    print(f"\n步骤5: 验证到最近公交站的直线距离不超过{max_distance_to_bus}米")
    if not bus_pois:
        print("步骤5失败: 未找到任何公交站")
        all_passed = False
    else:
        # 计算到每个公交站的直线距离，找到最小值
        min_distance = float('inf')
        for bus_poi in bus_pois:
            bus_detail = maps_search_detail(id=bus_poi.id)
            if bus_detail.error or not bus_detail.location:
                continue

            bus_location = bus_detail.location
            distance_result = maps_distance(
                origins=poi_location,
                destination=bus_location
            )

            if distance_result.error or not distance_result.results or len(distance_result.results) == 0:
                continue

            distance = distance_result.results[0].distance_meters
            if distance < min_distance:
                min_distance = distance

        if min_distance == float('inf'):
            print("步骤5失败: 无法计算到任何公交站的距离")
            all_passed = False
        elif min_distance > max_distance_to_bus:
            print(f"步骤5失败: 到最近公交站的距离{min_distance}米超过要求{max_distance_to_bus}米")
            all_passed = False
        else:
            print(f"步骤5通过: 到最近公交站的距离{min_distance}米，满足要求（<={max_distance_to_bus}米）")

    # 步骤6: 公交站最小步行距离上限
    print(f"\n步骤6: 验证到最近公交站的步行距离不超过{max_walking_distance_to_bus}米")
    if not bus_pois:
        print("步骤6失败: 未找到任何公交站")
        all_passed = False
    else:
        # 计算到每个公交站的步行距离，找到最小值
        min_walking_distance = float('inf')
        for bus_poi in bus_pois:
            bus_detail = maps_search_detail(id=bus_poi.id)
            if bus_detail.error or not bus_detail.location:
                continue

            bus_location = bus_detail.location
            walking_result = maps_walking_by_coordinates(
                origin=poi_location,
                destination=bus_location
            )

            if walking_result.error or walking_result.total_distance_meters is None:
                continue

            distance = walking_result.total_distance_meters
            if distance < min_walking_distance:
                min_walking_distance = distance

        if min_walking_distance == float('inf'):
            print("步骤6失败: 无法计算到任何公交站的步行距离")
            all_passed = False
        elif min_walking_distance > max_walking_distance_to_bus:
            print(f"步骤6失败: 到最近公交站的步行距离{min_walking_distance}米超过要求{max_walking_distance_to_bus}米")
            all_passed = False
        else:
            print(f"步骤6通过: 到最近公交站的步行距离{min_walking_distance}米，满足要求（<={max_walking_distance_to_bus}米）")

    # 步骤7: 到机场驾车时间上限
    print(f"\n步骤7: 验证到{airport_address}的驾车时间不超过{max_driving_time_to_airport}秒（{max_driving_time_to_airport//60}分钟）")
    geo_result = maps_geo(address=airport_address, city=airport_city)

    if geo_result.error:
        print(f"步骤7失败: 获取{airport_address}坐标失败 - {geo_result.error}")
        all_passed = False
    else:
        if not geo_result.results or len(geo_result.results) == 0:
            print(f"步骤7失败: 未找到{airport_address}坐标")
            all_passed = False
        else:
            airport_location = geo_result.results[0].location
            driving_result = maps_driving_by_coordinates(
                origin=poi_location,
                destination=airport_location
            )

            if driving_result.error:
                print(f"步骤7失败: 计算驾车时间失败 - {driving_result.error}")
                all_passed = False
            else:
                if driving_result.total_duration_seconds is None:
                    print("步骤7失败: 未获取到驾车时间")
                    all_passed = False
                else:
                    driving_time = driving_result.total_duration_seconds
                    if driving_time > max_driving_time_to_airport:
                        print(f"步骤7失败: 驾车时间{driving_time}秒超过要求{max_driving_time_to_airport}秒")
                        all_passed = False
                    else:
                        print(f"步骤7通过: 驾车时间{driving_time}秒，满足要求（<={max_driving_time_to_airport}秒）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")


if __name__ == "__main__":
    main()
