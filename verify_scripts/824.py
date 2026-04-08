"""
修改任务指令：你想在附近2500米以内找一家电竞馆。你打算散场后去赶火车，所以这家电竞馆开车到西昌站的时间不能超过12分钟。另外你准备在建昌古城(公交站)坐车回去，因此电竞馆到建昌古城(公交站)的直线距离不能超过1500米；同时电竞馆步行到它附近1200米范围内的公交站，最近的那一个公交站步行距离不能超过900米。你还想路上顺便取点现金，所以从你到电竞馆的步行路线中需要存在300米范围内有ATM的途径点。你健谈外向，乐观，乐于合作。
输入：B0GKCKQTV7
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近约束：调用maps_around_search(location='102.271242,27.890317', radius='2500', keywords='电竞馆')，验证返回pois中包含目标poi_id='B0GKCKQTV7'。
2) POI类型校验：目标poi来自上一步“电竞馆”关键词周边检索结果，视为类型满足。
3) 到西昌站驾车时间：调用maps_search_detail('B034201L31')获取西昌站坐标=102.224060,27.877396；调用maps_search_detail('B0GKCKQTV7')获取电竞馆坐标=102.258680,27.893486；调用maps_driving_by_coordinates(origin='102.258680,27.893486', destination='102.224060,27.877396')得到total_duration_seconds=401，验证≤720秒(12分钟)。
4) 到建昌古城(公交站)直线距离：调用maps_search_detail('BV09202277')获取建昌古城(公交站)坐标=102.272079,27.891011；调用maps_distance(origins='102.272079,27.891011', destination='102.258680,27.893486')得到distance_meters=1346，验证≤1500米。
5) 最近公交站步行距离：调用maps_around_search(location='102.258680,27.893486', radius='1200', keywords='公交站')获取候选公交站列表；对每个公交站poi调用maps_walking_by_coordinates(origin='102.258680,27.893486', destination=公交站location)，取total_distance_meters最小值min_d；验证min_d≤900米。（示例最近点：宁远街口(公交站) id='BV10283101'，其步行距离=787米。）
6) 途径点附近有ATM（可验证实现）：先调用maps_walking_by_coordinates(origin='102.271242,27.890317', destination='102.258680,27.893486')获取steps；遍历steps中的任一from_coordinates或to_coordinates作为“途径点”候选，对该途径点调用maps_around_search(location=该坐标, radius='300', keywords='ATM')，验证返回pois非空。
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
    target_poi_id: str = "B0GKCKQTV7",
    user_location: str = "102.271242,27.890317",
    radius: str = "2500",
    keywords: str = "电竞馆",
    xichang_station_poi_id: str = "B034201L31",
    max_driving_time_to_station: int = 720,
    bus_station_poi_id: str = "BV09202277",
    max_distance_to_bus_station: int = 1500,
    bus_search_radius: str = "1200",
    bus_keywords: str = "公交站",
    max_walking_distance_to_bus: int = 900,
    atm_search_radius: str = "300",
    atm_keywords: str = "ATM"
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        xichang_station_poi_id: 西昌站POI ID
        max_driving_time_to_station: 到西昌站的最大驾车时间（秒）
        bus_station_poi_id: 建昌古城公交站POI ID
        max_distance_to_bus_station: 到建昌古城公交站的最大直线距离（米）
        bus_search_radius: 公交站搜索半径（米）
        bus_keywords: 公交站搜索关键词
        max_walking_distance_to_bus: 到最近公交站的最大步行距离（米）
        atm_search_radius: ATM搜索半径（米）
        atm_keywords: ATM搜索关键词

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

    # 步骤2: POI类型校验（基于步骤1的结果，视为满足）
    print(f"\n步骤2: POI类型校验 - 目标POI来自'{keywords}'关键词周边检索结果，视为类型满足")

    # 步骤3: 到西昌站驾车时间
    print(f"\n步骤3: 验证到西昌站驾车时间不超过{max_driving_time_to_station}秒（{max_driving_time_to_station//60}分钟）")

    # 获取西昌站坐标
    station_detail = maps_search_detail(id=xichang_station_poi_id)
    if station_detail.error:
        print(f"步骤3失败: 获取西昌站坐标失败 - {station_detail.error}")
        all_passed = False
    else:
        if not station_detail.location:
            print("步骤3失败: 未获取到西昌站坐标")
            all_passed = False
        else:
            station_location = station_detail.location

            # 获取电竞馆坐标
            poi_detail = maps_search_detail(id=target_poi_id)
            if poi_detail.error:
                print(f"步骤3失败: 获取电竞馆坐标失败 - {poi_detail.error}")
                return False

            if not poi_detail.location:
                print("步骤3失败: 未获取到电竞馆坐标")
                return False

            poi_location = poi_detail.location

            # 计算驾车时间
            driving_result = maps_driving_by_coordinates(
                origin=poi_location,
                destination=station_location
            )

            if driving_result.error:
                print(f"步骤3失败: 计算驾车时间失败 - {driving_result.error}")
                all_passed = False
            else:
                if driving_result.total_duration_seconds is None:
                    print("步骤3失败: 未获取到驾车时间")
                    all_passed = False
                else:
                    driving_time = driving_result.total_duration_seconds
                    if driving_time > max_driving_time_to_station:
                        print(f"步骤3失败: 驾车时间{driving_time}秒超过要求{max_driving_time_to_station}秒")
                        all_passed = False
                    else:
                        print(f"步骤3通过: 驾车时间{driving_time}秒，满足要求（<={max_driving_time_to_station}秒）")

    # 步骤4: 到建昌古城(公交站)直线距离
    print(f"\n步骤4: 验证到建昌古城公交站的直线距离不超过{max_distance_to_bus_station}米")
    if 'poi_location' not in locals():
        # 如果前面没有获取到POI坐标，重新获取
        poi_detail = maps_search_detail(id=target_poi_id)
        if poi_detail.error or not poi_detail.location:
            print("步骤4失败: 无法获取电竞馆坐标")
            all_passed = False
        else:
            poi_location = poi_detail.location

    if 'poi_location' in locals():
        bus_station_detail = maps_search_detail(id=bus_station_poi_id)
        if bus_station_detail.error:
            print(f"步骤4失败: 获取建昌古城公交站坐标失败 - {bus_station_detail.error}")
            all_passed = False
        else:
            if not bus_station_detail.location:
                print("步骤4失败: 未获取到建昌古城公交站坐标")
                all_passed = False
            else:
                bus_station_location = bus_station_detail.location

                # 计算直线距离
                distance_result = maps_distance(
                    origins=bus_station_location,
                    destination=poi_location
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

    # 步骤5: 最近公交站步行距离
    print(f"\n步骤5: 验证最近公交站步行距离不超过{max_walking_distance_to_bus}米")
    if 'poi_location' not in locals():
        poi_detail = maps_search_detail(id=target_poi_id)
        if poi_detail.error or not poi_detail.location:
            print("步骤5失败: 无法获取电竞馆坐标")
            all_passed = False
        else:
            poi_location = poi_detail.location

    if 'poi_location' in locals():
        bus_around_result = maps_around_search(
            location=poi_location,
            radius=bus_search_radius,
            keywords=bus_keywords
        )

        if bus_around_result.error:
            print(f"步骤5失败: {bus_around_result.error}")
            all_passed = False
        else:
            if not bus_around_result.pois or len(bus_around_result.pois) == 0:
                print(f"步骤5失败: 未找到任何{bus_keywords}")
                all_passed = False
            else:
                # 计算到每个公交站的步行距离，找到最小值
                min_walking_distance = float('inf')
                for bus_poi in bus_around_result.pois:
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
                    print("步骤5失败: 无法计算到任何公交站的步行距离")
                    all_passed = False
                elif min_walking_distance > max_walking_distance_to_bus:
                    print(f"步骤5失败: 到最近公交站的步行距离{min_walking_distance}米超过要求{max_walking_distance_to_bus}米")
                    all_passed = False
                else:
                    print(f"步骤5通过: 到最近公交站的步行距离{min_walking_distance}米，满足要求（<={max_walking_distance_to_bus}米）")

    # 步骤6: 途径点附近有ATM
    print(f"\n步骤6: 验证途径点附近{atm_search_radius}米内有{atm_keywords}")
    if 'poi_location' not in locals():
        poi_detail = maps_search_detail(id=target_poi_id)
        if poi_detail.error or not poi_detail.location:
            print("步骤6失败: 无法获取电竞馆坐标")
            all_passed = False
        else:
            poi_location = poi_detail.location

    if 'poi_location' in locals():
        walking_steps_result = maps_walking_by_coordinates(
            origin=user_location,
            destination=poi_location
        )

        if walking_steps_result.error or not walking_steps_result.steps:
            print("步骤6失败: 未获取到步行路线步骤信息")
            all_passed = False
        else:
            found_atm = False
            for i, step in enumerate(walking_steps_result.steps):
                # 尝试from_coordinates
                waypoint_location = step.from_coordinates
                atm_result = maps_around_search(
                    location=waypoint_location,
                    radius=atm_search_radius,
                    keywords=atm_keywords
                )

                if not atm_result.error and atm_result.pois and len(atm_result.pois) > 0:
                    atm_count = len(atm_result.pois)
                    print(f"步骤6通过: 途径点{i+1}（{waypoint_location}）附近找到{atm_count}个ATM")
                    found_atm = True
                    break

                # 尝试to_coordinates
                waypoint_location = step.to_coordinates
                atm_result = maps_around_search(
                    location=waypoint_location,
                    radius=atm_search_radius,
                    keywords=atm_keywords
                )

                if not atm_result.error and atm_result.pois and len(atm_result.pois) > 0:
                    atm_count = len(atm_result.pois)
                    print(f"步骤6通过: 途径点{i+1}（{waypoint_location}）附近找到{atm_count}个ATM")
                    found_atm = True
                    break

            if not found_atm:
                print(f"步骤6失败: 所有途径点附近均未找到ATM")
                all_passed = False

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")


if __name__ == "__main__":
    main()
