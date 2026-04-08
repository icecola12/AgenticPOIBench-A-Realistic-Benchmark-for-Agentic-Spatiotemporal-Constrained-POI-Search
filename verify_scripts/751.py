"""
输入：B0FFIIKPZ0
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 验证POI基础信息（评分与营业时间）
- 调用 maps_search_detail("B0FFIIKPZ0") 获取biz_ext.rating与biz_ext.open_time/opentime2。
- 验证 rating >= 4.5。
- 结合本题给定time字段（当前时间）与open_time/opentime2，验证该POI在当前时刻仍处于营业状态。

2) 验证“附近2km内的咖啡厅”约束
- 调用 maps_around_search(location="116.363191,39.915637", radius="2000", keywords="咖啡厅") 获取2km内咖啡厅列表。
- 验证返回的pois中包含id == "B0FFIIKPZ0"。

3) 验证到两座地铁站的步行时间约束
- 调用 maps_text_search(keywords="地铁复兴门站", city="北京") 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取其坐标L_fxm。
- 调用 maps_text_search(keywords="地铁阜成门站", city="北京") 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取其坐标L_fcm。
- 调用 maps_search_detail("B0FFIIKPZ0") 取咖啡厅坐标L_poi。
- 调用 maps_walking_by_coordinates(origin=L_poi, destination=L_fxm) 得到步行时长T_fxm，验证 T_fxm <= 20分钟。
- 调用 maps_walking_by_coordinates(origin=L_poi, destination=L_fcm) 得到步行时长T_fcm，验证 T_fcm <= 15分钟。

4) 验证到北京南站的驾车时间约束
- 调用 maps_text_search(keywords="北京南站", city="北京") 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取其坐标L_bns。
- 调用 maps_driving_by_coordinates(origin=L_poi, destination=L_bns) 得到驾车时长T_bns，验证 T_bns <= 15分钟。
"""

import sys
import os
from typing import List, Dict
import re
from datetime import datetime

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
    maps_walking_by_coordinates,
    maps_text_search,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search

