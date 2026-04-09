"""
修改任务指令：你想找一家附近1.5km内的咖啡厅，骑车过去要在5分钟以内。你等会儿要去昌吉站赶车，所以从咖啡厅开车到昌吉站也得在18分钟以内。另外你今天想在店里坐一会儿，咖啡厅现在必须还在营业，并且至少要在23:00之后仍然营业。评分要不低于4.5。你有礼貌但非常坚决和不耐烦，希望尽快解决问题。
# 注意：首个约束已修正为"你想找一家附近1.5km内的咖啡厅"（原表述为"你要找一家附近1.5km内的咖啡厅"）

根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
我将按照四个步骤进行验证：  
  
1) 基础信息与营业时间/评分校验  
- 调用 maps_search_detail("B03E20M4A4") 获取目标POI的 biz_ext.rating 与 biz_ext.opentime2（或 open_time）。  
- 验证评分 rating >= 4.5。  
- 结合给定time字段（当前时间）验证：当前时刻在其营业区间内；且其关门时间晚于 23:00（即至少在23:00之后仍营业）。  
  
2) 附近搜索结果覆盖性校验（距离上限的可验证性）  
- 调用 maps_around_search，参数：location="87.29632,44.01132", radius="1500", keywords="咖啡厅"。  
- 验证 target_poi_id ("B03E20M4A4") 必须出现在该 pois 列表中，从而确认其在"附近1.5km内"。  
  
3) 骑行时长校验  
- 取用户坐标 origin="87.29632,44.01132"。  
- 取目标POI入口坐标 destination=maps_search_detail 返回的 entr_location（若为空则用 location）。  
- 调用 maps_bicycling_by_coordinates(origin, destination)，验证 total_duration_seconds <= 300（5分钟）。  
  
4) 到昌吉站的驾车时长校验  
- 调用 maps_search_detail("B03E20M5X4") 获取昌吉站 entr_location（若为空则用 location）。  
- 调用 maps_driving_by_coordinates(origin=目标POI entr_location(或location), destination=昌吉站 entr_location(或location))，验证 total_duration_seconds <= 1080（18分钟）。
"""

import os
import sys
import re

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
    maps_driving_by_coordinates,
)
from tools.amap_tools import maps_around_search


def parse_business_hours(opentime_str: str) -> tuple:
    """
    解析营业时间字符串，返回(开门时间, 关门时间)的元组
    
    支持格式：
    - "08:00-24:00" -> (8, 0, 24, 0)
    - "09:30-23:30" -> (9, 30, 23, 30)
    
    Args:
        opentime_str: 营业时间字符串，格式如"08:00-24:00"
    
    Returns:
        tuple: (开门小时, 开门分钟, 关门小时, 关门分钟)，如果解析失败返回None
    """
    if not opentime_str:
        return None
    
    # 匹配格式：HH:MM-HH:MM
    pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
    match = re.search(pattern, opentime_str.strip())
    
    if match:
        open_hour = int(match.group(1))
        open_minute = int(match.group(2))
        close_hour = int(match.group(3))
        close_minute = int(match.group(4))
        return (open_hour, open_minute, close_hour, close_minute)
    
    return None


