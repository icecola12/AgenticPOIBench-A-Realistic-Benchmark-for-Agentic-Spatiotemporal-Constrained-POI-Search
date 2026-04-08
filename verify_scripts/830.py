"""
输入：B0J2T56JT8
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围约束：调用 maps_around_search(location='116.362308,39.910052', radius='2000', keywords='图书馆')，验证返回pois中包含 target_poi_id='B0J2T56JT8'。
2) 类型与坐标：调用 maps_search_detail(id='B0J2T56JT8') 获取目标POI坐标 destination。
3) 最大骑行距离：调用 maps_bicycling_by_coordinates(origin='116.362308,39.910052', destination=destination)，验证 total_distance_meters ≤ 2000。
4) 到指定公交站直线距离：
- 用 maps_around_search(location=destination, radius='800', keywords='公交站') 找到“新文化街西口(公交站)”及其坐标 bus_loc；
- 调用 maps_distance(origins=destination, destination=bus_loc) 得到直线距离d_bus，验证 d_bus ≤ 300。
5) 最近地铁站直线距离（最小值约束）：
- 调用 maps_around_search(location=destination, radius='1000', keywords='地铁站') 获取1000米内地铁站列表；
- 对列表中每个地铁站，调用 maps_distance(origins=destination, destination=station_loc) 计算直线距离，取最小值 d_min；验证 d_min ≤ 1000。
6) 绕行总耗时增加不超过5分钟：
- 调用 maps_geo(address='北京西站', city='北京') 得到 A_loc；调用 maps_geo(address='天安门广场', city='北京') 得到 B_loc；
- 调用 maps_driving_by_coordinates(origin=A_loc, destination=destination) 得到 tA1；调用 maps_driving_by_coordinates(origin=destination, destination=B_loc) 得到 tA2；调用 maps_driving_by_coordinates(origin=A_loc, destination=B_loc) 得到 t_direct；
- 验证 (tA1.total_duration_seconds + tA2.total_duration_seconds - t_direct.total_duration_seconds) ≤ 300秒。
7) 途径点附近有公共厕所：调用 maps_around_search(location=destination, radius='500', keywords='公共厕所')，验证返回pois数量>0（或包含任一公共厕所POI）。
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
    target_poi_id: str = "B0J2T56JT8",
    user_location: str = "116.362308,39.910052",
    radius: str = "2000",
    keywords: str = "图书馆",
    max_bicycling_distance: int = 2000,
    bus_search_radius: str = "800",
    bus_keywords: str = "公交站",
    specific_bus_station_name: str = "新文化街西口(公交站)",
    max_distance_to_specific_bus: int = 300,
    subway_search_radius: str = "1000",
    subway_keywords: str = "地铁站",
    max_distance_to_subway: int = 1000,
    beijingxi_station_address: str = "北京西站",
    beijingxi_station_city: str = "北京",
    tiananmen_square_address: str = "天安门广场",
    tiananmen_square_city: str = "北京",
    max_detour_time: int = 300,
    toilet_search_radius: str = "500",
    toilet_keywords: str = "公共厕所"
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
        specific_bus_station_name: 指定公交站名称
        max_distance_to_specific_bus: 到指定公交站的最大直线距离（米）
        subway_search_radius: 地铁站搜索半径（米）
        subway_keywords: 地铁站搜索关键词
        max_distance_to_subway: 到地铁站的最大直线距离（米）
        beijingxi_station_address: 北京西站地址
        beijingxi_station_city: 北京西站所在城市
        tiananmen_square_address: 天安门广场地址
        tiananmen_square_city: 天安门广场所在城市
        max_detour_time: 最大绕路时间增量（秒）
        toilet_search_radius: 公共厕所搜索半径（米）
        toilet_keywords: 公共厕所搜索关键词

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 周边范围约束
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

    # 步骤2: 类型与坐标 - 获取目标POI坐标
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

    # 步骤3: 最大骑行距离
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

    # 步骤4: 到指定公交站直线距离
    print(f"\n步骤4: 验证到指定公交站'{specific_bus_station_name}'的直线距离不超过{max_distance_to_specific_bus}米")
    bus_around_result = maps_around_search(
        location=poi_location,
        radius=bus_search_radius,
        keywords=bus_keywords
    )

    if bus_around_result.error:
        print(f"步骤4失败: {bus_around_result.error}")
        all_passed = False
    else:
        if not bus_around_result.pois or len(bus_around_result.pois) == 0:
            print(f"步骤4失败: 未找到任何{bus_keywords}")
            all_passed = False
        else:
            # 查找指定的公交站
            specific_bus_found = False
            specific_bus_location = None
            for bus_poi in bus_around_result.pois:
                if specific_bus_station_name in bus_poi.name:
                    specific_bus_found = True
                    # 获取公交站坐标
                    bus_detail = maps_search_detail(id=bus_poi.id)
                    if not bus_detail.error and bus_detail.location:
                        specific_bus_location = bus_detail.location
                        break

            if not specific_bus_found:
                print(f"步骤4失败: 未找到指定公交站'{specific_bus_station_name}'")
                all_passed = False
            elif specific_bus_location is None:
                print(f"步骤4失败: 无法获取公交站'{specific_bus_station_name}'的坐标")
                all_passed = False
            else:
                # 计算直线距离
                distance_result = maps_distance(
                    origins=poi_location,
                    destination=specific_bus_location
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
                        if distance > max_distance_to_specific_bus:
                            print(f"步骤4失败: 到公交站的距离{distance}米超过要求{max_distance_to_specific_bus}米")
                            all_passed = False
                        else:
                            print(f"步骤4通过: 到公交站的距离{distance}米，满足要求（<={max_distance_to_specific_bus}米）")

    # 步骤5: 最近地铁站直线距离（最小值约束）
    print(f"\n步骤5: 验证最近地铁站直线距离不超过{max_distance_to_subway}米")
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
            # 计算到每个地铁站的直线距离，找到最小值
            min_distance = float('inf')
            for subway_poi in subway_around_result.pois:
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
                print("步骤5失败: 无法计算到任何地铁站的距离")
                all_passed = False
            elif min_distance > max_distance_to_subway:
                print(f"步骤5失败: 到最近地铁站的距离{min_distance}米超过要求{max_distance_to_subway}米")
                all_passed = False
            else:
                print(f"步骤5通过: 到最近地铁站的距离{min_distance}米，满足要求（<={max_distance_to_subway}米）")

    # 步骤6: 绕行总耗时增加不超过5分钟
    print(f"\n步骤6: 验证绕路时间增量不超过{max_detour_time}秒（{max_detour_time//60}分钟）")

    # 获取北京西站坐标
    beijingxi_result = maps_geo(address=beijingxi_station_address, city=beijingxi_station_city)
    if beijingxi_result.error:
        print(f"步骤6失败: 获取{beijingxi_station_address}坐标失败 - {beijingxi_result.error}")
        all_passed = False
    else:
        if not beijingxi_result.results or len(beijingxi_result.results) == 0:
            print(f"步骤6失败: 未找到{beijingxi_station_address}坐标")
            all_passed = False
        else:
            beijingxi_location = beijingxi_result.results[0].location

            # 获取天安门广场坐标
            tiananmen_result = maps_geo(address=tiananmen_square_address, city=tiananmen_square_city)
            if tiananmen_result.error:
                print(f"步骤6失败: 获取{tiananmen_square_address}坐标失败 - {tiananmen_result.error}")
                all_passed = False
            else:
                if not tiananmen_result.results or len(tiananmen_result.results) == 0:
                    print(f"步骤6失败: 未找到{tiananmen_square_address}坐标")
                    all_passed = False
                else:
                    tiananmen_location = tiananmen_result.results[0].location

                    # 计算北京西站到图书馆的驾车时间
                    driving_a1 = maps_driving_by_coordinates(
                        origin=beijingxi_location,
                        destination=poi_location
                    )

                    # 计算图书馆到天安门广场的驾车时间
                    driving_a2 = maps_driving_by_coordinates(
                        origin=poi_location,
                        destination=tiananmen_location
                    )

                    # 计算北京西站直接到天安门广场的驾车时间
                    driving_direct = maps_driving_by_coordinates(
                        origin=beijingxi_location,
                        destination=tiananmen_location
                    )

                    if (driving_a1.error or driving_a1.total_duration_seconds is None or
                        driving_a2.error or driving_a2.total_duration_seconds is None or
                        driving_direct.error or driving_direct.total_duration_seconds is None):
                        print("步骤6失败: 计算驾车时间失败")
                        all_passed = False
                    else:
                        t_a1 = driving_a1.total_duration_seconds
                        t_a2 = driving_a2.total_duration_seconds
                        t_direct = driving_direct.total_duration_seconds
                        detour_time = t_a1 + t_a2 - t_direct

                        if detour_time > max_detour_time:
                            print(f"步骤6失败: 绕路时间增量{detour_time}秒超过要求{max_detour_time}秒（t_a1={t_a1}秒, t_a2={t_a2}秒, t_direct={t_direct}秒）")
                            all_passed = False
                        else:
                            print(f"步骤6通过: 绕路时间增量{detour_time}秒，满足要求（<={max_detour_time}秒）（t_a1={t_a1}秒, t_a2={t_a2}秒, t_direct={t_direct}秒）")

    # 步骤7: 途径点附近有公共厕所
    print(f"\n步骤7: 验证附近{toilet_search_radius}米内有{toilet_keywords}")
    toilet_around_result = maps_around_search(
        location=poi_location,
        radius=toilet_search_radius,
        keywords=toilet_keywords
    )

    if toilet_around_result.error:
        print(f"步骤7失败: {toilet_around_result.error}")
        all_passed = False
    else:
        if not toilet_around_result.pois or len(toilet_around_result.pois) == 0:
            print(f"步骤7失败: 附近未找到{toilet_keywords}")
            all_passed = False
        else:
            toilet_count = len(toilet_around_result.pois)
            print(f"步骤7通过: 附近找到{toilet_count}个{toilet_keywords}，满足要求（数量>0）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
