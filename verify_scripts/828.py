"""
输入：B0L6U713F7
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边约束（附近2000米）：调用 maps_around_search(location='116.353136,39.910949', radius='2000', keywords='酒吧')，验证返回pois中包含 target_poi_id='B0L6U713F7'。
2) 驾车距离约束（≤3公里）：先调用 maps_search_detail('B0L6U713F7') 获取目标坐标dest；调用 maps_driving_by_coordinates(origin='116.353136,39.910949', destination=dest) 获取 total_distance_meters，验证 ≤3000。
3) 指定公交站直线距离约束（缸瓦市公交站≤200米）：调用 maps_text_search(keywords='缸瓦市公交站', city='北京', citylimit='true') 得到poi_id='BV10001841'；调用 maps_search_detail('BV10001841') 得到公交站坐标bus_loc；调用 maps_search_detail('B0L6U713F7') 得到酒吧坐标bar_loc；调用 maps_distance(origins=bar_loc, destination=bus_loc) 验证 distance_meters ≤200。
4) 附近1000米内地铁站的最小步行时间约束（≤12分钟）：调用 maps_search_detail('B0L6U713F7') 得到bar_loc；调用 maps_around_search(location=bar_loc, radius='1000', keywords='地铁站') 得到候选地铁站列表；对每个地铁站poi调用 maps_walking_by_coordinates(origin=bar_loc, destination=station_loc) 取最小 total_duration_seconds，验证 ≤720。
5) 到复兴门地铁站步行时间约束（≤18分钟）：调用 maps_text_search(keywords='复兴门(地铁站)', city='北京', citylimit='true') 得到poi_id='BV10007375'；调用 maps_search_detail('BV10007375') 得到fxm_loc；调用 maps_walking_by_coordinates(origin=bar_loc, destination=fxm_loc) 验证 total_duration_seconds ≤1080。
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
    target_poi_id: str = "B0L6U713F7",
    user_location: str = "116.353136,39.910949",
    radius: str = "2000",
    keywords: str = "酒吧",
    max_driving_distance: int = 3000,
    bus_station_keywords: str = "缸瓦市公交站",
    bus_station_city: str = "北京",
    bus_station_citylimit: str = "true",
    bus_station_poi_id: str = "BV10001841",
    max_distance_to_bus_station: int = 200,
    subway_search_radius: str = "1000",
    subway_keywords: str = "地铁站",
    max_walking_time_to_subway: int = 720,  # 12分钟
    fxm_subway_keywords: str = "复兴门(地铁站)",
    fxm_subway_city: str = "北京",
    fxm_subway_citylimit: str = "true",
    fxm_subway_poi_id: str = "BV10007375",
    max_walking_time_to_fxm: int = 1080  # 18分钟
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        max_driving_distance: 最大驾车距离（米）
        bus_station_keywords: 公交站搜索关键词
        bus_station_city: 公交站所在城市
        bus_station_citylimit: 是否限制城市
        bus_station_poi_id: 公交站POI ID
        max_distance_to_bus_station: 到公交站的最大直线距离（米）
        subway_search_radius: 地铁站搜索半径（米）
        subway_keywords: 地铁站搜索关键词
        max_walking_time_to_subway: 到地铁站的最大步行时间（秒）
        fxm_subway_keywords: 复兴门地铁站搜索关键词
        fxm_subway_city: 复兴门地铁站所在城市
        fxm_subway_citylimit: 是否限制城市
        fxm_subway_poi_id: 复兴门地铁站POI ID
        max_walking_time_to_fxm: 到复兴门地铁站的最大步行时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 周边约束（附近2000米）
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

    # 步骤2: 驾车距离约束（≤3公里）
    print(f"\n步骤2: 验证驾车距离不超过{max_driving_distance}米")
    driving_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if driving_result.error:
        print(f"步骤2失败: {driving_result.error}")
        all_passed = False
    else:
        if driving_result.total_distance_meters is None:
            print("步骤2失败: 未获取到驾车距离")
            all_passed = False
        else:
            driving_distance = driving_result.total_distance_meters
            if driving_distance > max_driving_distance:
                print(f"步骤2失败: 驾车距离{driving_distance}米超过要求{max_driving_distance}米")
                all_passed = False
            else:
                print(f"步骤2通过: 驾车距离{driving_distance}米，满足要求（<={max_driving_distance}米）")

    # 步骤3: 指定公交站直线距离约束（缸瓦市公交站≤200米）
    print(f"\n步骤3: 验证到指定公交站的直线距离不超过{max_distance_to_bus_station}米")
    bus_station_detail = maps_search_detail(id=bus_station_poi_id)

    if bus_station_detail.error:
        print(f"步骤3失败: 获取公交站坐标失败 - {bus_station_detail.error}")
        all_passed = False
    else:
        if not bus_station_detail.location:
            print("步骤3失败: 未获取到公交站坐标")
            all_passed = False
        else:
            bus_station_location = bus_station_detail.location
            distance_result = maps_distance(
                origins=poi_location,
                destination=bus_station_location
            )

            if distance_result.error:
                print(f"步骤3失败: 计算距离失败 - {distance_result.error}")
                all_passed = False
            else:
                if not distance_result.results or len(distance_result.results) == 0:
                    print("步骤3失败: 未获取到距离结果")
                    all_passed = False
                else:
                    distance = distance_result.results[0].distance_meters
                    if distance > max_distance_to_bus_station:
                        print(f"步骤3失败: 到公交站的距离{distance}米超过要求{max_distance_to_bus_station}米")
                        all_passed = False
                    else:
                        print(f"步骤3通过: 到公交站的距离{distance}米，满足要求（<={max_distance_to_bus_station}米）")

    # 步骤4: 附近1000米内地铁站的最小步行时间约束（≤12分钟）
    print(f"\n步骤4: 验证到地铁站的最小步行时间不超过{max_walking_time_to_subway}秒（{max_walking_time_to_subway//60}分钟）")
    subway_around_result = maps_around_search(
        location=poi_location,
        radius=subway_search_radius,
        keywords=subway_keywords
    )

    if subway_around_result.error:
        print(f"步骤4失败: {subway_around_result.error}")
        all_passed = False
    else:
        if not subway_around_result.pois or len(subway_around_result.pois) == 0:
            print(f"步骤4失败: 未找到任何{subway_keywords}")
            all_passed = False
        else:
            # 计算到每个地铁站的步行时间，找到最小值
            min_walking_time = float('inf')
            for subway_poi in subway_around_result.pois:
                subway_detail = maps_search_detail(id=subway_poi.id)
                if subway_detail.error or not subway_detail.location:
                    continue

                subway_location = subway_detail.location
                walking_result = maps_walking_by_coordinates(
                    origin=poi_location,
                    destination=subway_location
                )

                if walking_result.error or walking_result.total_duration_seconds is None:
                    continue

                walking_time = walking_result.total_duration_seconds
                if walking_time < min_walking_time:
                    min_walking_time = walking_time

            if min_walking_time == float('inf'):
                print("步骤4失败: 无法计算到任何地铁站的步行时间")
                all_passed = False
            elif min_walking_time > max_walking_time_to_subway:
                print(f"步骤4失败: 到最近地铁站的步行时间{min_walking_time}秒超过要求{max_walking_time_to_subway}秒")
                all_passed = False
            else:
                print(f"步骤4通过: 到最近地铁站的步行时间{min_walking_time}秒，满足要求（<={max_walking_time_to_subway}秒）")

    # 步骤5: 到复兴门地铁站步行时间约束（≤18分钟）
    print(f"\n步骤5: 验证到复兴门地铁站的步行时间不超过{max_walking_time_to_fxm}秒（{max_walking_time_to_fxm//60}分钟）")
    fxm_detail = maps_search_detail(id=fxm_subway_poi_id)

    if fxm_detail.error:
        print(f"步骤5失败: 获取复兴门地铁站坐标失败 - {fxm_detail.error}")
        all_passed = False
    else:
        if not fxm_detail.location:
            print("步骤5失败: 未获取到复兴门地铁站坐标")
            all_passed = False
        else:
            fxm_location = fxm_detail.location
            walking_result_to_fxm = maps_walking_by_coordinates(
                origin=poi_location,
                destination=fxm_location
            )

            if walking_result_to_fxm.error:
                print(f"步骤5失败: 计算步行时间失败 - {walking_result_to_fxm.error}")
                all_passed = False
            else:
                if walking_result_to_fxm.total_duration_seconds is None:
                    print("步骤5失败: 未获取到步行时间")
                    all_passed = False
                else:
                    walking_time_to_fxm = walking_result_to_fxm.total_duration_seconds
                    if walking_time_to_fxm > max_walking_time_to_fxm:
                        print(f"步骤5失败: 到复兴门地铁站的步行时间{walking_time_to_fxm}秒超过要求{max_walking_time_to_fxm}秒")
                        all_passed = False
                    else:
                        print(f"步骤5通过: 到复兴门地铁站的步行时间{walking_time_to_fxm}秒，满足要求（<={max_walking_time_to_fxm}秒）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")


if __name__ == "__main__":
    main()
