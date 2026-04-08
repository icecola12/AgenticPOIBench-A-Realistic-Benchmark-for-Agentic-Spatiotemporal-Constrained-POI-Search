"""
输入：B0K65HKD9J
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围(附近2000米内)：调用 maps_around_search(location='117.26921,31.869326', radius='2000', keywords='网吧')，验证返回pois中包含 target_poi_id='B0K65HKD9J'。
2) 评分≥4.6：调用 maps_search_detail(id='B0K65HKD9J')，读取 biz_ext.rating，验证 rating >= 4.6。
3) 到出发地步行距离≤1500米：调用 maps_walking_by_coordinates(origin='117.26921,31.869326', destination=POI.location)，验证 total_distance_meters <= 1500。
4) 到出发地骑行距离≤1500米：调用 maps_bicycling_by_coordinates(origin='117.26921,31.869326', destination=POI.location)，验证 total_distance_meters <= 1500。
5) 到出发地驾车距离≤2公里：调用 maps_driving_by_coordinates(origin='117.26921,31.869326', destination=POI.location)，验证 total_distance_meters <= 2000。
6) 到指定公交站“省博物院南门”直线距离≤8000米：调用 maps_text_search(keywords='省博物院南门(公交站)', city='合肥', citylimit='true') 获取公交站poi_id=BV11210019；再调用 maps_search_detail(id='BV11210019') 得到坐标；调用 maps_distance(origins=POI.location, destination=bus.location)，验证 distance_meters <= 8000。
7) 到合肥南站驾车时间≤20分钟：调用 maps_text_search(keywords='合肥南站', city='合肥', citylimit='true') 获取poi_id=B0FFF3K7UZ；调用 maps_search_detail(id='B0FFF3K7UZ') 得到坐标；调用 maps_driving_by_coordinates(origin=POI.location, destination=station.location)，验证 total_duration_seconds <= 1200。
8) 交通枢纽(地铁站)约束：调用 maps_around_search(location=POI.location, radius='1500', keywords='地铁站') 得到候选地铁站列表；对每个地铁站调用 maps_walking_by_coordinates(origin=POI.location, destination=metro.location)，取最小 total_distance_meters，验证最小值 <= 900。
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
    maps_driving_by_coordinates ,
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
    target_poi_id: str = "B0K65HKD9J",
    user_location: str = "117.26921,31.869326",
    radius: str = "2000",
    keywords: str = "网吧",
    min_rating: float = 4.6,
    max_walking_distance: int = 1500,
    max_bicycling_distance: int = 1500,
    max_driving_distance: int = 2000,
    bus_station_keywords: str = "省博物院南门(公交站)",
    bus_station_city: str = "合肥",
    bus_station_citylimit: str = "true",
    bus_station_poi_id: str = "BV11210019",
    max_distance_to_bus_station: int = 8000,
    train_station_keywords: str = "合肥南站",
    train_station_city: str = "合肥",
    train_station_citylimit: str = "true",
    train_station_poi_id: str = "B0FFF3K7UZ",
    max_driving_time_to_train_station: int = 1200,
    subway_search_radius: str = "1500",
    subway_keywords: str = "地铁站",
    max_walking_distance_to_subway: int = 900
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        min_rating: 最小评分
        max_walking_distance: 最大步行距离（米）
        max_bicycling_distance: 最大骑行距离（米）
        max_driving_distance: 最大驾车距离（米）
        bus_station_keywords: 公交站搜索关键词
        bus_station_city: 公交站所在城市
        bus_station_citylimit: 是否限制城市
        bus_station_poi_id: 公交站POI ID
        max_distance_to_bus_station: 到公交站的最大直线距离（米）
        train_station_keywords: 火车站搜索关键词
        train_station_city: 火车站所在城市
        train_station_citylimit: 是否限制城市
        train_station_poi_id: 火车站POI ID
        max_driving_time_to_train_station: 到火车站的最大驾车时间（秒）
        subway_search_radius: 地铁站搜索半径（米）
        subway_keywords: 地铁站搜索关键词
        max_walking_distance_to_subway: 到地铁站的最大步行距离（米）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 周边范围(附近2000米内)
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

    # 步骤2: 评分≥4.6
    print(f"\n步骤2: 验证评分 >= {min_rating}")
    if not poi_detail.biz_ext:
        print("步骤2失败: 未获取到POI扩展信息")
        all_passed = False
    else:
        rating = poi_detail.biz_ext.get('rating')
        if rating is None:
            print("步骤2失败: 未获取到评分信息")
            all_passed = False
        else:
            try:
                rating_value = float(rating)
                if rating_value < min_rating:
                    print(f"步骤2失败: 评分{rating_value}小于要求{min_rating}")
                    all_passed = False
                else:
                    print(f"步骤2通过: 评分{rating_value}，满足要求（>={min_rating}）")
            except (ValueError, TypeError):
                print(f"步骤2失败: 评分格式错误: {rating}")
                all_passed = False

    # 步骤3: 到出发地步行距离≤1500米
    print(f"\n步骤3: 验证步行距离不超过{max_walking_distance}米")
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if walking_result.error:
        print(f"步骤3失败: {walking_result.error}")
        all_passed = False
    else:
        if walking_result.total_distance_meters is None:
            print("步骤3失败: 未获取到步行距离")
            all_passed = False
        else:
            walking_distance = walking_result.total_distance_meters
            if walking_distance > max_walking_distance:
                print(f"步骤3失败: 步行距离{walking_distance}米超过要求{max_walking_distance}米")
                all_passed = False
            else:
                print(f"步骤3通过: 步行距离{walking_distance}米，满足要求（<={max_walking_distance}米）")

    # 步骤4: 到出发地骑行距离≤1500米
    print(f"\n步骤4: 验证骑行距离不超过{max_bicycling_distance}米")
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=poi_location
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

    # 步骤5: 到出发地驾车距离≤2公里
    print(f"\n步骤5: 验证驾车距离不超过{max_driving_distance}米")
    driving_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=poi_location
    )

    if driving_result.error:
        print(f"步骤5失败: {driving_result.error}")
        all_passed = False
    else:
        if driving_result.total_distance_meters is None:
            print("步骤5失败: 未获取到驾车距离")
            all_passed = False
        else:
            driving_distance = driving_result.total_distance_meters
            if driving_distance > max_driving_distance:
                print(f"步骤5失败: 驾车距离{driving_distance}米超过要求{max_driving_distance}米")
                all_passed = False
            else:
                print(f"步骤5通过: 驾车距离{driving_distance}米，满足要求（<={max_driving_distance}米）")

    # 步骤6: 到指定公交站"省博物院南门"直线距离≤8000米
    print(f"\n步骤6: 验证到指定公交站的直线距离不超过{max_distance_to_bus_station}米")
    bus_station_detail = maps_search_detail(id=bus_station_poi_id)

    if bus_station_detail.error:
        print(f"步骤6失败: 获取公交站坐标失败 - {bus_station_detail.error}")
        all_passed = False
    else:
        if not bus_station_detail.location:
            print("步骤6失败: 未获取到公交站坐标")
            all_passed = False
        else:
            bus_station_location = bus_station_detail.location
            distance_result = maps_distance(
                origins=poi_location,
                destination=bus_station_location
            )

            if distance_result.error:
                print(f"步骤6失败: 计算距离失败 - {distance_result.error}")
                all_passed = False
            else:
                if not distance_result.results or len(distance_result.results) == 0:
                    print("步骤6失败: 未获取到距离结果")
                    all_passed = False
                else:
                    distance = distance_result.results[0].distance_meters
                    if distance > max_distance_to_bus_station:
                        print(f"步骤6失败: 到公交站的距离{distance}米超过要求{max_distance_to_bus_station}米")
                        all_passed = False
                    else:
                        print(f"步骤6通过: 到公交站的距离{distance}米，满足要求（<={max_distance_to_bus_station}米）")

    # 步骤7: 到合肥南站驾车时间≤20分钟
    print(f"\n步骤7: 验证到火车站的驾车时间不超过{max_driving_time_to_train_station}秒（{max_driving_time_to_train_station//60}分钟）")
    train_station_detail = maps_search_detail(id=train_station_poi_id)

    if train_station_detail.error:
        print(f"步骤7失败: 获取火车站坐标失败 - {train_station_detail.error}")
        all_passed = False
    else:
        if not train_station_detail.location:
            print("步骤7失败: 未获取到火车站坐标")
            all_passed = False
        else:
            train_station_location = train_station_detail.location
            driving_result_to_station = maps_driving_by_coordinates(
                origin=poi_location,
                destination=train_station_location
            )

            if driving_result_to_station.error:
                print(f"步骤7失败: 计算驾车时间失败 - {driving_result_to_station.error}")
                all_passed = False
            else:
                if driving_result_to_station.total_duration_seconds is None:
                    print("步骤7失败: 未获取到驾车时间")
                    all_passed = False
                else:
                    driving_time_to_station = driving_result_to_station.total_duration_seconds
                    if driving_time_to_station > max_driving_time_to_train_station:
                        print(f"步骤7失败: 驾车时间{driving_time_to_station}秒超过要求{max_driving_time_to_train_station}秒")
                        all_passed = False
                    else:
                        print(f"步骤7通过: 驾车时间{driving_time_to_station}秒，满足要求（<={max_driving_time_to_train_station}秒）")

    # 步骤8: 交通枢纽(地铁站)约束
    print(f"\n步骤8: 验证到地铁站的步行距离不超过{max_walking_distance_to_subway}米")
    subway_around_result = maps_around_search(
        location=poi_location,
        radius=subway_search_radius,
        keywords=subway_keywords
    )

    if subway_around_result.error:
        print(f"步骤8失败: {subway_around_result.error}")
        all_passed = False
    else:
        if not subway_around_result.pois or len(subway_around_result.pois) == 0:
            print(f"步骤8失败: 未找到任何{subway_keywords}")
            all_passed = False
        else:
            # 计算到每个地铁站的步行距离，找到最小值
            min_walking_distance = float('inf')
            for subway_poi in subway_around_result.pois:
                subway_detail = maps_search_detail(id=subway_poi.id)
                if subway_detail.error or not subway_detail.location:
                    continue

                subway_location = subway_detail.location
                walking_result_to_subway = maps_walking_by_coordinates(
                    origin=poi_location,
                    destination=subway_location
                )

                if walking_result_to_subway.error or walking_result_to_subway.total_distance_meters is None:
                    continue

                distance = walking_result_to_subway.total_distance_meters
                if distance < min_walking_distance:
                    min_walking_distance = distance

            if min_walking_distance == float('inf'):
                print("步骤8失败: 无法计算到任何地铁站的步行距离")
                all_passed = False
            elif min_walking_distance > max_walking_distance_to_subway:
                print(f"步骤8失败: 到最近地铁站的步行距离{min_walking_distance}米超过要求{max_walking_distance_to_subway}米")
                all_passed = False
            else:
                print(f"步骤8通过: 到最近地铁站的步行距离{min_walking_distance}米，满足要求（<={max_walking_distance_to_subway}米）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
