"""
输入：B0LR0SMK8N
输出：True

验证方法：
1) 附近2000米内：调用 maps_around_search(location='113.406346,23.117579', radius='2000', keywords='电竞馆')，验证返回pois中包含 target_poi_id='B0LR0SMK8N'。
2) 到出发地最大步行距离≤1300米：调用 maps_walking_by_coordinates(origin='113.406346,23.117579', destination=POI.location)，验证 total_distance_meters ≤ 1300。
3) 到出发地最大驾车距离≤2公里：调用 maps_driving_by_coordinates(origin='113.406346,23.117579', destination=POI.location)，验证 total_distance_meters ≤ 2000。
4) 目标场所到附近1500米内地铁站的最小直线距离≤1000米：
a) 调用 maps_around_search(location=POI.location, radius='1500', keywords='地铁站') 获取候选地铁站列表S；
b) 将S中各站点location拼接为origins，调用 maps_distance(origins=origins, destination=POI.location)；
c) 取最小distance_meters，验证 ≤ 1000。
5) 目标场所到附近1500米内地铁站的最小步行时间≤16分钟：
a) 基于第4步的地铁站列表S，对每个站点调用 maps_walking_by_coordinates(origin=POI.location, destination=station.location)；
b) 取最小 total_duration_seconds，验证 ≤ 960。
6) 电竞馆附近500米内有ATM：调用 maps_around_search(location=POI.location, radius='500', keywords='ATM')，验证返回pois数量≥1。
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
    target_poi_id: str = "B0LR0SMK8N",
    user_location: str = "113.406346,23.117579",
    radius: str = "2000",
    keywords: str = "电竞馆",
    max_walking_distance: int = 1300,
    max_driving_distance: int = 2000,
    subway_search_radius: str = "1500",
    subway_keywords: str = "地铁站",
    max_distance_to_subway: int = 1000,
    max_walking_time_to_subway: int = 960,
    atm_search_radius: str = "500",
    atm_keywords: str = "ATM",
    min_atm_count: int = 1
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        max_walking_distance: 最大步行距离（米）
        max_driving_distance: 最大驾车距离（米）
        subway_search_radius: 地铁站搜索半径（米）
        subway_keywords: 地铁站搜索关键词
        max_distance_to_subway: 到地铁站的最大直线距离（米）
        max_walking_time_to_subway: 到地铁站的最大步行时间（秒）
        atm_search_radius: ATM搜索半径（米）
        atm_keywords: ATM搜索关键词
        min_atm_count: 最少ATM数量

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 附近2000米内
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

    # 步骤2: 到出发地最大步行距离≤1300米
    print(f"\n步骤2: 验证步行距离不超过{max_walking_distance}米")
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if walking_result.error:
        print(f"步骤2失败: {walking_result.error}")
        all_passed = False
    else:
        if walking_result.total_distance_meters is None:
            print("步骤2失败: 未获取到步行距离")
            all_passed = False
        else:
            walking_distance = walking_result.total_distance_meters
            if walking_distance > max_walking_distance:
                print(f"步骤2失败: 步行距离{walking_distance}米超过要求{max_walking_distance}米")
                all_passed = False
            else:
                print(f"步骤2通过: 步行距离{walking_distance}米，满足要求（<={max_walking_distance}米）")

    # 步骤3: 到出发地最大驾车距离≤2公里
    print(f"\n步骤3: 验证驾车距离不超过{max_driving_distance}米")
    driving_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if driving_result.error:
        print(f"步骤3失败: {driving_result.error}")
        all_passed = False
    else:
        if driving_result.total_distance_meters is None:
            print("步骤3失败: 未获取到驾车距离")
            all_passed = False
        else:
            driving_distance = driving_result.total_distance_meters
            if driving_distance > max_driving_distance:
                print(f"步骤3失败: 驾车距离{driving_distance}米超过要求{max_driving_distance}米")
                all_passed = False
            else:
                print(f"步骤3通过: 驾车距离{driving_distance}米，满足要求（<={max_driving_distance}米）")

    # 步骤4和5需要地铁站信息，先搜索地铁站
    print(f"\n搜索地铁站 - POI坐标: {poi_location}, 搜索半径: {subway_search_radius}米")
    subway_around_result = maps_around_search(
        location=poi_location,
        radius=subway_search_radius,
        keywords=subway_keywords
    )

    if subway_around_result.error:
        print(f"地铁站搜索失败: {subway_around_result.error}")
        print("步骤4失败: 无法获取地铁站信息")
        print("步骤5失败: 无法获取地铁站信息")
        all_passed = False
        subway_pois = []
    else:
        subway_pois = subway_around_result.pois if subway_around_result.pois else []
        subway_count = len(subway_pois)
        print(f"找到{subway_count}个地铁站")

    # 步骤4: 目标场所到附近1500米内地铁站的最小直线距离≤1000米
    print(f"\n步骤4: 验证到地铁站的最小直线距离不超过{max_distance_to_subway}米")
    if not subway_pois:
        print("步骤4失败: 未找到任何地铁站")
        all_passed = False
    else:
        min_distance = float('inf')
        for subway_poi in subway_pois:
            subway_detail = maps_search_detail(id=subway_poi.id)
            if subway_detail.error or not subway_detail.location:
                continue

            subway_location = subway_detail.location
            distance_result = maps_distance(
                origins=poi_location,
                destination=subway_location
            )

            if distance_result.error or not distance_result.results or len(distance_result.results) == 0:
                continue

            distance = distance_result.results[0].distance_meters
            if distance < min_distance:
                min_distance = distance

        if min_distance == float('inf'):
            print("步骤4失败: 无法计算到任何地铁站的距离")
            all_passed = False
        elif min_distance > max_distance_to_subway:
            print(f"步骤4失败: 到最近地铁站的距离{min_distance}米超过要求{max_distance_to_subway}米")
            all_passed = False
        else:
            print(f"步骤4通过: 到最近地铁站的距离{min_distance}米，满足要求（<={max_distance_to_subway}米）")

    # 步骤5: 目标场所到附近1500米内地铁站的最小步行时间≤16分钟
    print(f"\n步骤5: 验证到地铁站的最小步行时间不超过{max_walking_time_to_subway}秒（{max_walking_time_to_subway//60}分钟）")
    if not subway_pois:
        print("步骤5失败: 未找到任何地铁站")
        all_passed = False
    else:
        min_walking_time = float('inf')
        for subway_poi in subway_pois:
            subway_detail = maps_search_detail(id=subway_poi.id)
            if subway_detail.error or not subway_detail.location:
                continue

            subway_location = subway_detail.location
            walking_result_to_subway = maps_walking_by_coordinates(
                origin=poi_location,
                destination=subway_location
            )

            if walking_result_to_subway.error or walking_result_to_subway.total_duration_seconds is None:
                continue

            walking_time = walking_result_to_subway.total_duration_seconds
            if walking_time < min_walking_time:
                min_walking_time = walking_time

        if min_walking_time == float('inf'):
            print("步骤5失败: 无法获取到任何地铁站的步行时间")
            all_passed = False
        elif min_walking_time > max_walking_time_to_subway:
            print(f"步骤5失败: 到最近地铁站的步行时间{min_walking_time}秒超过要求{max_walking_time_to_subway}秒")
            all_passed = False
        else:
            print(f"步骤5通过: 到最近地铁站的步行时间{min_walking_time}秒，满足要求（<={max_walking_time_to_subway}秒）")

    # 步骤6: 电竞馆附近500米内有ATM
    print(f"\n步骤6: 验证附近{atm_search_radius}米内有至少{min_atm_count}个{atm_keywords}")
    atm_around_result = maps_around_search(
        location=poi_location,
        radius=atm_search_radius,
        keywords=atm_keywords
    )

    if atm_around_result.error:
        print(f"步骤6失败: {atm_around_result.error}")
        all_passed = False
    else:
        if not atm_around_result.pois:
            atm_count = 0
        else:
            atm_count = len(atm_around_result.pois)

        if atm_count < min_atm_count:
            print(f"步骤6失败: 找到{atm_count}个ATM，少于要求的最少数量{min_atm_count}")
            all_passed = False
        else:
            print(f"步骤6通过: 找到{atm_count}个ATM，满足要求（>={min_atm_count}）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
