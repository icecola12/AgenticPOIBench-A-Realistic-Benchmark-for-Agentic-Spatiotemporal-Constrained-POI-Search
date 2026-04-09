
"""
修改任务指令：你想找一家附近2公里内的餐厅，骑共享单车过去的路程不要超过2.5公里。餐厅附近600米内要有一个地铁站。你打算现在就过去，所以餐厅现在必须还在营业，并且评分要至少4.6分。为了方便朋友开车来接你，朋友从你这里开车到餐厅的时间必须不超过5分钟。你虽然心情不好，但仍然保持礼貌和独立的姿态。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束(附近2公里)：以用户坐标115.912814,28.702118为中心，调用maps_around_search(location=115.912814,28.702118,radius=2000,keywords=餐厅)，验证目标poi_id=B0FFFF5RXS在返回pois列表中。
2) 骑行距离不超过2.5公里：调用maps_search_detail(B0FFFF5RXS)取其location=115.903209,28.691623；再调用maps_bicycling_by_coordinates(origin=115.912814,28.702118,destination=115.903209,28.691623)，验证total_distance_meters<=2500。
3) 离附近地铁站距离不超过600米：以餐厅坐标为中心调用maps_around_search(location=115.903209,28.691623,radius=600,keywords=地铁站)，验证至少返回一个地铁站POI（如"青山路口(地铁站)" id=BV10272831）。
4) 现在仍在营业：调用maps_search_detail(B0FFFF5RXS)读取biz_ext.open_time/opentime2=10:00-02:00；结合time字段给出的当前时间，验证当前时间落在营业时间段内（星期几在营业时间范围内，当前具体时间也在营业时间范围内）。
5) 评分>=4.6：调用maps_search_detail(B0FFFF5RXS)，验证biz_ext.rating>=4.6。
6) 朋友从你这里开车到餐厅<=5分钟：调用maps_driving_by_coordinates(origin=115.912814,28.702118,destination=115.903209,28.691623)，验证total_duration_seconds<=300。
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
    maps_bicycling_by_coordinates,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.912814,28.702118",
    search_radius: int = 2000,  # 2km
    keywords: str = "餐厅",
    max_bicycling_distance: int = 2500,  # 2.5km
    subway_search_radius: int = 600,  # 600m
    subway_keywords: str = "地铁站",
    min_rating: float = 4.6,
    max_driving_duration: int = 300,  # 5 minutes = 300 seconds
    current_time: str = "周二 11:26:00"  # 当前时间
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离约束(附近2公里)：调用 maps_around_search，验证目标poi_id在返回pois列表中。
    2) 骑行距离不超过2.5公里：调用 maps_search_detail 取其location；再调用 maps_bicycling_by_coordinates，验证 total_distance_meters<=2500。
    3) 离附近地铁站距离不超过600米：以餐厅坐标为中心调用 maps_around_search，验证至少返回一个地铁站POI。
    4) 现在仍在营业：调用 maps_search_detail 读取 biz_ext.open_time/opentime2；结合time字段给出的当前时间，验证当前时间落在营业时间段内。
    5) 评分>=4.6：调用 maps_search_detail，验证 biz_ext.rating>=4.6。
    6) 朋友从你这里开车到餐厅<=5分钟：调用 maps_driving_by_coordinates，验证 total_duration_seconds<=300。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"115.912814,28.702118"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"餐厅"
        max_bicycling_distance: 最大骑行距离（米），默认2500（2.5公里）
        subway_search_radius: 地铁站搜索半径（米），默认600
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        min_rating: 最低评分，默认4.6
        max_driving_duration: 最大驾车时长（秒），默认300（5分钟）
        current_time: 当前时间，格式为"周X HH:MM:SS"，默认"周二 11:26:00"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（附近2公里）
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

    # 步骤2: 获取目标POI详情
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 骑行距离不超过2.5公里
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取骑行距离")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米，超过{max_bicycling_distance}米（{max_bicycling_distance / 1000}公里）")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米，符合要求（<= {max_bicycling_distance}米，即{max_bicycling_distance / 1000}公里）")

    # 步骤4: 离附近地铁站距离不超过600米
    subway_search_result = maps_around_search(
        location=poi_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 餐厅附近{subway_search_radius}米内未找到地铁站")
        return False

    print(f"✅ 餐厅附近{subway_search_radius}米内找到地铁站: {subway_search_result.pois[0].name} (共{len(subway_search_result.pois)}个)")

    # 步骤5: 验证评分>=4.6
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

    # 步骤6: 验证现在仍在营业
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

    # 提取时间段（例如 "10:00-02:00" 或 "周一至周日 10:00-02:00"）
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

    # 步骤7: 朋友从你这里开车到餐厅<=5分钟
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 715.py 文件...\n")
    result = verify_poi(poi_id="B0FFFF5RXS")
    print(f"\n验证结果: {result}")