def check_current_time_in_business_hours(current_time: str, biz_ext: dict) -> bool:
    """
    检查当前时间是否在营业时间内
    
    Args:
        current_time: 当前时间，格式如"周二 21:10:00"
        biz_ext: POI的biz_ext字典
    
    Returns:
        bool: True表示当前时间在营业时间内，False表示不在营业时间内或无法确定
    """
    if not biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
    # 尝试读取open_time或opentime2
    opentime_str = None
    if biz_ext.get("opentime2"):
        opentime_str = biz_ext.get("opentime2")
        print(f"📅 找到opentime2: {opentime_str}")
    elif biz_ext.get("open_time"):
        opentime_str = biz_ext.get("open_time")
        print(f"📅 找到open_time: {opentime_str}")
    
    if not opentime_str:
        print(f"❌ 无法找到营业时间信息（open_time/opentime2）")
        return False
    
    # 解析当前时间
    weekday_map = {
        "周一": 0, "周二": 1, "周三": 2, "周四": 3, 
        "周五": 4, "周六": 5, "周日": 6
    }
    
    time_match = re.match(r"周([一二三四五六日])\s+(\d{2}):(\d{2}):(\d{2})", current_time)
    if not time_match:
        print(f"❌ 无法解析当前时间格式: {current_time}")
        return False
    
    weekday_str = time_match.group(1)
    current_hour = int(time_match.group(2))
    current_minute = int(time_match.group(3))
    
    weekday_num = weekday_map.get("周" + weekday_str)
    if weekday_num is None:
        print(f"❌ 无法识别星期: {weekday_str}")
        return False
    
    # 解析营业时间字符串
    # 可能的格式：
    # "09:00-22:00"
    # "周一至周四,周日 07:00-22:00；周五至周六 07:00-22:30"
    
    is_open = False
    
    # 尝试匹配带星期的时间段格式
    pattern_with_weekday = r"([^；]+?)\s+(\d{2}):(\d{2})-(\d{2}):(\d{2})"
    matches = re.findall(pattern_with_weekday, opentime_str)
    
    if matches:
        # 有星期信息的时间段
        for match in matches:
            weekday_range_str = match[0].strip()
            start_hour = int(match[1])
            start_minute = int(match[2])
            end_hour = int(match[3])
            end_minute = int(match[4])
            
            # 检查当前星期是否在这个范围内
            weekday_in_range = False
            
            # 先按逗号分割，处理"周一至周四,周日"这种情况
            weekday_parts = [part.strip() for part in weekday_range_str.split(",")]
            
            for weekday_part in weekday_parts:
                # 处理星期范围，如"周一至周四"、"周五至周六"、"周日"
                if "至" in weekday_part:
                    # 处理范围，如"周一至周四"
                    range_match = re.match(r"周([一二三四五六日])至周([一二三四五六日])", weekday_part)
                    if range_match:
                        start_weekday = weekday_map.get("周" + range_match.group(1))
                        end_weekday = weekday_map.get("周" + range_match.group(2))
                        if start_weekday is not None and end_weekday is not None:
                            if start_weekday <= end_weekday:
                                if start_weekday <= weekday_num <= end_weekday:
                                    weekday_in_range = True
                                    break
                            else:
                                # 跨周的情况，如"周五至周一"
                                if weekday_num >= start_weekday or weekday_num <= end_weekday:
                                    weekday_in_range = True
                                    break
                else:
                    # 处理单个星期，如"周日"
                    single_match = re.match(r"周([一二三四五六日])", weekday_part)
                    if single_match:
                        single_weekday = weekday_map.get("周" + single_match.group(1))
                        if single_weekday == weekday_num:
                            weekday_in_range = True
                            break
            
            if weekday_in_range:
                # 检查时间是否在范围内
                current_time_minutes = current_hour * 60 + current_minute
                start_time_minutes = start_hour * 60 + start_minute
                end_time_minutes = end_hour * 60 + end_minute
                
                if end_time_minutes < start_time_minutes:
                    # 跨天的情况，如22:00-02:00
                    is_open = current_time_minutes >= start_time_minutes or current_time_minutes <= end_time_minutes
                else:
                    is_open = start_time_minutes <= current_time_minutes <= end_time_minutes
                
                if is_open:
                    break
    else:
        # 没有星期信息，直接匹配时间格式 "HH:MM-HH:MM"
        simple_pattern = r"(\d{2}):(\d{2})-(\d{2}):(\d{2})"
        simple_match = re.search(simple_pattern, opentime_str)
        if simple_match:
            start_hour = int(simple_match.group(1))
            start_minute = int(simple_match.group(2))
            end_hour = int(simple_match.group(3))
            end_minute = int(simple_match.group(4))
            
            current_time_minutes = current_hour * 60 + current_minute
            start_time_minutes = start_hour * 60 + start_minute
            end_time_minutes = end_hour * 60 + end_minute
            
            if end_time_minutes < start_time_minutes:
                # 跨天的情况
                is_open = current_time_minutes >= start_time_minutes or current_time_minutes <= end_time_minutes
            else:
                is_open = start_time_minutes <= current_time_minutes <= end_time_minutes
    
    if is_open:
        print(f"✅ 当前时间 {current_time} 在营业时间内")
        return True
    else:
        print(f"❌ 当前时间 {current_time} 不在营业时间内")
        return False


