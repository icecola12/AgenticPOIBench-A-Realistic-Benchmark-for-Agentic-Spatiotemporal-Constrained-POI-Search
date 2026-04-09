
"""
修改任务指令：你想找一家附近2公里的咖啡厅，方便你中午过去等人顺便把合同打印出来签字。你希望走路过去别超过20分钟，而且骑车过去要在8分钟以内。为了让对方也好到，你还要求这家店到附近800米最近的地铁站走路不超过12分钟。最后你希望这家咖啡厅现在这个时间点还在营业，并且评分至少要有4.0分。你说话非常有条理和注重细节
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 详情与营业时间/评分：对目标poi_id调用 maps_search_detail，读取 biz_ext.rating 与 biz_ext.open_time/opentime2；验证 rating >= 4.0；并结合给定的time字段，验证当前时刻落在其营业时间内（本POI: 周一至周五 09:00-19:30；周六至周日 10:00-19:00）。
2) 附近2公里约束：以用户坐标(125.275516,43.853659)为中心调用 maps_around_search，radius=2000，keywords=咖啡厅；验证返回pois中包含目标poi_id。
3) 步行时间约束：调用 maps_walking_by_coordinates(origin=用户坐标, destination=POI坐标) 得到 total_duration_seconds=t_walk；验证 t_walk <= 20*60。
4) 骑行时间约束：调用 maps_bicycling_by_coordinates(origin=用户坐标, destination=POI坐标) 得到 total_duration_seconds=t_bike；验证 t_bike <= 8*60。
5) 地铁站步行可达约束：以POI坐标为中心调用 maps_around_search，radius=800，keywords=地铁站，取返回pois中任一地铁站location作为候选；分别对每个候选调用 maps_walking_by_coordinates(origin=POI坐标, destination=地铁站坐标) 得到最小步行时长 t_subway_min；验证 t_subway_min <= 12*60。
"""

