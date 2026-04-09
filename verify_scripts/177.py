"""
输入：B0K3R4XH4Z
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近3000米内酒吧：调用 maps_around_search(location='116.354206,39.925014', radius='3000', keywords='酒吧')，验证返回pois中包含目标POI id=B0K3R4XH4Z。
2) 酒吧类型与坐标：调用 maps_search_detail(id='B0K3R4XH4Z') 获取location，作为后续计算的destination坐标。
3) 从出发地到酒吧最大骑行距离1200米：调用 maps_bicycling_by_coordinates(origin='116.354206,39.925014', destination='116.357736,39.926989')，验证 total_distance_meters<=1200。
4) 酒吧到指定公交站“阜成门内(公交站)”最大直线距离500米：
- 调用 maps_text_search(keywords='阜成门内公交站', city='北京', citylimit='true') 得到公交站POI id=BV10000069；再调用 maps_search_detail(id='BV10000069') 获取其location='116.359262,39.923715'。
- 调用 maps_distance(origins='116.357736,39.926989', destination='116.359262,39.923715')，验证 distance_meters<=500。
5) 酒吧周围1200米内存在地铁站：调用 maps_around_search(location='116.357736,39.926989', radius='1200', keywords='地铁站')，验证 pois数量>=1。
6) 酒吧到最近地铁站步行时间<=20分钟：对上一步返回的每个地铁站POI，调用 maps_walking_by_coordinates(origin='116.357736,39.926989', destination=地铁站location)，取 total_duration_seconds 最小值min_t，验证 min_t<=1200秒。
7) 酒吧到首都机场T3驾车时间<=50分钟：调用 maps_geo(address='首都机场T3航站楼', city='北京') 获取location='116.615430,40.054731'，再调用 maps_driving_by_coordinates(origin='116.357736,39.926989', destination='116.615430,40.054731')，验证 total_duration_seconds<=3000秒。
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
    target_poi_id: str = "B0K3R4XH4Z",
    user_location: str = "116.354206,39.925014",
    radius: str = "3000",
    keywords: str = "酒吧",
    max_bicycling_distance: int = 1200,
    bus_station_keywords: str = "阜成门内公交站",
    bus_station_city: str = "北京",
    bus_station_citylimit: str = "true",
    bus_station_poi_id: str = "BV10000069",
    max_distance_to_bus_station: int = 500,
    subway_search_radius: str = "1200",
    subway_keywords: str = "地铁站",
    max_walking_time_to_subway: int = 1200,
    airport_address: str = "首都机场T3航站楼",
    airport_city: str = "北京",
    max_driving_time_to_airport: int = 3000
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        max_bicycling_distance: 最大骑行距离（米）
        bus_station_keywords: 公交站搜索关键词
        bus_station_city: 公交站所在城市
        bus_station_citylimit: 是否限制城市
        bus_station_poi_id: 公交站POI ID
        max_distance_to_bus_station: 到公交站的最大直线距离（米）
        subway_search_radius: 地铁站搜索半径（米）
        subway_keywords: 地铁站搜索关键词
        max_walking_time_to_subway: 到地铁站的最大步行时间（秒）
        airport_address: 机场地址
        airport_city: 机场所在城市
        max_driving_time_to_airport: 到机场的最大驾车时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 附近3000米内酒吧
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

    # 步骤2: 酒吧类型与坐标
    print(f"\n步骤2: 获取酒吧坐标 - 查询POI ID: {target_poi_id}")
    poi_detail = maps_search_detail(id=target_poi_id)

    if poi_detail.error:
        print(f"步骤2失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print("步骤2失败: 未获取到POI坐标")
        return False

    poi_location = poi_detail.location
    print(f"步骤2通过: POI坐标为{poi_location}")

    # 步骤3: 从出发地到酒吧最大骑行距离1200米
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

    # 步骤4: 酒吧到指定公交站"阜成门内(公交站)"最大直线距离500米
    print(f"\n步骤4: 验证到指定公交站的直线距离不超过{max_distance_to_bus_station}米")
    bus_station_detail = maps_search_detail(id=bus_station_poi_id)

    if bus_station_detail.error:
        print(f"步骤4失败: 获取公交站坐标失败 - {bus_station_detail.error}")
        all_passed = False
    else:
        if not bus_station_detail.location:
            print("步骤4失败: 未获取到公交站坐标")
            all_passed = False
        else:
            bus_station_location = bus_station_detail.location
            distance_result = maps_distance(
                origins=poi_location,
                destination=bus_station_location
            )

            if distance_result.error:
                print(f"步骤4失败: 计算距离失败 - {distance_result.error}")
                all_passed = False
            else:
                if not distance_result.results or len(distance_result.results) == 0:
                    print("步骤4失败: 未获取到距离结果")
                    all_passed = False
                else:
                    distance = distance_result.results[0].distance_meters
                    if distance > max_distance_to_bus_station:
                        print(f"步骤4失败: 到公交站的距离{distance}米超过要求{max_distance_to_bus_station}米")
                        all_passed = False
                    else:
                        print(f"步骤4通过: 到公交站的距离{distance}米，满足要求（<={max_distance_to_bus_station}米）")

    # 步骤5: 酒吧周围1200米内存在地铁站
    print(f"\n步骤5: 验证周围{subway_search_radius}米内有{subway_keywords}")
    subway_around_result = maps_around_search(
        location=poi_location,
        radius=subway_search_radius,
        keywords=subway_keywords
    )

    if subway_around_result.error:
        print(f"步骤5失败: {subway_around_result.error}")
        all_passed = False
    else:
        if not subway_around_result.pois or len(subway_around_result.pois) == 0:
            print(f"步骤5失败: 未找到任何{subway_keywords}")
            all_passed = False
        else:
            subway_count = len(subway_around_result.pois)
            print(f"步骤5通过: 找到{subway_count}个{subway_keywords}，满足要求（数量>=1）")
            subway_pois = subway_around_result.pois  # 保存地铁站列表供步骤6使用

    # 步骤6: 酒吧到最近地铁站步行时间<=20分钟
    print(f"\n步骤6: 验证到最近地铁站步行时间不超过{max_walking_time_to_subway}秒（{max_walking_time_to_subway//60}分钟）")
    if 'subway_pois' not in locals() or not subway_pois:
        print("步骤6失败: 未获取到地铁站列表")
        all_passed = False
    else:
        min_walking_time = float('inf')
        for subway_poi in subway_pois:
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
            print("步骤6失败: 无法计算到任何地铁站的步行时间")
            all_passed = False
        else:
            if min_walking_time > max_walking_time_to_subway:
                print(f"步骤6失败: 到最近地铁站的步行时间{min_walking_time}秒超过要求{max_walking_time_to_subway}秒")
                all_passed = False
            else:
                print(f"步骤6通过: 到最近地铁站的步行时间{min_walking_time}秒，满足要求（<={max_walking_time_to_subway}秒）")

    # 步骤7: 酒吧到首都机场T3驾车时间<=50分钟
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
