"""
输入：B0L2FL1HHR
输出：True

验证方法：
1) 距离约束(附近2km)：调用 maps_around_search(location="117.290405,31.879452", radius="2000", keywords="餐厅")，验证返回pois中包含目标poi_id=B0L2FL1HHR。
2) 评分约束(≥4.3)与营业时间约束(当前仍营业)：调用 maps_search_detail(id="B0L2FL1HHR")，验证 biz_ext.rating >= 4.3，且 biz_ext.open_time/opentime2 显示当前时间仍在营业。
3) 离合肥火车站直线距离≤2200米：调用 maps_text_search(keywords="合肥火车站", city="合肥", citylimit="true") 获取 合肥站poi_id=B022700CD7；再调用 maps_search_detail(id="B022700CD7") 得到其location；最后调用 maps_distance(origins="目标POI.location", destination="合肥站.location")，验证 distance_meters <= 2200。
4) 步行时间≤25分钟：调用 maps_walking_by_coordinates(origin="117.290405,31.879452", destination="目标POI.location")，验证 total_duration_seconds <= 1500。
5) 骑行时间≤10分钟：调用 maps_bicycling_by_coordinates(origin="117.290405,31.879452", destination="目标POI.location")，验证 total_duration_seconds <= 600。
"""
import sys
import os
import re
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

