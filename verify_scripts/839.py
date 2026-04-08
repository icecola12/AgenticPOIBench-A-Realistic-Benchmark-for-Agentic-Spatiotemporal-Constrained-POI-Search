"""
输入：B0FFGNJ2RE
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边候选数量验证（避免候选过少）：调用 maps_around_search(location='126.967804,46.641862', radius='2500', keywords='洗衣店')，验证返回pois数量 > 8，且包含 target_poi_id='B0FFGNJ2RE'。
2) 获取目标POI坐标：调用 maps_search_detail(id='B0FFGNJ2RE') 获取洗衣店坐标 dest。
3) 验证目标与出发地的可达性（步行/骑行/驾车距离上限）：
- 调用 maps_walking_by_coordinates(origin='126.967804,46.641862', destination=dest)，验证 total_distance_meters ≤ 1000。
- 调用 maps_bicycling_by_coordinates(origin='126.967804,46.641862', destination=dest)，验证 total_distance_meters ≤ 1000。
- 调用 maps_driving_by_coordinates(origin='126.967804,46.641862', destination=dest)，验证 total_distance_meters ≤ 2000（即≤2公里）。
4) 验证“附近800米内公交站 + 最小步行时间 + 最小直线距离”组合约束：
- 调用 maps_around_search(location=dest, radius='800', keywords='公交站') 获取公交站列表 stops。
- 对 stops 中每个公交站：
a) 调用 maps_distance(origins=stop, destination=dest)，取最小直线距离 d_min，验证 d_min ≤ 150。
b) 调用 maps_walking_by_coordinates(origin=dest, destination=stop.location)，取最小步行时间 t_min，验证 t_min ≤ 20分钟（即 total_duration_seconds ≤ 1200）。
c)得到最小直线距离 d_min，验证 d_min ≤ 150,得到最小步行时间 t_min，验证 t_min ≤ 20分钟（即 total_duration_seconds ≤ 1200）。
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
    target_poi_id: str = "B0FFGNJ2RE",
    user_location: str = "126.967804,46.641862",
    radius: str = "2500",
    keywords: str = "洗衣店",
    min_poi_count: int = 8,
    max_walking_distance: int = 1000,
    max_bicycling_distance: int = 1000,
    max_driving_distance: int = 2000,
    bus_search_radius: str = "800",
    bus_keywords: str = "公交站",
    max_distance_to_bus: int = 150,
    max_walking_time_to_bus: int = 1200
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        min_poi_count: 最少POI数量
        max_walking_distance: 最大步行距离（米）
        max_bicycling_distance: 最大骑行距离（米）
        max_driving_distance: 最大驾车距离（米）
        bus_search_radius: 公交站搜索半径（米）
        bus_keywords: 公交站搜索关键词
        max_distance_to_bus: 到公交站的最大直线距离（米）
        max_walking_time_to_bus: 到公交站的最大步行时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 周边候选数量验证
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

    poi_count = len(around_result.pois)
    if poi_count <= min_poi_count:
        print(f"步骤1失败: POI数量{poi_count}不大于要求的最少数量{min_poi_count}")
        return False

    # 检查是否包含目标POI
    poi_ids = [poi.id for poi in around_result.pois]
    if target_poi_id not in poi_ids:
        print(f"步骤1失败: POI列表不包含目标POI ID '{target_poi_id}'")
        all_passed = False
    else:
        print(f"步骤1通过: POI列表中包含目标POI ID '{target_poi_id}'，总共找到{poi_count}个POI")

    # 步骤2: 获取目标POI坐标
    print(f"\n步骤2: 获取目标POI坐标 - 查询POI ID: {target_poi_id}")
    poi_detail = maps_search_detail(id=target_poi_id)

    if poi_detail.error:
        print(f"步骤2失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print("步骤2失败: 未获取到POI坐标")
        return False

    poi_location = poi_detail.location
    print(f"步骤2通过: POI坐标为{poi_location}")

    # 步骤3: 验证目标与出发地的可达性
    print(f"\n步骤3: 验证步行距离不超过{max_walking_distance}米")
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if walking_result.error:
        print(f"步骤3失败: {walking_result.error}")
        all_passed = False
    else:
        if walking_result.total_distance_meters is None:
            print("步骤3失败: 未获取到步行距离")
            all_passed = False
        else:
            walking_distance = walking_result.total_distance_meters
            if walking_distance > max_walking_distance:
                print(f"步骤3失败: 步行距离{walking_distance}米超过要求{max_walking_distance}米")
                all_passed = False
            else:
                print(f"步骤3通过: 步行距离{walking_distance}米，满足要求（<={max_walking_distance}米）")

    print(f"\n步骤4: 验证骑行距离不超过{max_bicycling_distance}米")
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if bicycling_result.error:
        print(f"步骤4失败: {bicycling_result.error}")
        all_passed = False
    else:
        if bicycling_result.total_distance_meters is None:
            print("步骤4失败: 未获取到骑行距离")
            all_passed = False
        else:
            bicycling_distance = bicycling_result.total_distance_meters
            if bicycling_distance > max_bicycling_distance:
                print(f"步骤4失败: 骑行距离{bicycling_distance}米超过要求{max_bicycling_distance}米")
                all_passed = False
            else:
                print(f"步骤4通过: 骑行距离{bicycling_distance}米，满足要求（<={max_bicycling_distance}米）")

    print(f"\n步骤5: 验证驾车距离不超过{max_driving_distance}米")
    driving_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if driving_result.error:
        print(f"步骤5失败: {driving_result.error}")
        all_passed = False
    else:
        if driving_result.total_distance_meters is None:
            print("步骤5失败: 未获取到驾车距离")
            all_passed = False
        else:
            driving_distance = driving_result.total_distance_meters
            if driving_distance > max_driving_distance:
                print(f"步骤5失败: 驾车距离{driving_distance}米超过要求{max_driving_distance}米")
                all_passed = False
            else:
                print(f"步骤5通过: 驾车距离{driving_distance}米，满足要求（<={max_driving_distance}米）")

    # 步骤4: 验证"附近800米内公交站 + 最小步行时间 + 最小直线距离"组合约束
    print(f"\n步骤6: 验证附近{bus_search_radius}米内公交站约束")
    bus_around_result = maps_around_search(
        location=poi_location,
        radius=bus_search_radius,
        keywords=bus_keywords
    )

    if bus_around_result.error:
        print(f"步骤6失败: {bus_around_result.error}")
        all_passed = False
    else:
        if not bus_around_result.pois or len(bus_around_result.pois) == 0:
            print(f"步骤6失败: 未找到任何{bus_keywords}")
            all_passed = False
        else:
            # 计算最小直线距离和最小步行时间
            min_distance = float('inf')
            min_walking_time = float('inf')

            for bus_poi in bus_around_result.pois:
                bus_detail = maps_search_detail(id=bus_poi.id)
                if bus_detail.error or not bus_detail.location:
                    continue

                bus_location = bus_detail.location

                # 计算直线距离
                distance_result = maps_distance(
                    origins=poi_location,
                    destination=bus_location
                )

                if not distance_result.error and distance_result.results and len(distance_result.results) > 0:
                    distance = distance_result.results[0].distance_meters
                    if distance < min_distance:
                        min_distance = distance

                # 计算步行时间
                walking_result_to_bus = maps_walking_by_coordinates(
                    origin=poi_location,
                    destination=bus_location
                )

                if not walking_result_to_bus.error and walking_result_to_bus.total_duration_seconds is not None:
                    walking_time = walking_result_to_bus.total_duration_seconds
                    if walking_time < min_walking_time:
                        min_walking_time = walking_time

            # 验证最小直线距离
            if min_distance == float('inf'):
                print("步骤6失败: 无法计算到任何公交站的直线距离")
                all_passed = False
            elif min_distance > max_distance_to_bus:
                print(f"步骤6失败: 到最近公交站的直线距离{min_distance}米超过要求{max_distance_to_bus}米")
                all_passed = False
            else:
                print(f"步骤6通过: 到最近公交站的直线距离{min_distance}米，满足要求（<={max_distance_to_bus}米）")

            # 验证最小步行时间
            if min_walking_time == float('inf'):
                print("步骤6失败: 无法计算到任何公交站的步行时间")
                all_passed = False
            elif min_walking_time > max_walking_time_to_bus:
                print(f"步骤6失败: 到最近公交站的步行时间{min_walking_time}秒超过要求{max_walking_time_to_bus}秒")
                all_passed = False
            else:
                print(f"步骤6通过: 到最近公交站的步行时间{min_walking_time}秒，满足要求（<={max_walking_time_to_bus}秒）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
