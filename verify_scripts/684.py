"""
修改任务指令：你现在要在附近2公里内找一家咖啡厅。你准备从这里步行过去，所以步行时间得控制在15分钟内。另外你约了客户在“河南省体育场”那边见面，对方打车过来，你希望他从河南省体育场开车到咖啡厅的时间不要超过8分钟。为了方便你们见完就去坐地铁，这家咖啡厅走到“海滩寺地铁站”的时间也必须在15分钟以内。最后，你到店的时候必须还在营业（不要是已经打烊的）。你健谈外向，乐观，乐于合作。
输入：B0LRJUH985
输出：True

验证方法：
1) 用 maps_search_detail(B0LRJUH985) 获取目标POI的 location 与 biz_ext.opentime2/open_time 信息。
2) 距离约束：用 maps_around_search，以用户坐标 113.65288,34.768385 为中心、radius=2000、keywords=咖啡厅 搜索，验证返回pois中包含该 target_poi_id。
3) 用户步行时长约束：用 maps_walking_by_coordinates(origin=113.65288,34.768385, destination=POI.location) 得到 total_duration_seconds，验证 <= 900 秒（15分钟）。
4) 客户驾车时长约束：用 maps_text_search(keywords=河南省体育场, city=郑州) 获取 poi_id，再调用 maps_search_detail(id=poi_id) 得到体育场坐标；再用 maps_driving_by_coordinates(origin=体育场坐标, destination=POI.location) 得到 total_duration_seconds，验证 <= 480 秒（8分钟）。
5) 到地铁站步行时长约束：用 maps_text_search(keywords=海滩寺地铁站, city=郑州) 获取 poi_id，再调用 maps_search_detail(id=poi_id) 得到地铁站坐标；再用 maps_walking_by_coordinates(origin=POI.location, destination=地铁站坐标) 得到 total_duration_seconds，验证 <= 900 秒（15分钟）。
6) 营业时间约束：读取 maps_search_detail 返回的 biz_ext.opentime2/open_time（例如“周一至周日 06:30-24:00”），结合本样例给定 time 字段，验证在该时刻POI仍处于营业时段内。
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
    maps_driving_by_coordinates,
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
    target_poi_id: str = 'B0LRJUH985',
    user_location: str = '113.65288,34.768385',
    radius: str = '2000',
    keywords: str = '咖啡厅',
    max_walking_seconds: int = 900,
    stadium_address: str = '河南省体育场',
    stadium_city: str = '郑州',
    max_driving_seconds: int = 480,
    subway_address: str = '海滩寺地铁站',
    subway_city: str = '郑州',
    max_walking_to_subway_seconds: int = 900,
    current_time: str = '周二 10:05:48'
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标，格式为"经度,纬度"
        radius: 搜索半径（米），字符串格式
        keywords: 搜索关键词
        max_walking_seconds: 最大步行时长（秒）
        stadium_address: 体育场地址
        stadium_city: 体育场所在城市
        max_driving_seconds: 最大驾车时长（秒）
        subway_address: 地铁站地址
        subway_city: 地铁站所在城市
        max_walking_to_subway_seconds: 到地铁站最大步行时长（秒）
        current_time: 当前时间，格式为"周二 10:05:48"
    
    Returns:
        bool: True表示所有验证通过，False表示部分或全部验证失败
    """
    all_passed = True
    
    # 验证步骤1: 获取POI详情，获取location和biz_ext信息
    print("验证步骤1: 获取POI详情并获取location和biz_ext信息")
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"验证步骤1失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print("验证步骤1失败: 未获取到POI坐标")
        return False
    
    target_poi_location = poi_detail.location
    print(f"验证步骤1通过: 成功获取POI坐标 {target_poi_location}")
    
    # 验证步骤2: 距离约束 - 验证POI在用户位置2公里内且为咖啡厅
    print(f"验证步骤2: 验证POI在用户位置{radius}米内且为{keywords}")
    around_search_result = maps_around_search(
        location=user_location,
        radius=radius,
        keywords=keywords
    )
    
    if around_search_result.error:
        print(f"验证步骤2失败: {around_search_result.error}")
        all_passed = False
    elif not around_search_result.pois:
        print("验证步骤2失败: 未找到符合条件的POI")
        all_passed = False
    else:
        # 检查返回的POI列表中是否包含目标POI ID
        found = False
        for poi in around_search_result.pois:
            if poi.id == target_poi_id:
                found = True
                break
        
        if found:
            print(f"验证步骤2通过: 在{radius}米内找到目标{keywords}POI")
        else:
            print(f"验证步骤2失败: 在{radius}米内未找到目标{keywords}POI")
            all_passed = False
    
    # 验证步骤3: 用户步行时长约束
    print(f"验证步骤3: 验证用户步行时长 <= {max_walking_seconds}秒（{max_walking_seconds // 60}分钟）")
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=target_poi_location
    )
    
    if walking_result.error:
        print(f"验证步骤3失败: {walking_result.error}")
        all_passed = False
    elif walking_result.total_duration_seconds is None:
        print("验证步骤3失败: 未获取到步行时长")
        all_passed = False
    else:
        walking_seconds = walking_result.total_duration_seconds
        if walking_seconds <= max_walking_seconds:
            print(f"验证步骤3通过: 步行时长 {walking_seconds}秒 <= {max_walking_seconds}秒（{max_walking_seconds // 60}分钟）")
        else:
            print(f"验证步骤3失败: 步行时长 {walking_seconds}秒 > {max_walking_seconds}秒（{max_walking_seconds // 60}分钟）")
            all_passed = False
    
    # 验证步骤4: 客户驾车时长约束（用 maps_text_search + maps_search_detail 获取体育场坐标）
    print(f"验证步骤4: 验证客户驾车时长 <= {max_driving_seconds}秒（{max_driving_seconds // 60}分钟）")
    text_search_result = maps_text_search(keywords=stadium_address, city=stadium_city)
    if text_search_result.error:
        print(f"验证步骤4失败: 无法获取{stadium_address}坐标 - {text_search_result.error}")
        all_passed = False
    elif not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"验证步骤4失败: 未找到{stadium_address}的坐标信息")
        all_passed = False
    else:
        first_poi_id = text_search_result.pois[0].id
        detail_result = maps_search_detail(id=first_poi_id)
        if detail_result.error or not detail_result.location:
            print(f"验证步骤4失败: 无法获取{stadium_address}坐标 - {detail_result.error or '无location'}")
            all_passed = False
        else:
            stadium_location = detail_result.location
            print(f"验证步骤4: 获取到{stadium_address}坐标: {stadium_location}")

            driving_result = maps_driving_by_coordinates(
                origin=stadium_location,
                destination=target_poi_location
            )

            if driving_result.error:
                print(f"验证步骤4失败: {driving_result.error}")
                all_passed = False
            elif driving_result.total_duration_seconds is None:
                print("验证步骤4失败: 未获取到驾车时长")
                all_passed = False
            else:
                driving_seconds = driving_result.total_duration_seconds
                if driving_seconds <= max_driving_seconds:
                    print(f"验证步骤4通过: 驾车时长 {driving_seconds}秒 <= {max_driving_seconds}秒（{max_driving_seconds // 60}分钟）")
                else:
                    print(f"验证步骤4失败: 驾车时长 {driving_seconds}秒 > {max_driving_seconds}秒（{max_driving_seconds // 60}分钟）")
                    all_passed = False
    
    # 验证步骤5: 用 maps_text_search + maps_search_detail 获取地铁站坐标，到地铁站步行时长约束
    print(f"验证步骤5: 验证到地铁站步行时长 <= {max_walking_to_subway_seconds}秒（{max_walking_to_subway_seconds // 60}分钟）")
    text_search_result = maps_text_search(keywords=subway_address, city=subway_city)
    if text_search_result.error:
        print(f"验证步骤5失败: 无法获取{subway_address}坐标 - {text_search_result.error}")
        all_passed = False
    elif not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"验证步骤5失败: 未找到{subway_address}的坐标信息")
        all_passed = False
    else:
        first_poi_id = text_search_result.pois[0].id
        detail_result = maps_search_detail(id=first_poi_id)
        if detail_result.error or not detail_result.location:
            print(f"验证步骤5失败: 无法获取{subway_address}坐标 - {detail_result.error or '无location'}")
            all_passed = False
        else:
            subway_location = detail_result.location
            print(f"验证步骤5: 获取到{subway_address}坐标: {subway_location}")

            walking_to_subway_result = maps_walking_by_coordinates(
                origin=target_poi_location,
                destination=subway_location
            )

            if walking_to_subway_result.error:
                print(f"验证步骤5失败: {walking_to_subway_result.error}")
                all_passed = False
            elif walking_to_subway_result.total_duration_seconds is None:
                print("验证步骤5失败: 未获取到步行时长")
                all_passed = False
            else:
                walking_to_subway_seconds = walking_to_subway_result.total_duration_seconds
                if walking_to_subway_seconds <= max_walking_to_subway_seconds:
                    print(f"验证步骤5通过: 步行时长 {walking_to_subway_seconds}秒 <= {max_walking_to_subway_seconds}秒（{max_walking_to_subway_seconds // 60}分钟）")
                else:
                    print(f"验证步骤5失败: 步行时长 {walking_to_subway_seconds}秒 > {max_walking_to_subway_seconds}秒（{max_walking_to_subway_seconds // 60}分钟）")
                    all_passed = False
    
    # 验证步骤6: 营业时间约束
    print(f"验证步骤6: 验证营业时间（当前时间: {current_time}）")
    
    if not poi_detail.biz_ext:
        print("验证步骤6失败: 无法获取POI扩展信息（biz_ext）")
        all_passed = False
    else:
        open_time = poi_detail.biz_ext.get("open_time")
        opentime2 = poi_detail.biz_ext.get("opentime2")
        
        # 优先使用opentime2，如果没有则使用open_time
        business_hours_str = opentime2 if opentime2 else open_time
        
        if not business_hours_str:
            print("验证步骤6失败: biz_ext中未找到open_time或opentime2字段")
            all_passed = False
        else:
            print(f"验证步骤6: 营业时间信息: {business_hours_str}")
            print(f"验证步骤6: 当前时间: {current_time}")
            
            # 解析当前时间
            weekday_map = {
                "周一": 0, "周二": 1, "周三": 2, "周四": 3, 
                "周五": 4, "周六": 5, "周日": 6
            }
            
            time_match = re.match(r"周([一二三四五六日])\s+(\d{2}):(\d{2}):(\d{2})", current_time)
            if not time_match:
                print(f"验证步骤6失败: 无法解析当前时间格式: {current_time}")
                all_passed = False
            else:
                weekday_str = time_match.group(1)
                current_hour = int(time_match.group(2))
                current_minute = int(time_match.group(3))
                current_second = int(time_match.group(4))
                
                weekday_num = weekday_map.get("周" + weekday_str)
                if weekday_num is None:
                    print(f"验证步骤6失败: 无法识别星期: {weekday_str}")
                    all_passed = False
                else:
                    # 解析营业时间字符串
                    is_open = False
                    
                    # 尝试匹配带星期的时间段格式
                    # 例如: "周一至周四,周日 07:00-22:00；周五至周六 07:00-22:30"
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
                        print(f"验证步骤6通过: 当前时间 {current_time} 在营业时间内")
                    else:
                        print(f"验证步骤6失败: 当前时间 {current_time} 不在营业时间内")
                        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")
    return result  


if __name__ == "__main__":
    main()