import os
import sys
from datetime import datetime

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 导入高德地图工具函数
from tools.amap_tools import (
    maps_search_detail,
    maps_walking_by_coordinates,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "125.275516,43.853659",
    search_radius: int = 2000,  # 2km
    keywords: str = "咖啡厅",
    min_rating: float = 4.0,
    max_walking_duration: int = 1200,  # 20 minutes = 1200 seconds
    max_bicycling_duration: int = 480,  # 8 minutes = 480 seconds
    subway_search_radius: int = 800,  # 800m
    subway_keywords: str = "地铁站",
    max_walking_duration_to_subway: int = 720,  # 12 minutes = 720 seconds
    current_time: str = "周二 11:20:00"  # 当前时间
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 详情与营业时间/评分：对目标poi_id调用 maps_search_detail，读取 biz_ext.rating 与 biz_ext.open_time/opentime2；验证 rating >= 4.0；并结合给定的time字段，验证当前时刻落在其营业时间内。
    2) 附近2公里约束：以用户坐标为中心调用 maps_around_search，验证返回pois中包含目标poi_id。
    3) 步行时间约束：调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 1200（20分钟）。
    4) 骑行时间约束：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds <= 480（8分钟）。
    5) 地铁站步行可达约束：以POI坐标为中心调用 maps_around_search，取返回pois中任一地铁站location作为候选；分别对每个候选调用 maps_walking_by_coordinates 得到最小步行时长；验证 <= 720（12分钟）。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"125.275516,43.853659"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"咖啡厅"
        min_rating: 最低评分，默认4.0
        max_walking_duration: 从用户位置到POI的最大步行时长（秒），默认1200（20分钟）
        max_bicycling_duration: 从用户位置到POI的最大骑行时长（秒），默认480（8分钟）
        subway_search_radius: 地铁站搜索半径（米），默认800
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_walking_duration_to_subway: 从POI到地铁站的最大步行时长（秒），默认720（12分钟）
        current_time: 当前时间，格式为"周X HH:MM:SS"，默认"周二 11:20:00"

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

    # 步骤2: 验证评分>=4.0
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

    # 步骤3: 验证营业时间
    open_time = poi_detail.biz_ext.get('open_time') or poi_detail.biz_ext.get('opentime2')
    if not open_time:
        print(f"❌ POI没有营业时间信息")
        return False

    print(f"✅ 获取营业时间: {open_time}")

    # 解析营业时间并验证当前时间是否在营业时间内
    import re

    # 解析当前时间字符串（格式：周X HH:MM:SS）
    weekday_map = {'周一': 0, '周二': 1, '周三': 2, '周四': 3, '周五': 4, '周六': 5, '周日': 6}
    time_parse_pattern = r'(周[一二三四五六日])\s+(\d{1,2}):(\d{2}):(\d{2})'
    time_match = re.match(time_parse_pattern, current_time)

    if not time_match:
        print(f"❌ 无法解析当前时间格式: {current_time}")
        return False

    weekday_str = time_match.group(1)
    current_hour = int(time_match.group(2))
    current_minute = int(time_match.group(3))
    current_weekday = weekday_map.get(weekday_str)

    if current_weekday is None:
        print(f"❌ 无法解析星期信息: {weekday_str}")
        return False

    current_time_minutes = current_hour * 60 + current_minute
    print(f"✅ 当前时间: {current_time}")

    # 检查是否包含星期信息
    weekday_pattern = r'(周[一二三四五六日])至(周[一二三四五六日])'
    weekday_match = re.search(weekday_pattern, open_time)

    # 如果有星期信息，先验证星期是否匹配
    if weekday_match:
        start_day_str = weekday_match.group(1)
        end_day_str = weekday_match.group(2)
        start_day = weekday_map.get(start_day_str)
        end_day = weekday_map.get(end_day_str)

        if start_day is None or end_day is None:
            print(f"❌ 无法解析星期信息: {start_day_str} 至 {end_day_str}")
            return False

        # 检查当前星期是否在营业范围内
        if start_day <= end_day:
            # 不跨周（例如：周一至周五）
            day_match = start_day <= current_weekday <= end_day
        else:
            # 跨周（例如：周六至周一，虽然这种情况比较少见）
            day_match = current_weekday >= start_day or current_weekday <= end_day

        if not day_match:
            weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            current_day_name = weekday_names[current_weekday]
            print(f"❌ 当前是{current_day_name}，不在营业日期{start_day_str}至{end_day_str}范围内")
            return False

        print(f"✅ 当前星期在营业日期范围内")

    # 提取时间段（例如 "09:00-19:30" 或 "周一至周五 09:00-19:30"）
    time_pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
    match = re.search(time_pattern, open_time)

    if not match:
        print(f"❌ 无法解析营业时间格式: {open_time}")
        return False

    start_hour, start_minute, end_hour, end_minute = map(int, match.groups())
    start_time_minutes = start_hour * 60 + start_minute
    end_time_minutes = end_hour * 60 + end_minute

    # 处理跨天的情况（例如 10:00-02:00，结束时间是第二天凌晨）
    if end_time_minutes < start_time_minutes:
        # 跨天营业：如果当前时间 >= 开始时间 或 当前时间 <= 结束时间
        is_open = current_time_minutes >= start_time_minutes or current_time_minutes <= end_time_minutes
    else:
        # 不跨天营业：当前时间必须在开始和结束时间之间
        is_open = start_time_minutes <= current_time_minutes <= end_time_minutes

    if not is_open:
        print(f"❌ 当前时间{current_hour:02d}:{current_minute:02d}不在营业时间{open_time}内")
        return False

    print(f"✅ 当前时间{current_hour:02d}:{current_minute:02d}在营业时间{open_time}内，验证通过")

    # 步骤4: 附近2公里约束
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

    # 步骤5: 步行时间约束（<=20分钟）
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

    # 步骤6: 骑行时间约束（<=8分钟）
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取骑行时长")
        return False

    bicycling_duration = bicycling_result.total_duration_seconds
    if bicycling_duration > max_bicycling_duration:
        print(f"❌ 骑行时长{bicycling_duration}秒，超过{max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 骑行时长{bicycling_duration}秒，符合要求（<= {max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")

    # 步骤7: 搜索POI附近800米内的地铁站
    subway_search_result = maps_around_search(
        location=poi_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ POI附近{subway_search_radius}米内未找到地铁站")
        return False

    print(f"✅ POI附近{subway_search_radius}米内找到{len(subway_search_result.pois)}个地铁站")

    # 步骤8: 找到步行时间最短的地铁站
    closest_subway = None
    min_walking_duration = float('inf')

    for subway in subway_search_result.pois:
        if not subway.location:
            continue

        walking_result_to_subway = maps_walking_by_coordinates(origin=poi_location, destination=subway.location)
        if walking_result_to_subway.error or walking_result_to_subway.total_duration_seconds is None:
            continue

        walking_duration = walking_result_to_subway.total_duration_seconds
        # print(f"  - {subway.name}: 步行时长{walking_duration}秒（{walking_duration // 60}分钟）")

        if walking_duration < min_walking_duration:
            min_walking_duration = walking_duration
            closest_subway = subway

    if closest_subway is None:
        print(f"❌ 无法找到可步行到达的地铁站")
        return False

    print(f"✅ 找到最近的地铁站: {closest_subway.name}，步行时长{min_walking_duration}秒（{min_walking_duration // 60}分钟）")

    if min_walking_duration > max_walking_duration_to_subway:
        print(f"❌ 到最近地铁站的步行时长{min_walking_duration}秒，超过{max_walking_duration_to_subway}秒（{max_walking_duration_to_subway // 60}分钟）")
        return False

    print(f"✅ 到最近地铁站的步行时长符合要求（<= {max_walking_duration_to_subway}秒，即{max_walking_duration_to_subway // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 723.py 文件...\n")
    result = verify_poi(poi_id="B0KBFRWLBA")
    print(f"\n验证结果: {result}")
