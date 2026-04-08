"""
输入：B0222028SA
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束(周边2km)：调用 maps_around_search(location='118.629852,37.44909', radius='2000', keywords='洗衣店')，验证返回pois中包含 target_poi_id='B0222028SA'。
2) 步行距离≤1700米：先用 maps_search_detail('B0222028SA')取目标坐标destination，然后调用 maps_walking_by_coordinates(origin='118.629852,37.44909', destination=destination) 验证 total_distance_meters ≤ 1700。
3) 骑行距离≤1700米：调用 maps_bicycling_by_coordinates(origin='118.629852,37.44909', destination=destination) 验证 total_distance_meters ≤ 1700。
4) 附近1000米内存在ATM：调用 maps_around_search(location=destination, radius='1000', keywords='ATM')，验证 pois 列表非空。
5) 洗衣店到最近ATM步行时间≤30分钟：对步骤4返回的每个ATM，调用 maps_walking_by_coordinates(origin=destination, destination=atm.location) 取最小 total_duration_seconds，验证 ≤ 1800。
6) 洗衣店到东营火车站驾车≤10分钟：调用 maps_geo(address='东营火车站', city='东营') 获取火车站坐标station_loc(工具返回为118.674633,37.433992)；再调用 maps_driving_by_coordinates(origin=destination, destination=station_loc) 验证 total_duration_seconds ≤ 600。
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
    target_poi_id: str = "B0222028SA",
    user_location: str = "118.629852,37.44909",
    radius: str = "2000",
    keywords: str = "洗衣店",
    max_walking_distance: int = 1700,
    max_bicycling_distance: int = 1700,
    atm_search_radius: str = "1000",
    atm_keywords: str = "ATM",
    max_walking_time_to_atm: int = 1800,
    station_address: str = "东营火车站",
    station_city: str = "东营",
    max_driving_time_to_station: int = 600
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        max_walking_distance: 最大步行距离（米）
        max_bicycling_distance: 最大骑行距离（米）
        atm_search_radius: ATM搜索半径（米）
        atm_keywords: ATM搜索关键词
        max_walking_time_to_atm: 到ATM的最大步行时间（秒）
        station_address: 火车站地址
        station_city: 火车站所在城市
        max_driving_time_to_station: 到火车站的最大驾车时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 距离约束(周边2km)
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

    # 步骤2: 步行距离≤1700米
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

    # 步骤3: 骑行距离≤1700米
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

    # 步骤4: 附近1000米内存在ATM
    print(f"\n步骤4: 验证附近{atm_search_radius}米内存在{atm_keywords}")
    atm_around_result = maps_around_search(
        location=poi_location,
        radius=atm_search_radius,
        keywords=atm_keywords
    )

    if atm_around_result.error:
        print(f"步骤4失败: {atm_around_result.error}")
        all_passed = False
    else:
        if not atm_around_result.pois or len(atm_around_result.pois) == 0:
            print(f"步骤4失败: 未找到任何{atm_keywords}")
            all_passed = False
        else:
            atm_count = len(atm_around_result.pois)
            print(f"步骤4通过: 找到{atm_count}个{atm_keywords}，满足要求（数量>0）")
            atm_pois = atm_around_result.pois

    # 步骤5: 洗衣店到最近ATM步行时间≤30分钟
    print(f"\n步骤5: 验证到最近ATM的步行时间不超过{max_walking_time_to_atm}秒（{max_walking_time_to_atm//60}分钟）")
    if 'atm_pois' not in locals() or not atm_pois:
        print("步骤5失败: 未找到ATM")
        all_passed = False
    else:
        # 计算到每个ATM的步行时间，找到最小值
        min_walking_time = float('inf')
        for atm_poi in atm_pois:
            atm_detail = maps_search_detail(id=atm_poi.id)
            if atm_detail.error or not atm_detail.location:
                continue

            atm_location = atm_detail.location
            walking_result_to_atm = maps_walking_by_coordinates(
                origin=poi_location,
                destination=atm_location
            )

            if walking_result_to_atm.error or walking_result_to_atm.total_duration_seconds is None:
                continue

            walking_time = walking_result_to_atm.total_duration_seconds
            if walking_time < min_walking_time:
                min_walking_time = walking_time

        if min_walking_time == float('inf'):
            print("步骤5失败: 无法计算到任何ATM的步行时间")
            all_passed = False
        elif min_walking_time > max_walking_time_to_atm:
            print(f"步骤5失败: 到最近ATM的步行时间{min_walking_time}秒超过要求{max_walking_time_to_atm}秒")
            all_passed = False
        else:
            print(f"步骤5通过: 到最近ATM的步行时间{min_walking_time}秒，满足要求（<={max_walking_time_to_atm}秒）")

    # 步骤6: 洗衣店到东营火车站驾车≤10分钟
    print(f"\n步骤6: 验证到{station_address}的驾车时间不超过{max_driving_time_to_station}秒（{max_driving_time_to_station//60}分钟）")
    geo_result = maps_geo(address=station_address, city=station_city)

    if geo_result.error:
        print(f"步骤6失败: 获取{station_address}坐标失败 - {geo_result.error}")
        all_passed = False
    else:
        if not geo_result.results or len(geo_result.results) == 0:
            print(f"步骤6失败: 未找到{station_address}坐标")
            all_passed = False
        else:
            station_location = geo_result.results[0].location
            print(f"{station_address}坐标: {station_location}")

            driving_result = maps_driving_by_coordinates(
                origin=poi_location,
                destination=station_location
            )

            if driving_result.error:
                print(f"步骤6失败: 计算驾车时间失败 - {driving_result.error}")
                all_passed = False
            else:
                if driving_result.total_duration_seconds is None:
                    print("步骤6失败: 未获取到驾车时间")
                    all_passed = False
                else:
                    driving_time = driving_result.total_duration_seconds
                    if driving_time > max_driving_time_to_station:
                        print(f"步骤6失败: 驾车时间{driving_time}秒超过要求{max_driving_time_to_station}秒")
                        all_passed = False
                    else:
                        print(f"步骤6通过: 驾车时间{driving_time}秒，满足要求（<={max_driving_time_to_station}秒）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
