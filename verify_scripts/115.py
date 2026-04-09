
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_search_detail(target_poi_id) 获取POI详情：确认POI类型为咖啡厅/咖啡相关；读取biz_ext.rating>=4.3；读取biz_ext.open_time或opentime2，验证今日营业开始时间<=07:00。
2) 调用 maps_around_search(location=112.1366,32.088017; radius=2000; keywords=咖啡厅)，验证返回pois中包含 target_poi_id（满足"附近2公里内"）。
3) 调用 maps_walking_by_coordinates(origin=112.1366,32.088017; destination=POI.location)，验证 total_duration_seconds<=600（10分钟）。
4) 调用 maps_text_search(keywords=station_address, city=station_city) 取 poi_id，再 maps_search_detail(id=poi_id) 获取 襄阳站坐标 station_loc。
5) 调用 maps_bicycling_by_coordinates(origin=station_loc; destination=POI.location)，验证 total_duration_seconds<=1200（20分钟）。
"""

import os
import sys

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 导入高德地图工具函数
from tools.amap_tools import (
    maps_text_search,
    maps_search_detail,
    maps_walking_by_coordinates ,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "112.1366,32.088017",
    search_radius: int = 2000,  # 2km
    keywords: str = "咖啡厅",
    min_rating: float = 4.3,
    max_opening_time: str = "07:00",  # 营业开始时间不晚于07:00
    max_walking_duration: int = 600,  # 10 minutes = 600 seconds
    station_address: str = "襄阳站",
    station_city: str = "襄阳",
    max_bicycling_duration_from_station: int = 1200  # 20 minutes = 1200 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 调用 maps_search_detail 获取POI详情：确认POI类型为咖啡厅/咖啡相关；读取biz_ext.rating>=4.3；读取biz_ext.open_time或opentime2，验证今日营业开始时间<=07:00。
    2) 调用 maps_around_search，验证返回pois中包含 target_poi_id。
    3) 调用 maps_walking_by_coordinates，验证 total_duration_seconds<=600。
    4) 调用获取襄阳站坐标。
    5) 调用 maps_bicycling_by_coordinates，验证 total_duration_seconds<=1200。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"112.1366,32.088017"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"咖啡厅"
        min_rating: 最低评分，默认4.3
        max_opening_time: 最晚营业开始时间，默认"07:00"
        max_walking_duration: 最大步行时长（秒），默认600（10分钟）
        station_address: 火车站地址，默认"襄阳站"
        station_city: 火车站所在城市，默认"襄阳"
        max_bicycling_duration_from_station: 从火车站到POI的最大骑行时长（秒），默认1200（20分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 获取目标POI详情
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤2: 验证评分>=4.3
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False

    rating = poi_detail.biz_ext.get('rating')
    if rating is None:
        print(f"❌ POI没有rating信息")
        return False

    try:
        rating_value = float(rating)
    except (ValueError, TypeError):
        print(f"❌ 无法解析rating值: {rating}")
        return False

    if rating_value < min_rating:
        print(f"❌ 评分{rating_value}分，低于{min_rating}分")
        return False
    print(f"✅ 评分{rating_value}分，符合要求（>= {min_rating}分）")

    # 步骤3: 验证营业开始时间<=07:00
    open_time = poi_detail.biz_ext.get('open_time') or poi_detail.biz_ext.get('opentime2')
    if not open_time:
        print(f"❌ POI没有营业时间信息")
        return False

    print(f"✅ 获取营业时间: {open_time}")

    # 解析营业开始时间
    import re
    # 提取时间段（例如 "07:00-22:00" 或 "周一至周日 07:00-22:00"）
    time_pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
    match = re.search(time_pattern, open_time)

    if not match:
        print(f"❌ 无法解析营业时间格式: {open_time}")
        return False

    start_hour = int(match.group(1))
    start_minute = int(match.group(2))

    # 解析最晚营业开始时间
    max_time_pattern = r'(\d{1,2}):(\d{2})'
    max_match = re.match(max_time_pattern, max_opening_time)
    if not max_match:
        print(f"❌ 无法解析最晚营业开始时间格式: {max_opening_time}")
        return False

    max_hour = int(max_match.group(1))
    max_minute = int(max_match.group(2))

    # 比较营业开始时间
    start_time_minutes = start_hour * 60 + start_minute
    max_time_minutes = max_hour * 60 + max_minute

    if start_time_minutes > max_time_minutes:
        print(f"❌ 营业开始时间{start_hour:02d}:{start_minute:02d}，晚于要求的{max_opening_time}")
        return False

    print(f"✅ 营业开始时间{start_hour:02d}:{start_minute:02d}，符合要求（<= {max_opening_time}）")

    # 步骤4: 距离约束（附近2公里）
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois or len(around_search_result.pois) == 0:
        print(f"❌ 未找到符合条件的POI")
        return False

    # 检查返回列表中是否包含目标POI ID
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break

    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False

    # 步骤5: 步行时间<=10分钟
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    # 步骤6: 获取襄阳站坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"❌ 获取火车站坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到火车站坐标")
        return False

    first_poi_id = station_text_result.pois[0].id
    station_detail_result = maps_search_detail(id=first_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取坐标失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print("❌ 未获取到坐标")
        return False

    station_location = station_detail_result.location
    print(f"✅ 获取火车站坐标: {station_location} ({station_address})")

    # 步骤7: 从火车站骑行到POI的时间<=20分钟
    bicycling_result = maps_bicycling_by_coordinates(origin=station_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算从火车站到POI的骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取从火车站到POI的骑行时长")
        return False

    bicycling_duration = bicycling_result.total_duration_seconds
    if bicycling_duration > max_bicycling_duration_from_station:
        print(f"❌ 从火车站到POI的骑行时长{bicycling_duration}秒，超过{max_bicycling_duration_from_station}秒（{max_bicycling_duration_from_station // 60}分钟）")
        return False
    print(f"✅ 从火车站到POI的骑行时长{bicycling_duration}秒，符合要求（<= {max_bicycling_duration_from_station}秒，即{max_bicycling_duration_from_station // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 727.py 文件...\n")
    result = verify_poi(poi_id="B0H6HAEK14")
    print(f"\n验证结果: {result}")