def check_business_hours_after_23(biz_ext: dict) -> bool:
    """
    检查营业时间是否覆盖到23:00之后
    
    Args:
        biz_ext: POI的biz_ext字典
    
    Returns:
        bool: True表示营业时间覆盖到23:00之后，False表示不符合要求或无法确定
    """
    if not biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
    # 尝试读取open_time或opentime2
    opentime_str = None
    if biz_ext.get("opentime2"):
        opentime_str = biz_ext.get("opentime2")
        print(f"📅 找到opentime2: {opentime_str}")
    elif biz_ext.get("open_time"):
        opentime_str = biz_ext.get("open_time")
        print(f"📅 找到open_time: {opentime_str}")
    
    if not opentime_str:
        print(f"❌ 无法找到营业时间信息（open_time/opentime2）")
        return False
    
    # 解析营业时间（可能需要处理多个时间段）
    # 先尝试解析所有时间段
    pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
    matches = re.findall(pattern, opentime_str)
    
    if not matches:
        print(f"❌ 无法解析营业时间格式: {opentime_str}")
        return False
    
    # 检查所有时间段，看是否有任何一个关门时间晚于23:00
    for match in matches:
        open_hour = int(match[0])
        open_minute = int(match[1])
        close_hour = int(match[2])
        close_minute = int(match[3])
        open_minutes = open_hour * 60 + open_minute
        close_minutes = close_hour * 60 + close_minute

        # 跨天：关门在次日凌晨，视为满足“晚于23:00”
        if close_minutes <= open_minutes:
            print(f"✅ 营业时间跨天（{open_hour:02d}:{open_minute:02d}-{close_hour:02d}:{close_minute:02d}），关门在次日，晚于23:00")
            return True

        # 检查关门时间是否晚于23:00
        if close_hour > 23:
            print(f"✅ 关门时间{close_hour:02d}:{close_minute:02d}晚于23:00")
            return True
        elif close_hour == 23 and close_minute > 0:
            print(f"✅ 关门时间{close_hour:02d}:{close_minute:02d}晚于23:00")
            return True
        elif close_hour == 23 and close_minute == 0:
            # 正好23:00，根据需求判断
            print(f"⚠️  关门时间正好23:00")
            # 如果正好23:00，可能不满足"23:00之后"的要求，但通常"营业到23:00"意味着23:00关门
            # 这里严格判断为不满足
            continue
        elif close_hour == 24 or (close_hour == 0 and close_minute == 0):
            # 24:00 或 00:00 表示营业到午夜
            print(f"✅ 关门时间{close_hour:02d}:{close_minute:02d}（营业到午夜）晚于23:00")
            return True
    
    print(f"❌ 所有营业时间段的关门时间都不晚于23:00")
    return False


