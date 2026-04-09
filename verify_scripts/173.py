"""
输入：B0HBKZOSRL
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围约束：调用 maps_around_search(location='104.848915,26.588112', radius='8000', keywords='广场')，验证返回pois中包含目标poi_id=B0HBKZOSRL。
2) 出发地步行距离约束：调用 maps_search_detail('B0HBKZOSRL') 获取目标坐标dest；再调用 maps_walking_by_coordinates(origin='104.848915,26.588112', destination=dest)，验证 total_distance_meters ≤ 1000。
3) 到指定公交站直线距离约束：用 maps_text_search(keywords='人民广场(公交站)', city='六盘水', citylimit='true') 获取该站坐标bus_loc；调用 maps_distance(origins=dest, destination=bus_loc)，验证 distance_meters ≤ 300。
4) 到指定公交站步行距离约束：调用 maps_walking_by_coordinates(origin=dest, destination=bus_loc)，验证 total_distance_meters ≤ 1500。
5) 广场附近公交站供给约束：调用 maps_around_search(location=dest, radius='800', keywords='公交站')，验证 pois 数量 ≥ 1。
6) 到火车站驾车时间约束：调用 maps_geo(address='六盘水站', city='六盘水') 获取站点坐标station_loc；调用 maps_driving_by_coordinates(origin=dest, destination=station_loc)，验证 total_duration_seconds ≤ 480(8分钟)。
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
    target_poi_id: str = "B0HBKZOSRL",
    user_location: str = "104.848915,26.588112",
    radius: str = "8000",
    keywords: str = "广场",
    max_walking_distance: int = 1000,
    bus_station_keywords: str = "人民广场(公交站)",
    bus_station_city: str = "六盘水",
    bus_station_citylimit: str = "true",
    max_distance_to_bus_station: int = 300,
    max_walking_distance_to_bus_station: int = 1500,
    bus_search_radius: str = "800",
    bus_keywords: str = "公交站",
    min_bus_count: int = 1,
    station_address: str = "六盘水站",
    station_city: str = "六盘水",
    max_driving_time_to_station: int = 480
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        max_walking_distance: 最大步行距离（米）
        bus_station_keywords: 公交站搜索关键词
        bus_station_city: 公交站所在城市
        bus_station_citylimit: 是否限制城市
        max_distance_to_bus_station: 到公交站的最大直线距离（米）
        max_walking_distance_to_bus_station: 到公交站的最大步行距离（米）
        bus_search_radius: 公交站搜索半径（米）
        bus_keywords: 公交站搜索关键词
        min_bus_count: 最少公交站数量
        station_address: 火车站地址
        station_city: 火车站所在城市
        max_driving_time_to_station: 到火车站的最大驾车时间（秒）

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

    # 步骤2: 出发地步行距离约束
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

    # 步骤3和4需要公交站坐标，先获取公交站坐标
    print(f"\n获取公交站坐标 - 搜索关键词: {bus_station_keywords}")
    bus_text_result = maps_text_search(
        keywords=bus_station_keywords,
        city=bus_station_city,
        citylimit=bus_station_citylimit
    )

    if bus_text_result.error:
        print(f"获取公交站坐标失败: {bus_text_result.error}")
        print("步骤3失败: 无法获取公交站坐标")
        print("步骤4失败: 无法获取公交站坐标")
        return False

    if not bus_text_result.pois or len(bus_text_result.pois) == 0:
        print(f"获取公交站坐标失败: 未找到'{bus_station_keywords}'")
        print("步骤3失败: 无法获取公交站坐标")
        print("步骤4失败: 无法获取公交站坐标")
        return False

    bus_station_poi = bus_text_result.pois[0]
    bus_station_detail = maps_search_detail(id=bus_station_poi.id)

    if bus_station_detail.error or not bus_station_detail.location:
        print("获取公交站坐标失败: 获取详情失败")
        print("步骤3失败: 无法获取公交站坐标")
        print("步骤4失败: 无法获取公交站坐标")
        return False

    bus_station_location = bus_station_detail.location
    print(f"公交站坐标: {bus_station_location}")

    # 步骤3: 到指定公交站直线距离约束
    print(f"\n步骤3: 验证到指定公交站的直线距离不超过{max_distance_to_bus_station}米")
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

    # 步骤4: 到指定公交站步行距离约束
    print(f"\n步骤4: 验证到指定公交站的步行距离不超过{max_walking_distance_to_bus_station}米")
    bus_walking_result = maps_walking_by_coordinates(
        origin=poi_location,
        destination=bus_station_location
    )

    if bus_walking_result.error:
        print(f"步骤4失败: {bus_walking_result.error}")
        all_passed = False
    else:
        if bus_walking_result.total_distance_meters is None:
            print("步骤4失败: 未获取到步行距离")
            all_passed = False
        else:
            bus_walking_distance = bus_walking_result.total_distance_meters
            if bus_walking_distance > max_walking_distance_to_bus_station:
                print(f"步骤4失败: 到公交站的步行距离{bus_walking_distance}米超过要求{max_walking_distance_to_bus_station}米")
                all_passed = False
            else:
                print(f"步骤4通过: 到公交站的步行距离{bus_walking_distance}米，满足要求（<={max_walking_distance_to_bus_station}米）")

    # 步骤5: 广场附近公交站供给约束
    print(f"\n步骤5: 验证附近{bus_search_radius}米内有至少{min_bus_count}个{bus_keywords}")
    bus_around_result = maps_around_search(
        location=poi_location,
        radius=bus_search_radius,
        keywords=bus_keywords
    )

    if bus_around_result.error:
        print(f"步骤5失败: {bus_around_result.error}")
        all_passed = False
    else:
        if not bus_around_result.pois:
            bus_count = 0
        else:
            bus_count = len(bus_around_result.pois)

        if bus_count < min_bus_count:
            print(f"步骤5失败: 找到{bus_count}个{bus_keywords}，少于要求的最少数量{min_bus_count}")
            all_passed = False
        else:
            print(f"步骤5通过: 找到{bus_count}个{bus_keywords}，满足要求（>={min_bus_count}）")

    # 步骤6: 到火车站驾车时间约束
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
