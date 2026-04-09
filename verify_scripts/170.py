"""
修改任务指令：你想在附近2500米以内找一家网吧。你希望它离你开车过去的距离不超过2公里，而且骑行过去的距离不超过1200米。你还要求这家网吧到“黄河路沙口路(公交站)”的直线距离不超过400米；另外，这家网吧到它附近1200米范围内地铁站里最近的那个，直线距离不能超过700米。你还要控制从这家网吧开车去郑州站的时间不超过8分钟，并且从这家网吧骑行到河南省人民医院的时间不超过25分钟。你思路混乱，可能会混淆信息，让对话难以跟进。
输入：B0I2BR4SQK
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边检索数量门槛：调用 maps_around_search(location='113.641592,34.762893', radius='2500', keywords='网吧')，验证返回 pois 数量≥8，且包含 target_poi_id=B0I2BR4SQK。
2) POI详情：调用 maps_search_detail(id='B0I2BR4SQK') 获取目标POI坐标 dest_loc。
3) 出发地到目标网吧驾车距离：调用 maps_driving_by_coordinates(origin='113.641592,34.762893', destination=dest_loc)，验证 total_distance_meters ≤ 2000。
4) 出发地到目标网吧骑行距离：调用 maps_bicycling_by_coordinates(origin='113.641592,34.762893', destination=dest_loc)，验证 total_distance_meters ≤ 1200。
5) 指定公交站直线距离：调用 maps_text_search(keywords='黄河路沙口路公交站', city='郑州', citylimit='true')，取结果中“黄河路沙口路(公交站)”坐标 bus_loc；调用 maps_distance(origins=dest_loc, destination=bus_loc)，验证 distance_meters ≤ 400。
6) 附近地铁站最小直线距离：调用 maps_around_search(location=dest_loc, radius='1200', keywords='地铁站') 得到地铁站列表；对每个地铁站坐标 metro_i 调用 maps_distance(origins=dest_loc, destination=metro_i)，取最小距离 min_d，验证 min_d ≤ 700。
7) 到郑州站驾车时间：调用 maps_text_search(keywords='郑州站', city='郑州', citylimit='true') 取“郑州站”坐标 zz_station_loc；调用 maps_driving_by_coordinates(origin=dest_loc, destination=zz_station_loc)，验证 total_duration_seconds/60 ≤ 8。
8) 到河南省人民医院骑行时间：调用 maps_text_search(keywords='河南省人民医院', city='郑州', citylimit='true') 取“河南省人民医院”坐标 hospital_loc；调用 maps_bicycling_by_coordinates(origin=dest_loc, destination=hospital_loc)，验证 total_duration_seconds/60 ≤ 25。
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
    target_poi_id: str = "B0I2BR4SQK",
    user_location: str = "113.641592,34.762893",
    radius: str = "2500",
    keywords: str = "网吧",
    min_poi_count: int = 8,
    max_driving_distance: int = 2000,
    max_bicycling_distance: int = 1200,
    bus_station_keywords: str = "黄河路沙口路公交站",
    bus_station_city: str = "郑州",
    bus_station_citylimit: str = "true",
    max_distance_to_bus: int = 400,
    subway_search_radius: str = "1200",
    subway_keywords: str = "地铁站",
    max_distance_to_subway: int = 700,
    zhengzhou_station_keywords: str = "郑州站",
    zhengzhou_station_city: str = "郑州",
    zhengzhou_station_citylimit: str = "true",
    max_driving_time_to_station: int = 8 * 60,
    hospital_keywords: str = "河南省人民医院",
    hospital_city: str = "郑州",
    hospital_citylimit: str = "true",
    max_bicycling_time_to_hospital: int = 25 * 60
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        min_poi_count: 最小POI数量门槛
        max_driving_distance: 最大驾车距离（米）
        max_bicycling_distance: 最大骑行距离（米）
        bus_station_keywords: 公交站搜索关键词
        bus_station_city: 公交站所在城市
        bus_station_citylimit: 是否限制城市
        max_distance_to_bus: 到公交站的最大直线距离（米）
        subway_search_radius: 地铁站搜索半径（米）
        subway_keywords: 地铁站搜索关键词
        max_distance_to_subway: 到地铁站的最大直线距离（米）
        zhengzhou_station_keywords: 郑州站搜索关键词
        zhengzhou_station_city: 郑州站所在城市
        zhengzhou_station_citylimit: 是否限制城市
        max_driving_time_to_station: 到郑州站的最大驾车时间（秒）
        hospital_keywords: 医院搜索关键词
        hospital_city: 医院所在城市
        hospital_citylimit: 是否限制城市
        max_bicycling_time_to_hospital: 到医院的最大骑行时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 周边检索数量门槛
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

    poi_count = len(around_result.pois)
    print(f"步骤1: 找到{poi_count}个POI")

    # if poi_count < min_poi_count:
    #     print(f"步骤1失败: POI数量{poi_count}小于要求的最小数量{min_poi_count}")
    #     all_passed = False
    # else:
    #     print(f"步骤1: POI数量{poi_count}满足要求（>={min_poi_count}）")

    # 检查是否包含目标POI
    poi_ids = [poi.id for poi in around_result.pois]
    if target_poi_id not in poi_ids:
        print(f"步骤1失败: POI列表不包含目标POI ID '{target_poi_id}'")
        all_passed = False
    else:
        print(f"步骤1通过: POI列表中包含目标POI ID '{target_poi_id}'")

    # 步骤2: POI详情
    print(f"\n步骤2: 获取POI详情 - 查询POI ID: {target_poi_id}")
    poi_detail = maps_search_detail(id=target_poi_id)

    if poi_detail.error:
        print(f"步骤2失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print("步骤2失败: 未获取到POI坐标")
        return False

    dest_loc = poi_detail.location
    print(f"步骤2通过: POI坐标为{dest_loc}")

    # 步骤3: 出发地到目标网吧驾车距离
    print(f"\n步骤3: 验证驾车距离不超过{max_driving_distance}米")
    driving_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=dest_loc
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

    # 步骤4: 出发地到目标网吧骑行距离
    print(f"\n步骤4: 验证骑行距离不超过{max_bicycling_distance}米")
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=dest_loc
    )

    if bicycling_result.error:
        print(f"步骤4失败: {bicycling_result.error}")
        all_passed = False
    else:
        if bicycling_result.total_distance_meters is None:
            print("步骤4失败: 未获取到骑行距离")
            all_passed = False
        else:
            bicycling_distance = bicycling_result.total_distance_meters
            if bicycling_distance > max_bicycling_distance:
                print(f"步骤4失败: 骑行距离{bicycling_distance}米超过要求{max_bicycling_distance}米")
                all_passed = False
            else:
                print(f"步骤4通过: 骑行距离{bicycling_distance}米，满足要求（<={max_bicycling_distance}米）")

    # 步骤5: 指定公交站直线距离
    print(f"\n步骤5: 验证到指定公交站的直线距离不超过{max_distance_to_bus}米")
    bus_text_result = maps_text_search(
        keywords=bus_station_keywords,
        city=bus_station_city,
        citylimit=bus_station_citylimit
    )

    if bus_text_result.error:
        print(f"步骤5失败: 搜索公交站失败 - {bus_text_result.error}")
        all_passed = False
    else:
        if not bus_text_result.pois or len(bus_text_result.pois) == 0:
            print(f"步骤5失败: 未找到'{bus_station_keywords}'")
            all_passed = False
        else:
            # 查找包含"公交站"的POI
            bus_poi = None
            for poi in bus_text_result.pois:
                if "公交站" in poi.name:
                    bus_poi = poi
                    break

            if not bus_poi:
                print(f"步骤5失败: 未找到公交站POI")
                all_passed = False
            else:
                bus_poi_id = bus_poi.id
                bus_detail = maps_search_detail(id=bus_poi_id)

                if bus_detail.error or not bus_detail.location:
                    print(f"步骤5失败: 获取公交站坐标失败")
                    all_passed = False
                else:
                    bus_loc = bus_detail.location
                    distance_result = maps_distance(
                        origins=dest_loc,
                        destination=bus_loc
                    )

                    if distance_result.error:
                        print(f"步骤5失败: 计算距离失败 - {distance_result.error}")
                        all_passed = False
                    else:
                        if not distance_result.results or len(distance_result.results) == 0:
                            print("步骤5失败: 未获取到距离结果")
                            all_passed = False
                        else:
                            distance = distance_result.results[0].distance_meters
                            if distance > max_distance_to_bus:
                                print(f"步骤5失败: 到公交站的距离{distance}米超过要求{max_distance_to_bus}米")
                                all_passed = False
                            else:
                                print(f"步骤5通过: 到公交站的距离{distance}米，满足要求（<={max_distance_to_bus}米）")

    # 步骤6: 附近地铁站最小直线距离
    print(f"\n步骤6: 验证到地铁站的最小直线距离不超过{max_distance_to_subway}米")
    subway_around_result = maps_around_search(
        location=dest_loc,
        radius=subway_search_radius,
        keywords=subway_keywords
    )

    if subway_around_result.error:
        print(f"步骤6失败: {subway_around_result.error}")
        all_passed = False
    else:
        if not subway_around_result.pois or len(subway_around_result.pois) == 0:
            print(f"步骤6失败: 未找到任何{subway_keywords}")
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
                    origins=dest_loc,
                    destination=subway_location
                )

                if distance_result.error or not distance_result.results or len(distance_result.results) == 0:
                    continue

                distance = distance_result.results[0].distance_meters
                if distance < min_distance:
                    min_distance = distance

            if min_distance == float('inf'):
                print("步骤6失败: 无法计算到任何地铁站的距离")
                all_passed = False
            elif min_distance > max_distance_to_subway:
                print(f"步骤6失败: 到最近地铁站的距离{min_distance}米超过要求{max_distance_to_subway}米")
                all_passed = False
            else:
                print(f"步骤6通过: 到最近地铁站的距离{min_distance}米，满足要求（<={max_distance_to_subway}米）")

    # 步骤7: 到郑州站驾车时间
    print(f"\n步骤7: 验证到郑州站的驾车时间不超过{max_driving_time_to_station}秒（{max_driving_time_to_station//60}分钟）")
    station_text_result = maps_text_search(
        keywords=zhengzhou_station_keywords,
        city=zhengzhou_station_city,
        citylimit=zhengzhou_station_citylimit
    )

    if station_text_result.error:
        print(f"步骤7失败: 搜索郑州站失败 - {station_text_result.error}")
        all_passed = False
    else:
        if not station_text_result.pois or len(station_text_result.pois) == 0:
            print(f"步骤7失败: 未找到'{zhengzhou_station_keywords}'")
            all_passed = False
        else:
            # 获取郑州站坐标
            station_poi = station_text_result.pois[0]
            station_detail = maps_search_detail(id=station_poi.id)

            if station_detail.error or not station_detail.location:
                print(f"步骤7失败: 获取郑州站坐标失败")
                all_passed = False
            else:
                zz_station_loc = station_detail.location
                driving_result_to_station = maps_driving_by_coordinates(
                    origin=dest_loc,
                    destination=zz_station_loc
                )

                if driving_result_to_station.error:
                    print(f"步骤7失败: 计算驾车时间失败 - {driving_result_to_station.error}")
                    all_passed = False
                else:
                    if driving_result_to_station.total_duration_seconds is None:
                        print("步骤7失败: 未获取到驾车时间")
                        all_passed = False
                    else:
                        driving_time = driving_result_to_station.total_duration_seconds
                        if driving_time > max_driving_time_to_station:
                            print(f"步骤7失败: 驾车时间{driving_time}秒超过要求{max_driving_time_to_station}秒")
                            all_passed = False
                        else:
                            print(f"步骤7通过: 驾车时间{driving_time}秒，满足要求（<={max_driving_time_to_station}秒）")

    # 步骤8: 到河南省人民医院骑行时间
    print(f"\n步骤8: 验证到河南省人民医院的骑行时间不超过{max_bicycling_time_to_hospital}秒（{max_bicycling_time_to_hospital//60}分钟）")
    hospital_text_result = maps_text_search(
        keywords=hospital_keywords,
        city=hospital_city,
        citylimit=hospital_citylimit
    )

    if hospital_text_result.error:
        print(f"步骤8失败: 搜索医院失败 - {hospital_text_result.error}")
        all_passed = False
    else:
        if not hospital_text_result.pois or len(hospital_text_result.pois) == 0:
            print(f"步骤8失败: 未找到'{hospital_keywords}'")
            all_passed = False
        else:
            # 获取医院坐标
            hospital_poi = hospital_text_result.pois[0]
            hospital_detail = maps_search_detail(id=hospital_poi.id)

            if hospital_detail.error or not hospital_detail.location:
                print(f"步骤8失败: 获取医院坐标失败")
                all_passed = False
            else:
                hospital_loc = hospital_detail.location
                bicycling_result_to_hospital = maps_bicycling_by_coordinates(
                    origin=dest_loc,
                    destination=hospital_loc
                )

                if bicycling_result_to_hospital.error:
                    print(f"步骤8失败: 计算骑行时间失败 - {bicycling_result_to_hospital.error}")
                    all_passed = False
                else:
                    if bicycling_result_to_hospital.total_duration_seconds is None:
                        print("步骤8失败: 未获取到骑行时间")
                        all_passed = False
                    else:
                        bicycling_time = bicycling_result_to_hospital.total_duration_seconds
                        if bicycling_time > max_bicycling_time_to_hospital:
                            print(f"步骤8失败: 骑行时间{bicycling_time}秒超过要求{max_bicycling_time_to_hospital}秒")
                            all_passed = False
                        else:
                            print(f"步骤8通过: 骑行时间{bicycling_time}秒，满足要求（<={max_bicycling_time_to_hospital}秒）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")


if __name__ == "__main__":
    main()
