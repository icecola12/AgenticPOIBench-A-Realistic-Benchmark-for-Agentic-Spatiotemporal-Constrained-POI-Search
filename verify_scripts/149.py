"""
修改任务指令：你想在附近2000米以内找一家网吧。你打算骑车过去，所以从你这里骑行到网吧的距离不能超过1500米。散场后你要坐公交回家，所以网吧走路到附近600米范围内公交站中最短步行距离不能超过700米。你还要赶去绥化火车站接人，所以从网吧开车到绥化火车站的时间不能超过8分钟。另外你们一共两个人：你从当前位置出发骑行过去，你朋友从绥化火车站出发开车过来，你们到网吧的通行时间差不要超过4分钟。最后你希望去网吧的路上顺路取点现金，所以你从当前位置骑车到网吧的路线中，任意一个骑行导航步骤的终点500米内必须能搜到ATM。你健谈外向，乐观，乐于合作。
输入：B0KRUUZB1O
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2000米约束：调用maps_around_search(location='126.986128,46.6463', radius='2000', keywords='网吧')，验证返回pois中包含目标poi_id=B0KRUUZB1O。
2) 最大骑行距离约束：先用maps_search_detail('B0KRUUZB1O')获取目标坐标dest；调用maps_bicycling_by_coordinates(origin='126.986128,46.6463', destination=dest)，验证total_distance_meters ≤ 1500。
3) 公交站最短步行距离约束（公交站集合在目标点周围600米内）：用maps_search_detail获取dest；调用maps_around_search(location=dest, radius='600', keywords='公交站')得到公交站列表；对每个公交站poi调用maps_walking_by_coordinates(origin=dest, destination=station.location)计算步行距离，取最小total_distance_meters，验证min_distance ≤ 700。
4) 网吧到绥化火车站驾车时间约束：调用 maps_text_search(keywords='绥化火车站', city='绥化') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 得到站点坐标station_loc；调用maps_driving_by_coordinates(origin=dest, destination=station_loc)，验证total_duration_seconds ≤ 480秒。
5) 你(骑行)与朋友(驾车)到网吧的时间差约束：调用maps_bicycling_by_coordinates(origin='126.986128,46.6463', destination=dest)得到t_bike；调用maps_driving_by_coordinates(origin=station_loc, destination=dest)得到t_drive；验证|t_bike - t_drive| ≤ 240秒。
6) 途径点附近有ATM约束（基于骑行路线步骤）：调用maps_bicycling_by_coordinates(origin='126.986128,46.6463', destination=dest)获取steps；对steps中任意一个step.to_coordinates作为途径点p，调用maps_around_search(location=p, radius='500', keywords='ATM')，验证至少存在一个p使返回pois数量>0。推荐验证途径点使用step.to_coordinates='126.987726,46.640588'（来自该路线的步骤终点），其500米内可搜到ATM（如id=B01C700DZ6或B0FFG78572）。
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
    maps_text_search,
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
    target_poi_id: str = "B0KRUUZB1O",
    user_location: str = "126.986128,46.6463",
    radius: str = "2000",
    keywords: str = "网吧",
    max_bicycling_distance: int = 1500,
    bus_search_radius: str = "600",
    bus_keywords: str = "公交站",
    max_walking_distance_to_bus: int = 700,
    station_address: str = "绥化火车站",
    station_city: str = "绥化",
    max_driving_time_to_station: int = 480,
    max_time_diff: int = 240,
    atm_search_radius: str = "500",
    atm_keywords: str = "ATM"
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
        max_walking_distance_to_bus: 到公交站的最大步行距离（米）
        station_address: 火车站地址
        station_city: 火车站所在城市
        max_driving_time_to_station: 到火车站的最大驾车时间（秒）
        max_time_diff: 最大时间差（秒）
        atm_search_radius: ATM搜索半径（米）
        atm_keywords: ATM搜索关键词

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 附近2000米约束
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

    # 步骤2: 最大骑行距离约束
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

    # 步骤3: 公交站最短步行距离约束
    print(f"\n步骤3: 验证到公交站的最小步行距离不超过{max_walking_distance_to_bus}米")
    bus_around_result = maps_around_search(
        location=poi_location,
        radius=bus_search_radius,
        keywords=bus_keywords
    )

    if bus_around_result.error:
        print(f"步骤3失败: {bus_around_result.error}")
        all_passed = False
    else:
        if not bus_around_result.pois or len(bus_around_result.pois) == 0:
            print(f"步骤3失败: 未找到任何{bus_keywords}")
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
                print("步骤3失败: 无法计算到任何公交站的步行距离")
                all_passed = False
            elif min_walking_distance > max_walking_distance_to_bus:
                print(f"步骤3失败: 到最近公交站的步行距离{min_walking_distance}米超过要求{max_walking_distance_to_bus}米")
                all_passed = False
            else:
                print(f"步骤3通过: 到最近公交站的步行距离{min_walking_distance}米，满足要求（<={max_walking_distance_to_bus}米）")

    # 步骤4: 网吧到绥化火车站驾车时间约束
    print(f"\n步骤4: 验证到{station_address}的驾车时间不超过{max_driving_time_to_station}秒（{max_driving_time_to_station//60}分钟）")
    text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if text_search_result.error:
        print(f"步骤4失败: 获取{station_address}坐标失败 - {text_search_result.error}")
        all_passed = False
    elif not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"步骤4失败: 未找到{station_address}坐标")
        all_passed = False
    else:
        first_poi_id = text_search_result.pois[0].id
        detail_result = maps_search_detail(id=first_poi_id)
        if detail_result.error or not detail_result.location:
            print(f"步骤4失败: 获取{station_address}坐标失败 - {detail_result.error or '无location'}")
            all_passed = False
        else:
            station_location = detail_result.location
            print(f"{station_address}坐标: {station_location}")

            driving_result_to_station = maps_driving_by_coordinates(
                origin=poi_location,
                destination=station_location
            )

            if driving_result_to_station.error:
                print(f"步骤4失败: 计算驾车时间失败 - {driving_result_to_station.error}")
                all_passed = False
            else:
                if driving_result_to_station.total_duration_seconds is None:
                    print("步骤4失败: 未获取到驾车时间")
                    all_passed = False
                else:
                    driving_time_to_station = driving_result_to_station.total_duration_seconds
                    if driving_time_to_station > max_driving_time_to_station:
                        print(f"步骤4失败: 驾车时间{driving_time_to_station}秒超过要求{max_driving_time_to_station}秒")
                        all_passed = False
                    else:
                        print(f"步骤4通过: 驾车时间{driving_time_to_station}秒，满足要求（<={max_driving_time_to_station}秒）")

    # 步骤5: 你(骑行)与朋友(驾车)到网吧的时间差约束
    print(f"\n步骤5: 验证骑行与驾车时间差不超过{max_time_diff}秒（{max_time_diff//60}分钟）")
    if bicycling_result.total_duration_seconds is None:
        print("步骤5失败: 未获取到骑行时间")
        all_passed = False
    else:
        t_bike = bicycling_result.total_duration_seconds

        # 朋友从火车站驾车到网吧
        driving_result_friend = maps_driving_by_coordinates(
            origin=station_location,
            destination=poi_location
        )

        if driving_result_friend.error:
            print(f"步骤5失败: 计算朋友驾车时间失败 - {driving_result_friend.error}")
            all_passed = False
        else:
            if driving_result_friend.total_duration_seconds is None:
                print("步骤5失败: 未获取到朋友驾车时间")
                all_passed = False
            else:
                t_drive = driving_result_friend.total_duration_seconds
                time_diff = abs(t_bike - t_drive)
                if time_diff > max_time_diff:
                    print(f"步骤5失败: 时间差{time_diff}秒超过要求{max_time_diff}秒（骑行时间: {t_bike}秒, 驾车时间: {t_drive}秒）")
                    all_passed = False
                else:
                    print(f"步骤5通过: 时间差{time_diff}秒，满足要求（<={max_time_diff}秒）（骑行时间: {t_bike}秒, 驾车时间: {t_drive}秒）")

    # 步骤6: 途径点附近有ATM约束
    print(f"\n步骤6: 验证骑行路线途径点附近有{atm_keywords}")
    if bicycling_result.error or not bicycling_result.steps:
        print("步骤6失败: 未获取到骑行路线步骤信息")
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

            if atm_around_result.error:
                continue  # 跳过这个途径点，继续检查下一个

            if atm_around_result.pois and len(atm_around_result.pois) > 0:
                atm_count = len(atm_around_result.pois)
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