def verify_poi(
    target_poi_id: str = "B0L2FL1HHR",
    user_location: str = "117.290405,31.879452",
    search_radius: str = "2000",
    search_keywords: str = "餐厅",
    min_rating: float = 4.3,
    current_time: str = "周二 14:30:00",
    station_keywords: str = "合肥火车站",
    station_city: str = "合肥",
    max_distance_meters: int = 2200,
    max_walking_seconds: int = 1500,
    max_bicycling_seconds: int = 600
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID，默认值为 "B0L2FL1HHR"
        user_location: 用户位置坐标，格式为"经度,纬度"，默认值为 "117.290405,31.879452"
        search_radius: 搜索半径（米），默认值为 "2000"
        search_keywords: 搜索关键词，默认值为 "餐厅"
        min_rating: 最小评分，默认值为 4.3
        current_time: 当前时间，格式为"周X HH:MM:SS"，默认值为 "周二 14:30:00"
        station_keywords: 车站搜索关键词，默认值为 "合肥火车站"
        station_city: 车站所在城市，默认值为 "合肥"
        max_distance_meters: 最大直线距离（米），默认值为 2200
        max_walking_seconds: 最大步行时间（秒），默认值为 1500（25分钟）
        max_bicycling_seconds: 最大骑行时间（秒），默认值为 600（10分钟）
    
    Returns:
        bool: 所有验证条件都满足返回True，否则返回False
    """
    all_passed = True
    
    # 步骤1：距离约束(附近2km)
    print(f"步骤1：验证目标是否在附近{int(search_radius)/1000}公里内")
    around_result = maps_around_search(
        location=user_location,
        radius=search_radius,
        keywords=search_keywords
    )
    
    if around_result.error:
        print(f"  验证失败：周边搜索出错 - {around_result.error}")
        return False
    
    if not around_result.pois:
        print(f"  验证失败：未找到任何POI")
        return False
    
    # 检查返回的pois列表中是否包含target_poi_id
    poi_ids = [poi.id for poi in around_result.pois]
    if target_poi_id in poi_ids:
        print(f"  验证通过：POI {target_poi_id} 在附近{int(search_radius)/1000}公里内")
    else:
        print(f"  验证失败：POI {target_poi_id} 不在附近{int(search_radius)/1000}公里内")
        all_passed = False
    
    # 步骤2：评分约束(≥4.3)与营业时间约束(当前仍营业)
    print(f"步骤2：验证评分不低于{min_rating}且当前时间仍在营业")
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"  验证失败：获取POI详情出错 - {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"  验证失败：无法获取POI坐标")
        return False
    
    poi_location = poi_detail.location
    
    # 验证评分
    rating_passed = False
    if not poi_detail.biz_ext:
        print(f"  验证失败：无法获取POI扩展信息（biz_ext）")
        all_passed = False
    else:
        rating = poi_detail.biz_ext.get("rating")
        if rating is None:
            print(f"  验证失败：无法获取评分信息")
            all_passed = False
        else:
            try:
                rating_value = float(rating)
                if rating_value >= min_rating:
                    print(f"  验证通过：评分 {rating_value} >= {min_rating}")
                    rating_passed = True
                else:
                    print(f"  验证失败：评分 {rating_value} < {min_rating}")
                    all_passed = False
            except (ValueError, TypeError):
                print(f"  验证失败：评分格式错误 - {rating}")
                all_passed = False
    
    # 验证营业时间
    open_time_passed = False
    if poi_detail.biz_ext:
        open_time = poi_detail.biz_ext.get("open_time")
        opentime2 = poi_detail.biz_ext.get("opentime2")
        
        # 优先使用opentime2，如果没有则使用open_time
        business_hours_str = opentime2 if opentime2 else open_time
        
        if not business_hours_str:
            print(f"  验证失败：biz_ext中未找到open_time或opentime2字段")
            all_passed = False
        else:
            print(f"  营业时间信息: {business_hours_str}")
            print(f"  当前时间: {current_time}")
            
            # 解析当前时间
            weekday_map = {
                "周一": 0, "周二": 1, "周三": 2, "周四": 3, 
                "周五": 4, "周六": 5, "周日": 6
            }
            
            time_match = re.match(r"周([一二三四五六日])\s+(\d{2}):(\d{2}):(\d{2})", current_time)
            if not time_match:
                print(f"  验证失败：无法解析当前时间格式: {current_time}")
                all_passed = False
            else:
                weekday_str = time_match.group(1)
                current_hour = int(time_match.group(2))
                current_minute = int(time_match.group(3))
                current_second = int(time_match.group(4))
                
                weekday_num = weekday_map.get("周" + weekday_str)
                if weekday_num is None:
                    print(f"  验证失败：无法识别星期: {weekday_str}")
                    all_passed = False
                else:
                    # 解析营业时间字符串
                    is_open = False
                    
                    # 尝试匹配带星期的时间段格式
                    pattern_with_weekday = r"([^；]+?)\s+(\d{2}):(\d{2})-(\d{2}):(\d{2})"
                    matches = re.findall(pattern_with_weekday, business_hours_str)
                    
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
                        simple_match = re.search(simple_pattern, business_hours_str)
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
                        print(f"  验证通过：当前时间 {current_time} 在营业时间内")
                        open_time_passed = True
                    else:
                        print(f"  验证失败：当前时间 {current_time} 不在营业时间内")
                        all_passed = False
    
    if not (rating_passed and open_time_passed):
        all_passed = False
    
    # 步骤3：离合肥火车站直线距离≤2200米
    print(f"步骤3：验证到车站直线距离不超过{max_distance_meters/1000}公里")
    
    # 调用 maps_text_search 获取合肥站poi_id
    station_search_result = maps_text_search(
        keywords=station_keywords,
        city=station_city,
        citylimit="true"
    )
    
    if station_search_result.error:
        print(f"  验证失败：搜索车站出错 - {station_search_result.error}")
        return False
    
    if not station_search_result.pois or len(station_search_result.pois) == 0:
        print(f"  验证失败：未找到车站")
        return False
    
    # 根据验证步骤，期望找到poi_id=B022700CD7，但实际可能不同，使用第一个结果
    station_poi_id = station_search_result.pois[0].id
    print(f"  找到车站POI ID: {station_poi_id}")
    
    # 获取车站坐标
    station_detail = maps_search_detail(id=station_poi_id)
    
    if station_detail.error:
        print(f"  验证失败：获取车站详情出错 - {station_detail.error}")
        return False
    
    if not station_detail.location:
        print(f"  验证失败：无法获取车站坐标")
        return False
    
    station_location = station_detail.location
    
    # 计算直线距离
    distance_result = maps_distance(
        origins=poi_location,
        destination=station_location
    )
    
    if distance_result.error:
        print(f"  验证失败：距离计算出错 - {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"  验证失败：无法获取距离信息")
        return False
    
    distance_meters = distance_result.results[0].distance_meters
    
    if distance_meters <= max_distance_meters:
        print(f"  验证通过：直线距离 {distance_meters/1000:.2f}公里 <= {max_distance_meters/1000}公里")
    else:
        print(f"  验证失败：直线距离 {distance_meters/1000:.2f}公里 > {max_distance_meters/1000}公里")
        all_passed = False
    
    # 步骤4：步行时间≤25分钟
    print(f"步骤4：验证步行时间不超过{max_walking_seconds//60}分钟")
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=poi_location
    )
    
    if walking_result.error:
        print(f"  验证失败：步行路线规划出错 - {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"  验证失败：无法获取步行时长")
        return False
    
    t_walk_seconds = walking_result.total_duration_seconds
    
    if t_walk_seconds <= max_walking_seconds:
        print(f"  验证通过：步行时间 {t_walk_seconds//60}分{t_walk_seconds%60}秒 <= {max_walking_seconds//60}分钟")
    else:
        print(f"  验证失败：步行时间 {t_walk_seconds//60}分{t_walk_seconds%60}秒 > {max_walking_seconds//60}分钟")
        all_passed = False
    
    # 步骤5：骑行时间≤10分钟
    print(f"步骤5：验证骑行时间不超过{max_bicycling_seconds//60}分钟")
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=poi_location
    )
    
    if bicycling_result.error:
        print(f"  验证失败：骑行路线规划出错 - {bicycling_result.error}")
        return False
    
    if bicycling_result.total_duration_seconds is None:
        print(f"  验证失败：无法获取骑行时长")
        return False
    
    t_bike_seconds = bicycling_result.total_duration_seconds
    
    if t_bike_seconds <= max_bicycling_seconds:
        print(f"  验证通过：骑行时间 {t_bike_seconds//60}分{t_bike_seconds%60}秒 <= {max_bicycling_seconds//60}分钟")
    else:
        print(f"  验证失败：骑行时间 {t_bike_seconds//60}分{t_bike_seconds%60}秒 > {max_bicycling_seconds//60}分钟")
        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '不通过'}")
    return result


if __name__ == "__main__":
    main()
