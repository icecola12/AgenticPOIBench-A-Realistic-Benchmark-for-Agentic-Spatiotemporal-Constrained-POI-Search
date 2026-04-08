"""
输入：B0K22S0E2I
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
步骤1：验证“附近1500米以内的青年旅舍”
- 调用 maps_around_search(location='117.29422,31.877043', radius='1500', keywords='青年旅舍')
- 验证返回结果中包含目标POI：B0K22S0E2I。

步骤2：验证“评分至少4.0分”
- 调用 maps_search_detail(id='B0K22S0E2I')
- 从 biz_ext.rating 读取评分，验证 rating >= 4.0。（该POI返回 rating='4.1'）

步骤3：验证“到合肥站开车不超过8分钟”
- 调用 maps_text_search(keywords='合肥站', city='合肥', citylimit='true') 获取合肥站坐标（取POI：B022700CD7，location='117.316937,31.885135'）
- 调用 maps_search_detail(id='B0K22S0E2I') 获取旅舍坐标（location='117.306975,31.874425'）
- 调用 maps_driving_by_coordinates(origin='117.316937,31.885135', destination='117.306975,31.874425')
- 验证 total_duration_seconds <= 480秒。

步骤4：验证公共交通与配套约束（地铁、公交、便利店）
(4.1) 验证“旅舍到最近地铁站步行≤15分钟，且最近地铁站在旅舍周边1200米内”
- 调用 maps_around_search(location='117.306975,31.874425', radius='1200', keywords='地铁站') 获取候选地铁站列表
- 对每个候选地铁站i，调用 maps_walking_by_coordinates(origin='117.306975,31.874425', destination=地铁站i.location) 得到步行时长
- 取最小步行时长 t_min，验证 t_min <= 900秒。
（示例：明光路地铁站 location='117.304588,31.869977'，步行 total_duration_seconds=592秒，满足）

(4.2) 验证“到炉桥路公交站直线距离≤1200米”
- 调用 maps_text_search(keywords='炉桥路公交站', city='合肥', citylimit='true') 获取公交站坐标（取POI：BV10414534，location='117.296664,31.877987'）
- 调用 maps_distance(origins='117.306975,31.874425', destination='117.296664,31.877987')
- 验证 distance_meters <= 1200。
（该结果 distance_meters=1052，满足）

(4.3) 验证“旅舍周边500米内有便利店”
- 调用 maps_around_search(location='117.306975,31.874425', radius='500', keywords='便利店')
- 验证 pois 列表非空即可。
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
    target_poi_id: str = "B0K22S0E2I",
    user_location: str = "117.29422,31.877043",
    radius: str = "1500",
    keywords: str = "青年旅舍",
    min_rating: float = 4.0,
    station_keywords: str = "合肥站",
    station_city: str = "合肥",
    station_citylimit: str = "true",
    station_poi_id: str = "B022700CD7",
    max_driving_time_to_station: int = 480,
    subway_search_radius: str = "1200",
    subway_keywords: str = "地铁站",
    max_walking_time_to_subway: int = 900,
    bus_station_keywords: str = "炉桥路公交站",
    bus_station_city: str = "合肥",
    bus_station_citylimit: str = "true",
    bus_station_poi_id: str = "BV10414534",
    max_distance_to_bus_station: int = 1200,
    convenience_store_radius: str = "500",
    convenience_store_keywords: str = "便利店"
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        min_rating: 最小评分
        station_keywords: 火车站搜索关键词
        station_city: 火车站所在城市
        station_citylimit: 是否限制城市
        station_poi_id: 火车站POI ID
        max_driving_time_to_station: 到火车站的最大驾车时间（秒）
        subway_search_radius: 地铁站搜索半径（米）
        subway_keywords: 地铁站搜索关键词
        max_walking_time_to_subway: 到地铁站的最大步行时间（秒）
        bus_station_keywords: 公交站搜索关键词
        bus_station_city: 公交站所在城市
        bus_station_citylimit: 是否限制城市
        bus_station_poi_id: 公交站POI ID
        max_distance_to_bus_station: 到公交站的最大直线距离（米）
        convenience_store_radius: 便利店搜索半径（米）
        convenience_store_keywords: 便利店搜索关键词

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 验证"附近1500米以内的青年旅舍"
    print(f"步骤1: 验证附近{radius}米内的{keywords}约束 - 查询POI ID: {target_poi_id}")
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

    # 步骤2: 验证"评分至少4.0分"
    print(f"\n步骤2: 验证评分 >= {min_rating}")
    poi_detail = maps_search_detail(id=target_poi_id)

    if poi_detail.error:
        print(f"步骤2失败: {poi_detail.error}")
        print("错误: 无法获取POI详情，无法继续验证")
        return False

    # 获取POI坐标（后续步骤需要）
    if not poi_detail.location:
        print("错误: 未获取到POI坐标，无法继续验证")
        return False

    poi_location = poi_detail.location
    print(f"POI坐标: {poi_location}")

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

    # 步骤3: 验证"到合肥站开车不超过8分钟"
    print(f"\n步骤3: 验证到{station_keywords}开车时间不超过{max_driving_time_to_station}秒（{max_driving_time_to_station//60}分钟）")

    # 获取合肥站坐标
    station_detail = maps_search_detail(id=station_poi_id)

    if station_detail.error:
        print(f"步骤3失败: 获取{station_keywords}坐标失败 - {station_detail.error}")
        all_passed = False
    else:
        if not station_detail.location:
            print(f"步骤3失败: 未获取到{station_keywords}坐标")
            all_passed = False
        else:
            station_location = station_detail.location
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

    # 步骤4.1: 验证"旅舍到最近地铁站步行≤15分钟，且最近地铁站在旅舍周边1200米内"
    print(f"\n步骤4.1: 验证到最近{subway_keywords}步行时间不超过{max_walking_time_to_subway}秒（{max_walking_time_to_subway//60}分钟）")
    subway_around_result = maps_around_search(
        location=poi_location,
        radius=subway_search_radius,
        keywords=subway_keywords
    )

    if subway_around_result.error:
        print(f"步骤4.1失败: {subway_around_result.error}")
        all_passed = False
    else:
        if not subway_around_result.pois or len(subway_around_result.pois) == 0:
            print(f"步骤4.1失败: 未找到任何{subway_keywords}")
            all_passed = False
        else:
            # 计算到每个地铁站的步行时间，找到最小值
            min_walking_time = float('inf')
            for subway_poi in subway_around_result.pois:
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
                print("步骤4.1失败: 无法计算到任何地铁站的步行时间")
                all_passed = False
            elif min_walking_time > max_walking_time_to_subway:
                print(f"步骤4.1失败: 到最近地铁站的步行时间{min_walking_time}秒超过要求{max_walking_time_to_subway}秒")
                all_passed = False
            else:
                print(f"步骤4.1通过: 到最近地铁站的步行时间{min_walking_time}秒，满足要求（<={max_walking_time_to_subway}秒）")

    # 步骤4.2: 验证"到炉桥路公交站直线距离≤1200米"
    print(f"\n步骤4.2: 验证到指定公交站的直线距离不超过{max_distance_to_bus_station}米")

    # 获取公交站坐标
    bus_station_detail = maps_search_detail(id=bus_station_poi_id)

    if bus_station_detail.error:
        print(f"步骤4.2失败: 获取公交站坐标失败 - {bus_station_detail.error}")
        all_passed = False
    else:
        if not bus_station_detail.location:
            print("步骤4.2失败: 未获取到公交站坐标")
            all_passed = False
        else:
            bus_station_location = bus_station_detail.location
            distance_result = maps_distance(
                origins=poi_location,
                destination=bus_station_location
            )

            if distance_result.error:
                print(f"步骤4.2失败: 计算距离失败 - {distance_result.error}")
                all_passed = False
            else:
                if not distance_result.results or len(distance_result.results) == 0:
                    print("步骤4.2失败: 未获取到距离结果")
                    all_passed = False
                else:
                    distance = distance_result.results[0].distance_meters
                    if distance > max_distance_to_bus_station:
                        print(f"步骤4.2失败: 到公交站的距离{distance}米超过要求{max_distance_to_bus_station}米")
                        all_passed = False
                    else:
                        print(f"步骤4.2通过: 到公交站的距离{distance}米，满足要求（<={max_distance_to_bus_station}米）")

    # 步骤4.3: 验证"旅舍周边500米内有便利店"
    print(f"\n步骤4.3: 验证周边{convenience_store_radius}米内有{convenience_store_keywords}")
    convenience_store_result = maps_around_search(
        location=poi_location,
        radius=convenience_store_radius,
        keywords=convenience_store_keywords
    )

    if convenience_store_result.error:
        print(f"步骤4.3失败: {convenience_store_result.error}")
        all_passed = False
    else:
        if not convenience_store_result.pois or len(convenience_store_result.pois) == 0:
            print(f"步骤4.3失败: 未找到任何{convenience_store_keywords}")
            all_passed = False
        else:
            store_count = len(convenience_store_result.pois)
            print(f"步骤4.3通过: 找到{store_count}个{convenience_store_keywords}，满足要求（数量>0）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
