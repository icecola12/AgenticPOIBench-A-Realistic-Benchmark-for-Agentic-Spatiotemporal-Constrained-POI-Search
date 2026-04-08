"""
输入：B0JBR5SCGN
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
步骤1：验证候选POI基础信息（营业与评分）
- 调用 maps_search_detail("B0JBR5SCGN") 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 biz_ext.open_time/opentime2 与 biz_ext.rating。
- 以给定 time 字段为准，验证当前时刻处于其营业时段内（例如 15:00-02:00 表示跨天营业）。
- 验证评分 rating >= 4.2。

步骤2：验证“附近2公里内的餐厅”与“步行<=25分钟”
- 调用 maps_around_search，以用户坐标(118.866563,42.259432)为中心，radius=2000，keywords="餐厅"。
- 验证返回 pois 数量 > 8（用于保证任务有足够候选，避免退化）。
- 验证 POI_ID=B0JBR5SCGN 在返回列表中。
- 从步骤1的 location 取该餐厅坐标，调用 maps_walking_by_coordinates(origin=用户坐标, destination=餐厅坐标)，验证 total_duration_seconds <= 1500（25分钟）。

步骤3：验证“300米范围内有药店”
- 调用 maps_around_search(location=餐厅坐标, radius=300, keywords="药店")。
- 验证 pois 列表非空且数量>=1，即满足300米内存在药店。

步骤4：验证“开车到赤峰站<=6分钟”
- 调用 maps_text_search(keywords="赤峰站", city="赤峰市") 取 poi_id，再 maps_search_detail(id=poi_id) 获取赤峰站坐标。
- 调用 maps_driving_by_coordinates(origin=餐厅坐标, destination=赤峰站坐标)，验证 total_duration_seconds <= 360（6分钟）。
- 调用 maps_driving_by_coordinates(origin=餐厅坐标, destination=赤峰站坐标)，验证 total_duration_seconds <= 360（6 分钟）。
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
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(
    target_poi_id: str = 'B0JBR5SCGN',
    user_location: str = '118.866563,42.259432',
    current_time: str = '周二 20:30:00',
    min_rating: float = 4.2,
    radius: str = '2000',
    keywords: str = '餐厅',
    min_pois_count: int = 8,
    max_walking_seconds: int = 1500,
    pharmacy_radius: str = '300',
    pharmacy_keywords: str = '药店',
    station_address: str = '赤峰站',
    station_city: str = '赤峰市',
    max_driving_seconds: int = 360
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标，格式为"经度,纬度"
        current_time: 当前时间，格式为"周二 20:30:00"
        min_rating: 最低评分要求
        radius: 搜索半径（米），字符串格式
        keywords: 搜索关键词
        min_pois_count: 最小POI数量要求（用于保证任务有足够候选）
        max_walking_seconds: 最大步行时长（秒）
        pharmacy_radius: 药店搜索半径（米），字符串格式
        pharmacy_keywords: 药店搜索关键词
        station_address: 车站地址
        station_city: 车站所在城市
        max_driving_seconds: 最大驾车时长（秒）
    
    Returns:
        bool: True表示所有验证通过，False表示部分或全部验证失败
    """
    all_passed = True
    
    # 验证步骤1: 验证候选POI基础信息（营业与评分）
    print("验证步骤1: 验证候选POI基础信息（营业与评分）")
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"验证步骤1失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print("验证步骤1失败: 未获取到POI坐标")
        return False
    
    target_poi_location = poi_detail.location
    print(f"验证步骤1: 成功获取POI坐标 {target_poi_location}")
    
    # 验证评分
    rating = None
    if poi_detail.biz_ext and isinstance(poi_detail.biz_ext, dict):
        rating_str = poi_detail.biz_ext.get('rating')
        if rating_str:
            try:
                rating = float(rating_str)
            except (ValueError, TypeError):
                pass
    
    if rating is None:
        print("验证步骤1失败: 未获取到POI评分")
        all_passed = False
    elif rating >= min_rating:
        print(f"验证步骤1通过: 评分 {rating} >= {min_rating}")
    else:
        print(f"验证步骤1失败: 评分 {rating} < {min_rating}")
        all_passed = False
    
    # 验证营业时间
    if not poi_detail.biz_ext:
        print("验证步骤1失败: 无法获取POI扩展信息（biz_ext）")
        all_passed = False
    else:
        open_time = poi_detail.biz_ext.get("open_time")
        opentime2 = poi_detail.biz_ext.get("opentime2")
        
        # 优先使用opentime2，如果没有则使用open_time
        business_hours_str = opentime2 if opentime2 else open_time
        
        if not business_hours_str:
            print("验证步骤1失败: biz_ext中未找到open_time或opentime2字段")
            all_passed = False
        else:
            print(f"验证步骤1: 营业时间信息: {business_hours_str}")
            print(f"验证步骤1: 当前时间: {current_time}")
            
            # 解析当前时间
            weekday_map = {
                "周一": 0, "周二": 1, "周三": 2, "周四": 3, 
                "周五": 4, "周六": 5, "周日": 6
            }
            
            time_match = re.match(r"周([一二三四五六日])\s+(\d{2}):(\d{2}):(\d{2})", current_time)
            if not time_match:
                print(f"验证步骤1失败: 无法解析当前时间格式: {current_time}")
                all_passed = False
            else:
                weekday_str = time_match.group(1)
                current_hour = int(time_match.group(2))
                current_minute = int(time_match.group(3))
                current_second = int(time_match.group(4))
                
                weekday_num = weekday_map.get("周" + weekday_str)
                if weekday_num is None:
                    print(f"验证步骤1失败: 无法识别星期: {weekday_str}")
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
                        print(f"验证步骤1通过: 当前时间 {current_time} 在营业时间内")
                    else:
                        print(f"验证步骤1失败: 当前时间 {current_time} 不在营业时间内")
                        all_passed = False
    
    # 验证步骤2: 验证"附近2公里内的餐厅"与"步行<=25分钟"
    print(f"验证步骤2: 验证附近{radius}米内的{keywords}与步行<={max_walking_seconds}秒（{max_walking_seconds // 60}分钟）")
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
        pois_count = len(around_search_result.pois)
        if pois_count > min_pois_count:
            print(f"验证步骤2通过: 返回pois数量 {pois_count} > {min_pois_count}")
        else:
            print(f"验证步骤2失败: 返回pois数量 {pois_count} <= {min_pois_count}")
            all_passed = False
        
        # 检查返回的POI列表中是否包含目标POI ID
        found = False
        for poi in around_search_result.pois:
            if poi.id == target_poi_id:
                found = True
                break
        
        if found:
            print(f"验证步骤2通过: POI_ID={target_poi_id} 在返回列表中")
        else:
            print(f"验证步骤2失败: POI_ID={target_poi_id} 不在返回列表中")
            all_passed = False
    
    # 验证步行时长
    print(f"验证步骤2: 验证步行时长 <= {max_walking_seconds}秒（{max_walking_seconds // 60}分钟）")
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=target_poi_location
    )
    
    if walking_result.error:
        print(f"验证步骤2失败: {walking_result.error}")
        all_passed = False
    elif walking_result.total_duration_seconds is None:
        print("验证步骤2失败: 未获取到步行时长")
        all_passed = False
    else:
        walking_seconds = walking_result.total_duration_seconds
        if walking_seconds <= max_walking_seconds:
            print(f"验证步骤2通过: 步行时长 {walking_seconds}秒 <= {max_walking_seconds}秒（{max_walking_seconds // 60}分钟）")
        else:
            print(f"验证步骤2失败: 步行时长 {walking_seconds}秒 > {max_walking_seconds}秒（{max_walking_seconds // 60}分钟）")
            all_passed = False
    
    # 验证步骤3: 验证"300米范围内有药店"
    print(f"验证步骤3: 验证{pharmacy_radius}米范围内有{pharmacy_keywords}")
    pharmacy_result = maps_around_search(
        location=target_poi_location,
        radius=pharmacy_radius,
        keywords=pharmacy_keywords
    )
    
    if pharmacy_result.error:
        print(f"验证步骤3失败: {pharmacy_result.error}")
        all_passed = False
    elif not pharmacy_result.pois or len(pharmacy_result.pois) == 0:
        print(f"验证步骤3失败: POI附近{pharmacy_radius}米内未找到{pharmacy_keywords}")
        all_passed = False
    else:
        pharmacy_count = len(pharmacy_result.pois)
        print(f"验证步骤3通过: POI附近{pharmacy_radius}米内找到{pharmacy_count}个{pharmacy_keywords}")
    
    # 验证步骤4: 验证"开车到赤峰站<=6分钟"（用 maps_text_search + maps_search_detail 替代 maps_geo）
    print(f"验证步骤4: 验证开车到{station_address}<={max_driving_seconds}秒（{max_driving_seconds // 60}分钟）")
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"验证步骤4失败: 无法获取{station_address}坐标 - {station_text_result.error}")
        all_passed = False
    elif not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"验证步骤4失败: 未找到{station_address}的坐标信息")
        all_passed = False
    else:
        first_poi_id = station_text_result.pois[0].id
        station_detail_result = maps_search_detail(id=first_poi_id)
        if station_detail_result.error:
            print(f"❌ 获取坐标失败: {station_detail_result.error}")
            all_passed = False
        elif not station_detail_result.location:
            print("❌ 未获取到坐标")
            all_passed = False
        else:
            station_location = station_detail_result.location
            print(f"验证步骤4: 获取到{station_address}坐标: {station_location}")
            
            driving_result = maps_driving_by_coordinates(
                origin=target_poi_location,
                destination=station_location
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
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")
    return result  


if __name__ == "__main__":
    main()
