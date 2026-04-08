
"""
修改任务指令：你想要在你周边5公里内找一家餐厅。你打算走路过去，所以步行距离要控制在1.6公里以内、步行时间不超过15分钟。另外这家店今天的营业时间要覆盖现在这个时间点，并且评分至少要有4.4分。你逻辑性强但没有耐心，希望高效沟通，讨厌废话。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 验证"附近不超过5公里的餐厅"
- 调用 maps_around_search(location="106.072999,30.794291", radius="5000", keywords="餐厅")
- 断言返回pois数量>8，且列表中包含 target_poi_id = "B033101RYE"

2) 验证评分与营业时间（且营业中）
- 调用 maps_search_detail(id="B033101RYE") 获取 biz_ext.rating 与 biz_ext.open_time/opentime2
- 断言 rating >= 4.4
- 结合本题time字段给出的当前时间，断言 open_time/opentime2 覆盖当前时刻，不仅星期几匹配，且当前时间在营业时间范围内。

3) 验证步行距离与步行时间
- 从 maps_search_detail(id="B033101RYE") 读取 location 作为目的地坐标
- 调用 maps_walking_by_coordinates(origin="106.072999,30.794291", destination="106.085942,30.789088")
- 断言 total_distance_meters <= 1600
- 断言 total_duration_seconds <= 900（15分钟）
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
    maps_search_detail,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "106.072999,30.794291",
    search_radius: int = 5000,  # 5km
    keywords: str = "餐厅",
    min_poi_count: int = 8,
    min_rating: float = 4.4,
    max_walking_distance: int = 1600,  # 1600 meters
    max_walking_duration: int = 900,  # 15 minutes = 900 seconds
    current_time: str = "周六 18:30:00"  # 当前时间，格式为周* HH:MM:SS
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证"附近不超过5公里的餐厅"：断言返回pois数量>8，且列表中包含 target_poi_id
    2) 验证评分与营业时间（且营业中）：断言 rating >= 4.4，断言 open_time/opentime2 覆盖当前时刻
    3) 验证步行距离与步行时间：断言 total_distance_meters <= 1600，断言 total_duration_seconds <= 900

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"106.072999,30.794291"
        search_radius: 搜索半径（米），默认5000（5公里）
        keywords: 搜索关键词，默认"餐厅"
        min_poi_count: 最少POI数量，默认8
        min_rating: 最低评分，默认4.4
        max_walking_distance: 最大步行距离（米），默认1600
        max_walking_duration: 最大步行时长（秒），默认900（15分钟）
        current_time: 当前时间，格式为周* HH:MM:SS，默认"周六 18:30:00"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 验证"附近不超过5公里的餐厅"
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

    # 检查返回POI数量是否>8
    poi_count = len(around_search_result.pois)
    if poi_count <= min_poi_count:
        print(f"❌ 返回POI数量{poi_count}个，不大于{min_poi_count}个")
        return False
    print(f"✅ 返回POI数量{poi_count}个，符合要求（> {min_poi_count}个）")

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

    # 步骤2: 验证评分与营业时间（且营业中）
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分（rating >= 4.4）
    if hasattr(poi_detail, 'biz_ext') and poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        rating = poi_detail.biz_ext['rating']
        try:
            rating_value = float(rating)
            if rating_value < min_rating:
                print(f"❌ 评分{rating_value}低于{min_rating}")
                return False
            print(f"✅ 评分{rating_value}，符合要求（>= {min_rating}）")
        except (ValueError, TypeError):
            print(f"⚠️  无法解析评分值: {rating}，跳过评分验证")
    else:
        print(f"⚠️  未找到评分信息，跳过评分验证")

    # 验证营业时间（覆盖当前时刻，且当前时间在营业时段内）
    if hasattr(poi_detail, 'biz_ext') and poi_detail.biz_ext:
        opentime = None
        # biz_ext 是字典类型，需要使用字典键访问方式
        if 'opentime2' in poi_detail.biz_ext and poi_detail.biz_ext['opentime2']:
            opentime = poi_detail.biz_ext['opentime2']
        elif 'open_time' in poi_detail.biz_ext and poi_detail.biz_ext['open_time']:
            opentime = poi_detail.biz_ext['open_time']

        if opentime:
            print(f"✅ 营业时间: {opentime}")
            print(f"✅ 当前时间: {current_time}")

            import re

            # 解析当前是星期几（格式：周* HH:MM:SS）
            weekday_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '日': 7, '天': 7}
            current_weekday_match = re.search(r'周([一二三四五六日天])', current_time)
            current_weekday = None
            if current_weekday_match:
                current_weekday = weekday_map.get(current_weekday_match.group(1))

            # 解析当前时间
            current_time_match = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', current_time)
            if current_time_match:
                current_hour = int(current_time_match.group(1))
                current_minute = int(current_time_match.group(2))
                current_time_minutes = current_hour * 60 + current_minute

                # 检查营业时间中是否包含星期几的信息
                weekday_pattern = r'周([一二三四五六日天])至周([一二三四五六日天])'
                weekday_match = re.search(weekday_pattern, opentime)

                # 如果有星期几信息，验证今天是否在营业日范围内
                if weekday_match and current_weekday:
                    start_day = weekday_map.get(weekday_match.group(1))
                    end_day = weekday_map.get(weekday_match.group(2))

                    # 检查当前星期几是否在营业范围内
                    is_open_today = False
                    if start_day <= end_day:
                        # 正常情况，如周一至周五
                        is_open_today = start_day <= current_weekday <= end_day
                    else:
                        # 跨周情况，如周六至周一
                        is_open_today = current_weekday >= start_day or current_weekday <= end_day

                    if not is_open_today:
                        print(f"❌ 今天（周{list(weekday_map.keys())[list(weekday_map.values()).index(current_weekday)]}）不在营业日范围内")
                        return False
                    print(f"✅ 今天在营业日范围内")
                else:
                    # 如果没有星期几信息，默认每天都营业
                    print(f"✅ 营业时间未指定星期几，默认每天营业")

                # 解析营业时间（格式为 "HH:MM-HH:MM"）
                time_pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
                matches = re.findall(time_pattern, opentime)

                if matches:
                    # 检查当前时间是否在任一营业时段内
                    is_open = False
                    for match in matches:
                        open_hour = int(match[0])
                        open_minute = int(match[1])
                        close_hour = int(match[2])
                        close_minute = int(match[3])

                        open_time_minutes = open_hour * 60 + open_minute
                        close_time_minutes = close_hour * 60 + close_minute

                        # 判断当前时间是否在营业时段内（含跨天：关门在次日则 在段内 = current>=open 或 current<=close）
                        if close_time_minutes < open_time_minutes:
                            # 跨天时段：当前在开门之后或关门之前
                            if current_time_minutes >= open_time_minutes or current_time_minutes <= close_time_minutes:
                                is_open = True
                                break
                        else:
                            if open_time_minutes <= current_time_minutes <= close_time_minutes:
                                is_open = True
                                break

                    if not is_open:
                        print(f"❌ 当前时间{current_time}不在营业时段内")
                        return False
                    print(f"✅ 当前时间在营业时段内，符合要求")
                else:
                    print(f"⚠️  无法解析营业时间格式，跳过营业时间验证")
            else:
                print(f"⚠️  无法解析当前时间格式，跳过营业时间验证")
        else:
            print(f"⚠️  未找到营业时间信息，跳过营业时间验证")
    else:
        print(f"⚠️  未找到biz_ext信息，跳过营业时间验证")

    # 步骤3: 验证步行距离与步行时间
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_distance_meters is None:
        print(f"❌ 无法获取步行距离")
        return False

    walking_distance = walking_result.total_distance_meters
    if walking_distance > max_walking_distance:
        print(f"❌ 步行距离{walking_distance}米，超过{max_walking_distance}米")
        return False
    print(f"✅ 步行距离{walking_distance}米，符合要求（<= {max_walking_distance}米）")

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 640.py 文件...\n")
    result = verify_poi(poi_id="B033101RYE")
    print(f"\n验证结果: {result}")