def parse_business_hours(business_hours_str: str, current_time_str: str) -> bool:
    """
    解析营业时间字符串，判断当前时间是否在营业时间内

    Args:
        business_hours_str: 营业时间字符串，如 "周一至周五 07:00-22:00；周六至周日 08:00-23:00"
        current_time_str: 当前时间字符串，如 "周二 14:20:00"

    Returns:
        bool: 当前时间是否在营业时间内
    """
    if not business_hours_str or not current_time_str:
        return False

    # 解析当前时间
    time_match = re.match(r"周([一二三四五六日])\s+(\d{1,2}):(\d{2}):(\d{2})", current_time_str)
    if not time_match:
        return False

    weekday_str = time_match.group(1)
    current_hour = int(time_match.group(2))
    current_minute = int(time_match.group(3))

    # 星期映射
    weekday_map = {
        "一": 0, "二": 1, "三": 2, "四": 3,
        "五": 4, "六": 5, "日": 6
    }
    current_weekday = weekday_map.get(weekday_str)
    if current_weekday is None:
        return False

    # 将当前时间转换为当天分钟数
    current_minutes = current_hour * 60 + current_minute

    # 解析营业时间段
    time_ranges = business_hours_str.split("；")

    for time_range in time_ranges:
        time_range = time_range.strip()
        if not time_range:
            continue

        # 匹配格式：周一至周五 07:00-22:00 或 周六 08:00-23:00
        # 或者简单格式：06:30-20:00（表示每天都适用）
        range_match = re.match(r"(.+?)\s+(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", time_range)
        if range_match:
            # 带星期信息的格式
            weekday_range_str = range_match.group(1).strip()
            start_hour = int(range_match.group(2))
            start_minute = int(range_match.group(3))
            end_hour = int(range_match.group(4))
            end_minute = int(range_match.group(5))
        else:
            # 尝试匹配简单格式：06:30-20:00
            simple_match = re.match(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", time_range)
            if not simple_match:
                continue
            # 简单格式，没有星期信息，表示每天都适用
            weekday_range_str = ""  # 空字符串表示适用于所有星期
            start_hour = int(simple_match.group(1))
            start_minute = int(simple_match.group(2))
            end_hour = int(simple_match.group(3))
            end_minute = int(simple_match.group(4))

        # 检查当前星期是否在范围内
        if not is_weekday_in_range(weekday_range_str, current_weekday):
            continue

        # 将营业时间转换为分钟数
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute

        # 处理跨天情况（如 22:00-02:00）
        if end_minutes < start_minutes:
            # 跨天营业时间
            if current_minutes >= start_minutes or current_minutes <= end_minutes:
                return True
        else:
            # 正常营业时间
            if start_minutes <= current_minutes <= end_minutes:
                return True

    return False

def is_weekday_in_range(weekday_range_str: str, current_weekday: int) -> bool:
    """
    检查当前星期是否在指定的星期范围内

    Args:
        weekday_range_str: 星期范围字符串，如 "周一至周五" 或 "周六"，空字符串表示适用于所有星期
        current_weekday: 当前星期（0-6，0表示周一）

    Returns:
        bool: 是否在范围内
    """
    # 如果星期范围为空，表示适用于所有星期
    if not weekday_range_str:
        return True

    # 星期映射
    weekday_map = {
        "一": 0, "二": 1, "三": 2, "四": 3,
        "五": 4, "六": 5, "日": 6
    }

    # 处理单个星期，如 "周六"
    if "至" not in weekday_range_str:
        single_match = re.match(r"周([一二三四五六日])", weekday_range_str)
        if single_match:
            weekday = weekday_map.get(single_match.group(1))
            return weekday == current_weekday
        return False

    # 处理星期范围，如 "周一至周五"
    range_match = re.match(r"周([一二三四五六日])至周([一二三四五六日])", weekday_range_str)
    if not range_match:
        return False

    start_weekday = weekday_map.get(range_match.group(1))
    end_weekday = weekday_map.get(range_match.group(2))

    if start_weekday is None or end_weekday is None:
        return False

    # 处理跨周情况，如 "周五至周一"
    if start_weekday <= end_weekday:
        return start_weekday <= current_weekday <= end_weekday
    else:
        return current_weekday >= start_weekday or current_weekday <= end_weekday

"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(
    target_poi_id: str = "B0FFIIKPZ0",
    user_location: str = "116.363191,39.915637",
    around_search_radius: str = "2000",
    around_search_keywords: str = "咖啡厅",
    min_rating: float = 4.5,
    current_time_str: str = "周二 14:20:00",
    fxm_station_address: str = "地铁复兴门站",
    fxm_station_city: str = "北京",
    max_fxm_walking_seconds: int = 1200,  # 20分钟 = 1200秒
    fcm_station_address: str = "地铁阜成门站",
    fcm_station_city: str = "北京",
    max_fcm_walking_seconds: int = 900,   # 15分钟 = 900秒
    nan_station_address: str = "北京南站",
    nan_station_city: str = "北京",
    max_driving_seconds: int = 900         # 15分钟 = 900秒
) -> bool:
    """
    验证POI ID是否符合给定的验证条件

    验证步骤：
    1) 验证POI基础信息（评分与营业时间）
    2) 验证"附近2km内的咖啡厅"约束
    3) 验证到两座地铁站的步行时间约束
    4) 验证到北京南站的驾车时间约束

    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        around_search_radius: 周边搜索半径
        around_search_keywords: 周边搜索关键词
        min_rating: 最低评分要求
        current_time_str: 当前时间字符串
        fxm_station_address: 复兴门站地址
        fxm_station_city: 复兴门站所在城市
        max_fxm_walking_seconds: 到复兴门站的最大步行时间（秒）
        fcm_station_address: 阜成门站地址
        fcm_station_city: 阜成门站所在城市
        max_fcm_walking_seconds: 到阜成门站的最大步行时间（秒）
        nan_station_address: 北京南站地址
        nan_station_city: 北京南站所在城市
        max_driving_seconds: 到北京南站的最大驾车时间（秒）

    Returns:
        bool: 完全满足所有验证条件返回True，否则返回False
    """
    passed_count = 0
    total_count = 4

    # 实际用于后续计算的POI坐标，从POI详情中获取
    actual_poi_location = None

    # 验证步骤1: 验证POI基础信息（评分与营业时间）
    print("验证步骤1: 验证POI基础信息（评分与营业时间）")
    print(f"调用 maps_search_detail(id=\"{target_poi_id}\")")
    detail_result = maps_search_detail(id=target_poi_id)

    if detail_result.error:
        print(f"POI详情查询失败: {detail_result.error}")
        print("验证步骤1: 未通过")
    else:
        # 验证评分
        rating_passed = False
        if detail_result.biz_ext and isinstance(detail_result.biz_ext, dict):
            rating_value = detail_result.biz_ext.get("rating")
            if rating_value is not None:
                try:
                    rating = float(rating_value)
                    if rating >= min_rating:
                        print(f"验证步骤1-评分: 通过 - POI评分 {rating} >= {min_rating}")
                        rating_passed = True
                    else:
                        print(f"验证步骤1-评分: 未通过 - POI评分 {rating} < {min_rating}")
                except (ValueError, TypeError):
                    print("验证步骤1-评分: 未通过 - 无法解析评分值")

        # 验证营业时间
        business_time_passed = False
        if detail_result.biz_ext and isinstance(detail_result.biz_ext, dict):
            business_hours_str = detail_result.biz_ext.get("open_time") or detail_result.biz_ext.get("opentime2")
            if business_hours_str:
                print(f"营业时间信息: {business_hours_str}")
                print(f"当前时间: {current_time_str}")
                if parse_business_hours(business_hours_str, current_time_str):
                    print("验证步骤1-营业时间: 通过 - 当前时间在营业时间内")
                    business_time_passed = True
                else:
                    print("验证步骤1-营业时间: 未通过 - 当前时间不在营业时间内")
            else:
                print("验证步骤1-营业时间: 未通过 - 无法获取营业时间信息")

        # 更新POI坐标
        if detail_result.location:
            actual_poi_location = detail_result.location
            print(f"获取到POI坐标: {actual_poi_location}")

        # 步骤1需要同时满足评分和营业时间
        if rating_passed and business_time_passed:
            print("验证步骤1: 通过 - 评分和营业时间均满足要求")
            passed_count += 1
        else:
            print("验证步骤1: 未通过 - 评分或营业时间不满足要求")

    # 验证步骤2: 验证"附近2km内的咖啡厅"约束
    print("\n验证步骤2: 验证\"附近2km内的咖啡厅\"约束")
    print(f"调用 maps_around_search(location=\"{user_location}\", radius=\"{around_search_radius}\", keywords=\"{around_search_keywords}\")")
    around_result = maps_around_search(
        location=user_location,
        radius=around_search_radius,
        keywords=around_search_keywords
    )

    if around_result.error:
        print(f"周边搜索失败: {around_result.error}")
        print("验证步骤2: 未通过")
    else:
        poi_found = False
        if around_result.pois:
            for poi in around_result.pois:
                if poi.id == target_poi_id:
                    poi_found = True
                    break

        if poi_found:
            print(f"验证步骤2: 通过 - 在周边搜索结果中找到目标POI ID: {target_poi_id}")
            passed_count += 1
        else:
            print(f"验证步骤2: 未通过 - 在周边搜索结果中未找到目标POI ID: {target_poi_id}")

    # 验证步骤3: 验证到两座地铁站的步行时间约束
    print("\n验证步骤3: 验证到两座地铁站的步行时间约束")
    if not actual_poi_location:
        print("验证步骤3: 未通过 - 无法获取POI坐标，无法计算步行时间")
    else:
        fxm_passed = False
        fcm_passed = False

        # 用 maps_text_search + maps_search_detail 获取复兴门站坐标
        print(f"调用 maps_text_search(keywords=\"{fxm_station_address}\", city=\"{fxm_station_city}\") 获取 poi_id，再 maps_search_detail 获取坐标")
        fxm_text_result = maps_text_search(keywords=fxm_station_address, city=fxm_station_city)
        if fxm_text_result.error:
            print(f"复兴门站文本搜索失败: {fxm_text_result.error}")
        elif not fxm_text_result.pois or len(fxm_text_result.pois) == 0:
            print("未找到复兴门站POI")
        else:
            fxm_poi_id = fxm_text_result.pois[0].id
            fxm_detail = maps_search_detail(id=fxm_poi_id)
            if fxm_detail.error or not fxm_detail.location:
                print(f"复兴门站详情获取失败: {fxm_detail.error or '无location'}")
            else:
                fxm_location = fxm_detail.location
                print(f"获取到复兴门站坐标: {fxm_location}")

                # 计算步行时间
                print(f"调用 maps_walking_by_coordinates(origin=\"{actual_poi_location}\", destination=\"{fxm_location}\")")
                fxm_walking_result = maps_walking_by_coordinates(
                    origin=actual_poi_location,
                    destination=fxm_location
                )

                if fxm_walking_result.error:
                    print(f"复兴门站步行路线规划失败: {fxm_walking_result.error}")
                else:
                    if fxm_walking_result.total_duration_seconds is not None:
                        fxm_duration = fxm_walking_result.total_duration_seconds
                        if fxm_duration <= max_fxm_walking_seconds:
                            print(f"验证步骤3-复兴门站: 通过 - 步行时间 {fxm_duration}秒 <= {max_fxm_walking_seconds}秒")
                            fxm_passed = True
                        else:
                            print(f"验证步骤3-复兴门站: 未通过 - 步行时间 {fxm_duration}秒 > {max_fxm_walking_seconds}秒")

        # 用 maps_text_search + maps_search_detail 获取阜成门站坐标
        print(f"调用 maps_text_search(keywords=\"{fcm_station_address}\", city=\"{fcm_station_city}\") 获取 poi_id，再 maps_search_detail 获取坐标")
        fcm_text_result = maps_text_search(keywords=fcm_station_address, city=fcm_station_city)
        if fcm_text_result.error:
            print(f"阜成门站文本搜索失败: {fcm_text_result.error}")
        elif not fcm_text_result.pois or len(fcm_text_result.pois) == 0:
            print("未找到阜成门站POI")
        else:
            fcm_poi_id = fcm_text_result.pois[0].id
            fcm_detail = maps_search_detail(id=fcm_poi_id)
            if fcm_detail.error or not fcm_detail.location:
                print(f"阜成门站详情获取失败: {fcm_detail.error or '无location'}")
            else:
                fcm_location = fcm_detail.location
                print(f"获取到阜成门站坐标: {fcm_location}")

                # 计算步行时间
                print(f"调用 maps_walking_by_coordinates(origin=\"{actual_poi_location}\", destination=\"{fcm_location}\")")
                fcm_walking_result = maps_walking_by_coordinates(
                    origin=actual_poi_location,
                    destination=fcm_location
                )

                if fcm_walking_result.error:
                    print(f"阜成门站步行路线规划失败: {fcm_walking_result.error}")
                else:
                    if fcm_walking_result.total_duration_seconds is not None:
                        fcm_duration = fcm_walking_result.total_duration_seconds
                        if fcm_duration <= max_fcm_walking_seconds:
                            print(f"验证步骤3-阜成门站: 通过 - 步行时间 {fcm_duration}秒 <= {max_fcm_walking_seconds}秒")
                            fcm_passed = True
                        else:
                            print(f"验证步骤3-阜成门站: 未通过 - 步行时间 {fcm_duration}秒 > {max_fcm_walking_seconds}秒")

        # 步骤3需要同时满足两个地铁站的时间要求
        if fxm_passed and fcm_passed:
            print("验证步骤3: 通过 - 到两座地铁站的步行时间均满足要求")
            passed_count += 1
        else:
            print("验证步骤3: 未通过 - 到地铁站的步行时间不满足要求")

    # 验证步骤4: 验证到北京南站的驾车时间约束
    print("\n验证步骤4: 验证到北京南站的驾车时间约束")
    if not actual_poi_location:
        print("验证步骤4: 未通过 - 无法获取POI坐标，无法规划驾车路线")
    else:
        # 用 maps_text_search + maps_search_detail 获取北京南站坐标
        print(f"调用 maps_text_search(keywords=\"{nan_station_address}\", city=\"{nan_station_city}\") 获取 poi_id，再 maps_search_detail 获取坐标")
        nan_text_result = maps_text_search(keywords=nan_station_address, city=nan_station_city)
        if nan_text_result.error:
            print(f"北京南站文本搜索失败: {nan_text_result.error}")
            print("验证步骤4: 未通过")
        elif not nan_text_result.pois or len(nan_text_result.pois) == 0:
            print("未找到北京南站POI")
            print("验证步骤4: 未通过")
        else:
            nan_poi_id = nan_text_result.pois[0].id
            nan_detail = maps_search_detail(id=nan_poi_id)
            if nan_detail.error or not nan_detail.location:
                print(f"北京南站详情获取失败: {nan_detail.error or '无location'}")
                print("验证步骤4: 未通过")
            else:
                nan_location = nan_detail.location
                print(f"获取到北京南站坐标: {nan_location}")

                # 计算驾车时间
                print(f"调用 maps_driving_by_coordinates(origin=\"{actual_poi_location}\", destination=\"{nan_location}\")")
                driving_result = maps_driving_by_coordinates(
                    origin=actual_poi_location,
                    destination=nan_location
                )

                if driving_result.error:
                    print(f"驾车路线规划失败: {driving_result.error}")
                    print("验证步骤4: 未通过")
                else:
                    if driving_result.total_duration_seconds is not None:
                        driving_duration = driving_result.total_duration_seconds
                        if driving_duration <= max_driving_seconds:
                            print(f"验证步骤4: 通过 - 驾车时间 {driving_duration}秒 <= {max_driving_seconds}秒")
                            passed_count += 1
                        else:
                            print(f"验证步骤4: 未通过 - 驾车时间 {driving_duration}秒 > {max_driving_seconds}秒")
                    else:
                        print("验证步骤4: 未通过 - 无法获取驾车时间")

    # 输出最终结果
    print(f"\n验证完成: 通过 {passed_count}/{total_count} 项验证")
    if passed_count == total_count:
        print("最终验证结果: True (完全满足所有验证条件)")
        return True
    else:
        print("最终验证结果: False (部分满足或不满足验证条件)")
        return False


def main():
    result = verify_poi()
    print(f"\n函数返回值: {result}")


if __name__ == "__main__":
    main()