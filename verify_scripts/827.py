"""
输入：B0KKVPRS0B
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近约束：调用 maps_around_search(location='110.348815,20.072306', radius='2500', keywords='民宿')，验证返回结果中包含目标poi_id=B0KKVPRS0B。
2) 最大骑行距离：调用 maps_bicycling_by_coordinates(origin='110.348815,20.072306', destination=目标POI坐标)，验证 total_distance_meters ≤ 2500。
3) 途径点附近200米内有指定公交站（POI类型A=公交站，指定站点=江南城公交站）：
- 以步骤2返回的 steps 中每个 step 的 to_coordinates 作为“途径点候选”；
- 对每个候选点调用 maps_around_search(location=该途径点坐标, radius='200', keywords='公交站')；
- 验证存在至少一个候选点的返回pois中包含 名称为“江南城(公交站)”（id=BV10291357）。
4) 到指定公交站点的最大步行距离：
- 调用 maps_text_search(keywords='白沙门公园公交站', city='海口', citylimit='true') 得到白沙门公园(公交站) id=BV10291147；再 maps_search_detail 获取其坐标；
- 调用 maps_walking_by_coordinates(origin=目标POI坐标, destination=白沙门公园(公交站)坐标)，验证 total_distance_meters ≤ 1600。
5) 到机场最大驾车时间：
- 调用 maps_text_search(keywords='美兰机场', city='海口', citylimit='true')，取“海口美兰国际机场”(id=B03820000A)；maps_search_detail 获取坐标；
- 调用 maps_driving_by_coordinates(origin=目标POI坐标, destination=机场坐标)，验证 total_duration_seconds ≤ 3000(50分钟)。
6) 两地到达时间差（绝对值小于指定分钟）：
- 调用 maps_search_detail('B038202CRQ') 获取“海口汽车东站”坐标；
- 调用 maps_walking_by_coordinates(origin='110.348815,20.072306', destination=目标POI坐标) 得到 t_walk；
- 调用 maps_driving_by_coordinates(origin=汽车东站坐标, destination=目标POI坐标) 得到 t_drive；
- 验证 |t_walk - t_drive| ≤ 120秒(2分钟)。
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
    target_poi_id: str = "B0KKVPRS0B",
    user_location: str = "110.348815,20.072306",
    radius: str = "2500",
    keywords: str = "民宿",
    max_bicycling_distance: int = 2500,
    bus_search_radius: str = "200",
    bus_keywords: str = "公交站",
    specific_bus_station_name: str = "江南城(公交站)",
    specific_bus_station_id: str = "BV10291357",
    park_bus_keywords: str = "白沙门公园公交站",
    park_bus_city: str = "海口",
    park_bus_citylimit: str = "true",
    park_bus_station_id: str = "BV10291147",
    max_walking_distance_to_park_bus: int = 1600,
    airport_keywords: str = "美兰机场",
    airport_city: str = "海口",
    airport_citylimit: str = "true",
    airport_id: str = "B03820000A",
    max_driving_time_to_airport: int = 3000,
    bus_station_id: str = "B038202CRQ",
    max_time_diff: int = 120
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
        specific_bus_station_id: 指定公交站ID
        park_bus_keywords: 公园公交站搜索关键词
        park_bus_city: 公园公交站所在城市
        park_bus_citylimit: 是否限制城市
        park_bus_station_id: 公园公交站ID
        max_walking_distance_to_park_bus: 到公园公交站的最大步行距离（米）
        airport_keywords: 机场搜索关键词
        airport_city: 机场所在城市
        airport_citylimit: 是否限制城市
        airport_id: 机场ID
        max_driving_time_to_airport: 到机场的最大驾车时间（秒）
        bus_station_id: 汽车东站ID
        max_time_diff: 最大时间差（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 附近约束
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

    # 步骤2: 最大骑行距离
    print(f"\n步骤2: 验证骑行距离不超过{max_bicycling_distance}米")
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if bicycling_result.error:
        print(f"步骤2失败: {bicycling_result.error}")
        all_passed = False
    else:
        if bicycling_result.total_distance_meters is None:
            print("步骤2失败: 未获取到骑行距离")
            all_passed = False
        else:
            bicycling_distance = bicycling_result.total_distance_meters
            if bicycling_distance > max_bicycling_distance:
                print(f"步骤2失败: 骑行距离{bicycling_distance}米超过要求{max_bicycling_distance}米")
                all_passed = False
            else:
                print(f"步骤2通过: 骑行距离{bicycling_distance}米，满足要求（<={max_bicycling_distance}米）")

    # 步骤3: 途径点附近200米内有指定公交站
    print(f"\n步骤3: 验证途径点附近{bus_search_radius}米内有指定公交站{specific_bus_station_name}")
    if bicycling_result.steps:
        found_specific_bus = False
        for i, step in enumerate(bicycling_result.steps):
            waypoint_location = step.to_coordinates
            bus_around_result = maps_around_search(
                location=waypoint_location,
                radius=bus_search_radius,
                keywords=bus_keywords
            )

            if not bus_around_result.error and bus_around_result.pois:
                for bus_poi in bus_around_result.pois:
                    if bus_poi.id == specific_bus_station_id:
                        print(f"步骤3通过: 途径点{i+1}（{waypoint_location}）附近找到指定公交站{specific_bus_station_name}")
                        found_specific_bus = True
                        break

            if found_specific_bus:
                break

        if not found_specific_bus:
            print(f"步骤3失败: 所有途径点附近均未找到指定公交站{specific_bus_station_name}")
            all_passed = False
    else:
        print("步骤3失败: 未获取到骑行路线步骤信息")
        all_passed = False

    # 步骤4: 到指定公交站点的最大步行距离
    print(f"\n步骤4: 验证到白沙门公园公交站的步行距离不超过{max_walking_distance_to_park_bus}米")
    park_bus_detail = maps_search_detail(id=park_bus_station_id)

    if park_bus_detail.error:
        print(f"步骤4失败: 获取白沙门公园公交站坐标失败 - {park_bus_detail.error}")
        all_passed = False
    else:
        if not park_bus_detail.location:
            print("步骤4失败: 未获取到白沙门公园公交站坐标")
            all_passed = False
        else:
            park_bus_location = park_bus_detail.location
            walking_result_to_park = maps_walking_by_coordinates(
                origin=poi_location,
                destination=park_bus_location
            )

            if walking_result_to_park.error:
                print(f"步骤4失败: 计算步行距离失败 - {walking_result_to_park.error}")
                all_passed = False
            else:
                if walking_result_to_park.total_distance_meters is None:
                    print("步骤4失败: 未获取到步行距离")
                    all_passed = False
                else:
                    walking_distance_to_park = walking_result_to_park.total_distance_meters
                    if walking_distance_to_park > max_walking_distance_to_park_bus:
                        print(f"步骤4失败: 到公交站的步行距离{walking_distance_to_park}米超过要求{max_walking_distance_to_park_bus}米")
                        all_passed = False
                    else:
                        print(f"步骤4通过: 到公交站的步行距离{walking_distance_to_park}米，满足要求（<={max_walking_distance_to_park_bus}米）")

    # 步骤5: 到机场最大驾车时间
    print(f"\n步骤5: 验证到机场的驾车时间不超过{max_driving_time_to_airport}秒（{max_driving_time_to_airport//60}分钟）")
    airport_detail = maps_search_detail(id=airport_id)

    if airport_detail.error:
        print(f"步骤5失败: 获取机场坐标失败 - {airport_detail.error}")
        all_passed = False
    else:
        if not airport_detail.location:
            print("步骤5失败: 未获取到机场坐标")
            all_passed = False
        else:
            airport_location = airport_detail.location
            driving_result_to_airport = maps_driving_by_coordinates(
                origin=poi_location,
                destination=airport_location
            )

            if driving_result_to_airport.error:
                print(f"步骤5失败: 计算驾车时间失败 - {driving_result_to_airport.error}")
                all_passed = False
            else:
                if driving_result_to_airport.total_duration_seconds is None:
                    print("步骤5失败: 未获取到驾车时间")
                    all_passed = False
                else:
                    driving_time_to_airport = driving_result_to_airport.total_duration_seconds
                    if driving_time_to_airport > max_driving_time_to_airport:
                        print(f"步骤5失败: 驾车时间{driving_time_to_airport}秒超过要求{max_driving_time_to_airport}秒")
                        all_passed = False
                    else:
                        print(f"步骤5通过: 驾车时间{driving_time_to_airport}秒，满足要求（<={max_driving_time_to_airport}秒）")

    # 步骤6: 两地到达时间差
    print(f"\n步骤6: 验证到达时间差不超过{max_time_diff}秒（{max_time_diff//60}分钟）")
    bus_station_detail = maps_search_detail(id=bus_station_id)

    if bus_station_detail.error:
        print(f"步骤6失败: 获取汽车东站坐标失败 - {bus_station_detail.error}")
        all_passed = False
    else:
        if not bus_station_detail.location:
            print("步骤6失败: 未获取到汽车东站坐标")
            all_passed = False
        else:
            bus_station_location = bus_station_detail.location

            # 从用户位置步行到POI的时间
            walking_to_poi = maps_walking_by_coordinates(
                origin=user_location,
                destination=poi_location
            )

            # 从汽车东站驾车到POI的时间
            driving_from_bus_station = maps_driving_by_coordinates(
                origin=bus_station_location,
                destination=poi_location
            )

            if walking_to_poi.error or walking_to_poi.total_duration_seconds is None:
                print("步骤6失败: 未获取到步行时间")
                all_passed = False
            elif driving_from_bus_station.error or driving_from_bus_station.total_duration_seconds is None:
                print("步骤6失败: 未获取到驾车时间")
                all_passed = False
            else:
                t_walk = walking_to_poi.total_duration_seconds
                t_drive = driving_from_bus_station.total_duration_seconds
                time_diff = abs(t_walk - t_drive)

                if time_diff > max_time_diff:
                    print(f"步骤6失败: 到达时间差{time_diff}秒超过要求{max_time_diff}秒（步行时间: {t_walk}秒, 驾车时间: {t_drive}秒）")
                    all_passed = False
                else:
                    print(f"步骤6通过: 到达时间差{time_diff}秒，满足要求（<={max_time_diff}秒）（步行时间: {t_walk}秒, 驾车时间: {t_drive}秒）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