def verify_poi(
    poi_id: str,
    user_location: str = "87.29632,44.01132",
    station_poi_id: str = "B03E20M5X4",
    current_time: str = "周二 21:10:00",
    search_radius: int = 1500,
    keywords: str = "咖啡厅",
    min_rating: float = 4.5,
    max_bicycling_duration: int = 300,  # 5分钟 = 300秒
    max_driving_duration: int = 1080  # 18分钟 = 1080秒
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 基础信息与营业时间/评分校验：调用 maps_search_detail，获取 biz_ext.rating 与 biz_ext.opentime2（或 open_time），验证评分>=4.5，当前时刻在其营业区间内，且关门时间晚于23:00。
    2) 附近搜索结果覆盖性校验：调用 maps_around_search，验证 target_poi_id 必须出现在该 pois 列表中。
    3) 骑行时长校验：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds <= 300（5分钟）。
    4) 到昌吉站的驾车时长校验：调用 maps_search_detail 获取昌吉站坐标，再调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 1080（18分钟）。
    
    Args:
        poi_id: POI ID，默认"B03E20M4A4"
        user_location: 用户坐标，格式为"经度,纬度"，默认"87.29632,44.01132"
        station_poi_id: 昌吉站POI ID，默认"B03E20M5X4"
        current_time: 当前时间，格式如"周二 21:10:00"，默认"周二 21:10:00"
        search_radius: 搜索半径（米），默认1500（1.5km）
        keywords: 搜索关键词，默认"咖啡厅"
        min_rating: 最小评分，默认4.5
        max_bicycling_duration: 最大骑行时长（秒），默认300（5分钟）
        max_driving_duration: 最大驾车时长（秒），默认1080（18分钟）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 基础信息与营业时间/评分校验
    print(f"【步骤1】验证基础信息与营业时间/评分（评分>={min_rating}，当前时间在营业时间内，关门时间晚于23:00）")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
    # 验证评分
    rating = poi_detail.biz_ext.get("rating")
    if rating is None:
        print(f"❌ POI没有rating信息")
        return False
    
    try:
        rating_value = float(rating)
    except (ValueError, TypeError):
        print(f"❌ 无法解析rating值: {rating}")
        return False
    
    if rating_value < min_rating:
        print(f"❌ POI评分{rating_value}，低于要求的最小评分{min_rating}")
        return False
    print(f"✅ POI评分{rating_value}，满足要求（>={min_rating}）")
    
    # 验证当前时间在营业时间内
    if not check_current_time_in_business_hours(current_time, poi_detail.biz_ext):
        return False
    
    # 验证关门时间晚于23:00
    if not check_business_hours_after_23(poi_detail.biz_ext):
        return False
    
    # 获取目标POI坐标（优先使用entr_location，如果为空则使用location）
    target_poi_location = poi_detail.entr_location if poi_detail.entr_location else poi_detail.location
    if not target_poi_location:
        print(f"❌ POI没有location或entr_location信息")
        return False
    print(f"✅ 获取目标POI坐标: {target_poi_location} ({poi_detail.name})")
    
    # 步骤2: 附近搜索结果覆盖性校验
    print(f"\n【步骤2】验证附近搜索结果覆盖性（{search_radius}米范围内，关键词：{keywords}）")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False
    
    if not around_search_result.pois:
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
    
    # 步骤3: 骑行时长校验
    print(f"\n【步骤3】验证骑行时长（<={max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")
    print("-" * 80)
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=target_poi_location
    )
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
    
    # 步骤4: 到昌吉站的驾车时长校验
    print(f"\n【步骤4】验证到昌吉站的驾车时长（<={max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    print("-" * 80)
    # 获取昌吉站坐标
    station_detail = maps_search_detail(id=station_poi_id)
    if station_detail.error:
        print(f"❌ 获取昌吉站详情失败: {station_detail.error}")
        return False
    
    # 优先使用entr_location，如果为空则使用location
    station_location = station_detail.entr_location if station_detail.entr_location else station_detail.location
    if not station_location:
        print(f"❌ 昌吉站没有location或entr_location信息")
        return False
    print(f"✅ 获取昌吉站坐标: {station_location} ({station_detail.name})")
    
    # 计算驾车时间
    driving_result = maps_driving_by_coordinates(
        origin=target_poi_location,
        destination=station_location
    )
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
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 594.py <poi_id> [user_location] [current_time]")
        print("示例: python 594.py B03E20M4A4")
        print("示例: python 594.py B03E20M4A4 87.29632,44.01132")
        print("示例: python 594.py B03E20M4A4 87.29632,44.01132 '周二 21:10:00'")
        print("未传参，使用示例默认值运行。")
        poi_id = "B03E20M4A4"
        user_location = "87.29632,44.01132"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "87.29632,44.01132"
        current_time = sys.argv[3] if len(sys.argv) > 3 else "周二 21:10:00"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print(f"当前时间: {current_time}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, current_time=current_time)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
