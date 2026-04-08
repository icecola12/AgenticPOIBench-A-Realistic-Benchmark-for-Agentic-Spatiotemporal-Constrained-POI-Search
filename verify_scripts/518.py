"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
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

"""
根据给定的验证方法验证POI是否符合要求。
输入：B0H015NRX9
输出：True

验证方法：
我将按照四个步骤进行验证：
1) POI基础信息与评分/营业时间：对输入的poi_id调用 maps_search_detail(id)，获取其location与biz_ext信息；验证评分rating>=4.7；并根据biz_ext.open_time/opentime2验证在给定time时刻处于营业时段内。
2) 附近3公里约束：以用户坐标118.870476,42.256555为中心，调用 maps_around_search(location="118.870476,42.256555", radius="3000", keywords="餐厅")
3) 骑行时间约束：用 maps_bicycling_by_coordinates(origin="118.870476,42.256555", destination=POI的location) 得到骑行总时长t_bike；验证 t_bike<=480秒。
4) 到赤峰站步行时间约束：先调用 maps_text_search(keywords="赤峰站", city="赤峰") 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 赤峰站坐标L_station；再用 maps_walking_by_coordinates(origin=POI入口或POI坐标, destination=L_station) 得到步行总时长t_walk_station；验证 t_walk_station<=1200秒。
"""
def verify_poi(
    target_poi_id: str = "B0H015NRX9",
    user_location: str = "118.870476,42.256555",
    search_radius: str = "3000",
    search_keywords: str = "餐厅",
    min_rating: float = 4.7,
    max_bicycling_seconds: int = 480,
    station_address: str = "赤峰站",
    station_city: str = "赤峰",
    max_walking_seconds: int = 1200,
    current_time: str = "周一 18:40:00"
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID，默认值为 "B0H015NRX9"
        user_location: 用户位置坐标，格式为"经度,纬度"，默认值为 "118.870476,42.256555"
        search_radius: 搜索半径（米），默认值为 "3000"
        search_keywords: 搜索关键词，默认值为 "餐厅"
        min_rating: 最小评分，默认值为 4.7
        max_bicycling_seconds: 最大骑行时间（秒），默认值为 480（8分钟）
        station_address: 车站地址，默认值为 "赤峰站"
        station_city: 车站所在城市，默认值为 "赤峰"
        max_walking_seconds: 最大步行时间（秒），默认值为 1200（20分钟）
        current_time: 当前时间，格式为"周X HH:MM:SS"，默认值为 "周一 18:40:00"
    
    Returns:
        bool: 所有验证条件都满足返回True，否则返回False
    """
    all_passed = True
    
    # 步骤1：POI基础信息与评分/营业时间
    print(f"步骤1：验证POI基础信息与评分/营业时间")
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
    
    # 步骤2：附近3公里约束
    print(f"步骤2：验证目标是否在附近{int(search_radius)/1000}公里内")
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
    
    # 步骤3：骑行时间约束
    print(f"步骤3：验证骑行时间不超过{max_bicycling_seconds//60}分钟")
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
    
    t_bike = bicycling_result.total_duration_seconds
    
    if t_bike <= max_bicycling_seconds:
        print(f"  验证通过：骑行时间 {t_bike//60}分{t_bike%60}秒 <= {max_bicycling_seconds//60}分钟")
    else:
        print(f"  验证失败：骑行时间 {t_bike//60}分{t_bike%60}秒 > {max_bicycling_seconds//60}分钟")
        all_passed = False
    
    # 步骤4：到赤峰站步行时间约束
    print(f"步骤4：验证到车站步行时间不超过{max_walking_seconds//60}分钟")
    
    # 获取赤峰站坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
    text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if text_search_result.error:
        print(f"  验证失败：获取车站坐标出错 - {text_search_result.error}")
        return False
    
    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"  验证失败：未找到车站坐标")
        return False
    
    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error:
        print(f"❌ 获取坐标失败: {detail_result.error}")
        return False
    if not detail_result.location:
        print("❌ 未获取到坐标")
        return False
    
    L_station = detail_result.location
    # 使用POI入口坐标或POI坐标
    origin_location = poi_detail.entr_location if poi_detail.entr_location else poi_location
    
    walking_result = maps_walking_by_coordinates(
        origin=origin_location,
        destination=L_station
    )
    
    if walking_result.error:
        print(f"  验证失败：步行路线规划出错 - {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"  验证失败：无法获取步行时长")
        return False
    
    t_walk_station = walking_result.total_duration_seconds
    
    if t_walk_station <= max_walking_seconds:
        print(f"  验证通过：步行时间 {t_walk_station//60}分{t_walk_station%60}秒 <= {max_walking_seconds//60}分钟")
    else:
        print(f"  验证失败：步行时间 {t_walk_station//60}分{t_walk_station%60}秒 > {max_walking_seconds//60}分钟")
        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '不通过'}")
    return result


if __name__ == "__main__":
    main()
