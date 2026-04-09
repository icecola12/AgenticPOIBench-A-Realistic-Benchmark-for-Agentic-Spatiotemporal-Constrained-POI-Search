"""
修改任务指令：你想在附近5000米以内找一家电竞馆。你打算骑车过去，所以从你这里骑行到电竞馆的距离不能超过4500米。另外你还要从电竞馆直接打车去赤峰玉龙机场，车程要控制在20分钟内。你希望电竞馆走路到最近的公交站不超过10分钟，并且这个最近的公交站需要在电竞馆附近800米内。为了减少绕路，你还要求从你这里出发经由电竞馆再去赤峰站的总驾车时间，比你直接开车去赤峰站最多只多8分钟。最后，你想要沿着你到电竞馆的骑行路线上存在某个途径点，该附近800米内能找到ATM自助银行。你虽然心情不好，但仍然保持礼貌和独立的姿态。
输入：B0LD5785HE
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近5000米：调用 maps_around_search(location='118.866224,42.245545', radius='5000', keywords='电竞馆')，验证返回pois中包含目标POI id='B0LD5785HE'。
2) POI类型：由步骤1的keywords='电竞馆'保证目标POI为电竞馆类候选，并可通过 maps_search_detail('B0LD5785HE')核对名称/类型语义。
3) 骑行距离≤4500米：调用 maps_bicycling_by_coordinates(origin='118.866224,42.245545', destination='118.912899,42.252956')，验证 total_distance_meters ≤ 4500。
4) 到赤峰玉龙机场驾车≤20分钟：调用 maps_geo(address='赤峰玉龙机场', city='赤峰市') 得到机场坐标destination='118.846896,42.159804'；再调用 maps_driving_by_coordinates(origin='118.912899,42.252956', destination='118.846896,42.159804')，验证 total_duration_seconds ≤ 1200。
5) 最近公交站步行≤10分钟 且该站在直线800米内：
a) 调用 maps_around_search(location='118.912899,42.252956', radius='800', keywords='公交站') 获取候选公交站列表,验证返回列表不为空。
b) 对每个候选公交站poi的location调用 maps_walking_by_coordinates(origin='118.912899,42.252956', destination=公交站location)，取最小步行时间t_min，验证 t_min ≤ 600 秒。
6) 绕行增加时间≤8分钟（驾车）：
a) 调用 maps_geo(address='赤峰站', city='赤峰市') 得到赤峰站坐标B='118.901624,42.275612'。
b) 直接A->B：调用 maps_driving_by_coordinates(origin='118.866224,42.245545', destination='118.901624,42.275612') 得到T_direct。
c) 经由电竞馆A->POI->B：分别调用 maps_driving_by_coordinates(origin='118.866224,42.245545', destination='118.912899,42.252956') 得到T1，和 maps_driving_by_coordinates(origin='118.912899,42.252956', destination='118.901624,42.275612') 得到T2；验证 (T1+T2) - T_direct ≤ 480 秒。
7) 骑行途径点附近800米有ATM：
a) 调用 maps_bicycling_by_coordinates(origin='118.866224,42.245545', destination='118.912899,42.252956')，遍历steps，以step的to_coordinates作为途径点P（非起点/终点）。
b) 调用 maps_around_search(location=P, radius='800', keywords='ATM自助银行')，验证是否存在某一step对应的返回pois数量>0（存在ATM自助银行类POI）。
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
    target_poi_id: str = "B0LD5785HE",
    user_location: str = "118.866224,42.245545",
    radius: str = "5000",
    keywords: str = "电竞馆",
    max_bicycling_distance: int = 4500,
    airport_address: str = "赤峰玉龙机场",
    airport_city: str = "赤峰市",
    max_driving_time_to_airport: int = 1200,
    bus_search_radius: str = "800",
    bus_keywords: str = "公交站",
    max_walking_time_to_bus: int = 600,
    station_address: str = "赤峰站",
    station_city: str = "赤峰市",
    max_detour_time: int = 480,
    atm_search_radius: str = "800",
    atm_keywords: str = "ATM自助银行"
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        max_bicycling_distance: 最大骑行距离（米）
        airport_address: 机场地址
        airport_city: 机场所在城市
        max_driving_time_to_airport: 到机场的最大驾车时间（秒）
        bus_search_radius: 公交站搜索半径（米）
        bus_keywords: 公交站搜索关键词
        max_walking_time_to_bus: 到公交站的最大步行时间（秒）
        station_address: 火车站地址
        station_city: 火车站所在城市
        max_detour_time: 最大绕路时间增量（秒）
        atm_search_radius: ATM搜索半径（米）
        atm_keywords: ATM搜索关键词

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 附近5000米
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
    poi_name = poi_detail.name if poi_detail.name else ""
    print(f"POI坐标: {poi_location}, 名称: {poi_name}")

    # 步骤2: POI类型
    print(f"\n步骤2: 验证POI名称包含'{keywords}'")
    if keywords not in poi_name:
        print(f"步骤2失败: POI名称'{poi_name}'不包含'{keywords}'")
        all_passed = False
    else:
        print(f"步骤2通过: POI名称'{poi_name}'包含'{keywords}'")

    # 步骤3: 骑行距离≤4500米
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

    # 步骤4: 到赤峰玉龙机场驾车≤20分钟
    print(f"\n步骤4: 验证到{airport_address}的驾车时间不超过{max_driving_time_to_airport}秒（{max_driving_time_to_airport//60}分钟）")
    geo_result_airport = maps_geo(address=airport_address, city=airport_city)

    if geo_result_airport.error:
        print(f"步骤4失败: 获取{airport_address}坐标失败 - {geo_result_airport.error}")
        all_passed = False
    else:
        if not geo_result_airport.results or len(geo_result_airport.results) == 0:
            print(f"步骤4失败: 未找到{airport_address}坐标")
            all_passed = False
        else:
            airport_location = geo_result_airport.results[0].location
            driving_result_to_airport = maps_driving_by_coordinates(
                origin=poi_location,
                destination=airport_location
            )

            if driving_result_to_airport.error:
                print(f"步骤4失败: 计算驾车时间失败 - {driving_result_to_airport.error}")
                all_passed = False
            else:
                if driving_result_to_airport.total_duration_seconds is None:
                    print("步骤4失败: 未获取到驾车时间")
                    all_passed = False
                else:
                    driving_time_to_airport = driving_result_to_airport.total_duration_seconds
                    if driving_time_to_airport > max_driving_time_to_airport:
                        print(f"步骤4失败: 驾车时间{driving_time_to_airport}秒超过要求{max_driving_time_to_airport}秒")
                        all_passed = False
                    else:
                        print(f"步骤4通过: 驾车时间{driving_time_to_airport}秒，满足要求（<={max_driving_time_to_airport}秒）")

    # 步骤5: 最近公交站步行≤10分钟且在800米内
    print(f"\n步骤5: 验证最近公交站步行时间不超过{max_walking_time_to_bus}秒（{max_walking_time_to_bus//60}分钟）且在{bus_search_radius}米内")
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
            # 计算到每个公交站的步行时间，找到最小值
            min_walking_time = float('inf')
            for bus_poi in bus_around_result.pois:
                bus_detail = maps_search_detail(id=bus_poi.id)
                if bus_detail.error or not bus_detail.location:
                    continue

                bus_location = bus_detail.location
                walking_result = maps_walking_by_coordinates(
                    origin=poi_location,
                    destination=bus_location
                )

                if walking_result.error or walking_result.total_duration_seconds is None:
                    continue

                walking_time = walking_result.total_duration_seconds
                if walking_time < min_walking_time:
                    min_walking_time = walking_time

            if min_walking_time == float('inf'):
                print("步骤5失败: 无法计算到任何公交站的步行时间")
                all_passed = False
            elif min_walking_time > max_walking_time_to_bus:
                print(f"步骤5失败: 到最近公交站的步行时间{min_walking_time}秒超过要求{max_walking_time_to_bus}秒")
                all_passed = False
            else:
                print(f"步骤5通过: 到最近公交站的步行时间{min_walking_time}秒，满足要求（<={max_walking_time_to_bus}秒）")

    # 步骤6: 绕行增加时间≤8分钟
    print(f"\n步骤6: 验证绕路时间增量不超过{max_detour_time}秒（{max_detour_time//60}分钟）")
    geo_result_station = maps_geo(address=station_address, city=station_city)

    if geo_result_station.error:
        print(f"步骤6失败: 获取{station_address}坐标失败 - {geo_result_station.error}")
        all_passed = False
    else:
        if not geo_result_station.results or len(geo_result_station.results) == 0:
            print(f"步骤6失败: 未找到{station_address}坐标")
            all_passed = False
        else:
            station_location = geo_result_station.results[0].location
            print(f"{station_address}坐标: {station_location}")

            # 计算直接路线时间
            driving_direct = maps_driving_by_coordinates(
                origin=user_location,
                destination=station_location
            )

            if driving_direct.error or driving_direct.total_duration_seconds is None:
                print("步骤6失败: 计算直接路线时间失败")
                all_passed = False
            else:
                t_direct = driving_direct.total_duration_seconds

                # 计算绕路路线时间
                driving_to_poi = maps_driving_by_coordinates(
                    origin=user_location,
                    destination=poi_location
                )

                driving_poi_to_station = maps_driving_by_coordinates(
                    origin=poi_location,
                    destination=station_location
                )

                if (driving_to_poi.error or driving_to_poi.total_duration_seconds is None or
                    driving_poi_to_station.error or driving_poi_to_station.total_duration_seconds is None):
                    print("步骤6失败: 计算绕路路线时间失败")
                    all_passed = False
                else:
                    t1 = driving_to_poi.total_duration_seconds
                    t2 = driving_poi_to_station.total_duration_seconds
                    detour_time = (t1 + t2) - t_direct

                    if detour_time > max_detour_time:
                        print(f"步骤6失败: 绕路时间增量{detour_time}秒超过要求{max_detour_time}秒（t1={t1}秒, t2={t2}秒, t_direct={t_direct}秒）")
                        all_passed = False
                    else:
                        print(f"步骤6通过: 绕路时间增量{detour_time}秒，满足要求（<={max_detour_time}秒）（t1={t1}秒, t2={t2}秒, t_direct={t_direct}秒）")

    # 步骤7: 骑行途径点附近800米有ATM
    print(f"\n步骤7: 验证骑行路线途径点附近{atm_search_radius}米内有{atm_keywords}")
    if bicycling_result.error or not bicycling_result.steps:
        print("步骤7失败: 未获取到骑行路线步骤信息")
        all_passed = False
    else:
        found_atm = False
        for i, step in enumerate(bicycling_result.steps):
            waypoint_location = step.to_coordinates
            atm_around_result = maps_around_search(
                location=waypoint_location,
                radius=atm_search_radius,
                keywords=atm_keywords
            )

            if not atm_around_result.error and atm_around_result.pois and len(atm_around_result.pois) > 0:
                atm_count = len(atm_around_result.pois)
                print(f"步骤7通过: 途径点{i+1}（{waypoint_location}）附近找到{atm_count}个{atm_keywords}")
                found_atm = True
                break

        if not found_atm:
            print(f"步骤7失败: 所有途径点附近均未找到{atm_keywords}")
            all_passed = False

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
