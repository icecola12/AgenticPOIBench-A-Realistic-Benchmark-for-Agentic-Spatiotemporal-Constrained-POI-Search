"""
输入：B001D06AOS
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近直线距离≤1200米：调用 maps_search_detail('B001D06AOS') 获取目标POI坐标destination；调用 maps_distance(origins='108.930698,34.234571', destination=destination) 验证distance_meters ≤ 1200。
2) 最大骑行距离≤1300米：调用 maps_bicycling_by_coordinates(origin='108.930698,34.234571', destination=destination) 验证 total_distance_meters ≤ 1300。
3) 最大驾车距离≤2公里：调用 maps_driving_by_coordinates(origin='108.930698,34.234571', destination=destination) 验证 total_distance_meters ≤ 2000。
4) 博物馆评分≥4.7：调用 maps_search_detail('B001D06AOS')，读取 biz_ext.rating，验证 rating ≥ 4.7。
5) 营业时间覆盖09:00-17:00：调用 maps_search_detail('B001D06AOS')，读取 biz_ext.open_time 或 biz_ext.opentime2，验证包含“09:00-17:00”。并结合场景 time（见输出time字段）验证当前时间早于17:00。
6) 地铁站约束（两段式）：
a. 调用 maps_around_search(location=destination, keywords='地铁站', radius='800') 获取候选地铁站列表。
b. 对每个地铁站poi调用 maps_walking_by_coordinates(origin=destination, destination=station.location) 计算步行距离，取最小 total_distance_meters，验证最小值 ≤ 2500。
7) 到西安火车站驾车时间≤10分钟：调用 maps_text_search(keywords='西安火车站', city='西安') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取火车站坐标station_loc；调用 maps_driving_by_coordinates(origin=destination, destination=station_loc) 验证 total_duration_seconds ≤ 600。
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
    target_poi_id: str = "B001D06AOS",
    user_location: str = "108.930698,34.234571",
    max_distance: int = 1200,
    max_bicycling_distance: int = 1300,
    max_driving_distance: int = 2000,
    min_rating: float = 4.7,
    required_time_range: str = "09:00-17:00",
    subway_search_radius: str = "800",
    subway_keywords: str = "地铁站",
    max_walking_distance_to_subway: int = 2500,
    station_address: str = "西安火车站",
    station_city: str = "西安",
    max_driving_time_to_station: int = 600
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        max_distance: 最大直线距离（米）
        max_bicycling_distance: 最大骑行距离（米）
        max_driving_distance: 最大驾车距离（米）
        min_rating: 最小评分
        required_time_range: 要求的营业时间范围
        subway_search_radius: 地铁站搜索半径（米）
        subway_keywords: 地铁站搜索关键词
        max_walking_distance_to_subway: 到地铁站的最大步行距离（米）
        station_address: 火车站地址
        station_city: 火车站所在城市
        max_driving_time_to_station: 到火车站的最大驾车时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 附近直线距离≤1200米
    print(f"步骤1: 验证直线距离不超过{max_distance}米")
    poi_detail = maps_search_detail(id=target_poi_id)

    if poi_detail.error:
        print(f"步骤1失败: 获取POI详情失败 - {poi_detail.error}")
        return False

    if not poi_detail.location:
        print("步骤1失败: 未获取到POI坐标")
        return False

    poi_location = poi_detail.location
    print(f"POI坐标: {poi_location}")

    distance_result = maps_distance(
        origins=user_location,
        destination=poi_location
    )

    if distance_result.error:
        print(f"步骤1失败: 计算距离失败 - {distance_result.error}")
        all_passed = False
    else:
        if not distance_result.results or len(distance_result.results) == 0:
            print("步骤1失败: 未获取到距离结果")
            all_passed = False
        else:
            distance = distance_result.results[0].distance_meters
            if distance > max_distance:
                print(f"步骤1失败: 直线距离{distance}米超过要求{max_distance}米")
                all_passed = False
            else:
                print(f"步骤1通过: 直线距离{distance}米，满足要求（<={max_distance}米）")

    # 步骤2: 最大骑行距离≤1300米
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

    # 步骤3: 最大驾车距离≤2公里
    print(f"\n步骤3: 验证驾车距离不超过{max_driving_distance}米")
    driving_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=poi_location
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

    # 步骤4: 博物馆评分≥4.7
    print(f"\n步骤4: 验证评分 >= {min_rating}")
    if not poi_detail.biz_ext:
        print("步骤4失败: 未获取到POI扩展信息")
        all_passed = False
    else:
        rating = poi_detail.biz_ext.get('rating')
        if rating is None:
            print("步骤4失败: 未获取到评分信息")
            all_passed = False
        else:
            try:
                rating_value = float(rating)
                if rating_value < min_rating:
                    print(f"步骤4失败: 评分{rating_value}小于要求{min_rating}")
                    all_passed = False
                else:
                    print(f"步骤4通过: 评分{rating_value}，满足要求（>={min_rating}）")
            except (ValueError, TypeError):
                print(f"步骤4失败: 评分格式错误: {rating}")
                all_passed = False

    # 步骤5: 营业时间覆盖09:00-17:00
    print(f"\n步骤5: 验证营业时间覆盖{required_time_range}")
    if not poi_detail.biz_ext:
        print("步骤5失败: 未获取到POI扩展信息")
        all_passed = False
    else:
        open_time = poi_detail.biz_ext.get('open_time') or poi_detail.biz_ext.get('opentime2')
        if open_time is None:
            print("步骤5失败: 未获取到营业时间信息")
            all_passed = False
        else:
            if required_time_range not in str(open_time):
                print(f"步骤5失败: 营业时间'{open_time}'不包含要求的时间范围'{required_time_range}'")
                all_passed = False
            else:
                print(f"步骤5通过: 营业时间'{open_time}'包含要求的时间范围'{required_time_range}'")

    # 步骤6: 地铁站约束
    print(f"\n步骤6: 验证到地铁站的步行距离不超过{max_walking_distance_to_subway}米")
    subway_around_result = maps_around_search(
        location=poi_location,
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
            # 计算到每个地铁站的步行距离，找到最小值
            min_walking_distance = float('inf')
            for subway_poi in subway_around_result.pois:
                subway_detail = maps_search_detail(id=subway_poi.id)
                if subway_detail.error or not subway_detail.location:
                    continue

                subway_location = subway_detail.location
                walking_result = maps_walking_by_coordinates(
                    origin=poi_location,
                    destination=subway_location
                )

                if walking_result.error or walking_result.total_distance_meters is None:
                    continue

                distance = walking_result.total_distance_meters
                if distance < min_walking_distance:
                    min_walking_distance = distance

            if min_walking_distance == float('inf'):
                print("步骤6失败: 无法计算到任何地铁站的步行距离")
                all_passed = False
            elif min_walking_distance > max_walking_distance_to_subway:
                print(f"步骤6失败: 到最近地铁站的步行距离{min_walking_distance}米超过要求{max_walking_distance_to_subway}米")
                all_passed = False
            else:
                print(f"步骤6通过: 到最近地铁站的步行距离{min_walking_distance}米，满足要求（<={max_walking_distance_to_subway}米）")

    # 步骤7: 到西安火车站驾车时间≤10分钟
    print(f"\n步骤7: 验证到{station_address}的驾车时间不超过{max_driving_time_to_station}秒（{max_driving_time_to_station//60}分钟）")
    text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if text_search_result.error:
        print(f"步骤7失败: 获取{station_address}坐标失败 - {text_search_result.error}")
        all_passed = False
    elif not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"步骤7失败: 未找到{station_address}坐标")
        all_passed = False
    else:
        first_poi_id = text_search_result.pois[0].id
        detail_result = maps_search_detail(id=first_poi_id)
        if detail_result.error or not detail_result.location:
            print(f"步骤7失败: 获取{station_address}坐标失败 - {detail_result.error or '无location'}")
            all_passed = False
        else:
            station_location = detail_result.location
            print(f"{station_address}坐标: {station_location}")

            driving_result_to_station = maps_driving_by_coordinates(
                origin=poi_location,
                destination=station_location
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
                    if driving_time_to_station > max_driving_time_to_station:
                        print(f"步骤7失败: 驾车时间{driving_time_to_station}秒超过要求{max_driving_time_to_station}秒")
                        all_passed = False
                    else:
                        print(f"步骤7通过: 驾车时间{driving_time_to_station}秒，满足要求（<={max_driving_time_to_station}秒）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
