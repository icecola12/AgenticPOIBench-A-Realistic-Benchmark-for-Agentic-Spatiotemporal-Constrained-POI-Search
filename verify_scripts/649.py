"""
修改任务指令：你要找一个附近2公里内的咖啡厅，打算先去那儿和客户见面再一起出发。为了方便客户从“西北民航大厦”过来，这家咖啡厅离西北民航大厦的直线距离不能超过1.6公里。你自己需要步行过去，步行时间不能超过10分钟。你还希望这家咖啡厅的评分至少有4.6分，并且现在还在营业（不要已经打烊的）。另外，咖啡厅附近500米内必须有地铁站，方便后续转地铁走。你有礼貌但非常坚决和不耐烦，希望尽快解决问题。
输入：B0FFFON0T7
输出：True

验证方法：
1) 周边可达性：调用 maps_around_search(location=108.910954,34.244338, radius=2000, keywords=咖啡厅)，验证返回pois中包含目标poi_id=B0FFFON0T7。
2) 评分约束：调用 maps_search_detail(id=B0FFFON0T7)，读取biz_ext.rating，验证 rating>=4.6。
3) 营业状态（基于当前时间）：从 maps_search_detail 的 biz_ext.open_time/opentime2 获取营业时间段；结合time字段（周二 16:20:00），验证当前时刻落在营业时间内（该POI为09:00-24:00）。
4) 步行时间：调用 maps_walking_by_coordinates(origin=108.910954,34.244338, destination=目标POI的location=108.909794,34.241743)，验证 total_duration_seconds<=600。
5) 参考地直线距离：调用 maps_text_search(keywords=reference_address, city=reference_city) 取 poi_id，再 maps_search_detail(id=poi_id) 获取其 location；再调用 maps_distance，验证 distance_meters<=1600。
6) 地铁站邻近：调用 maps_around_search(location=108.909794,34.241743, radius=500, keywords=地铁站)，验证返回pois数量>=1（如“西北工业大学(地铁站)”）。
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
    target_poi_id: str = "B0FFFON0T7",
    user_location: str = "108.910954,34.244338",
    search_radius: str = "2000",
    search_keywords: str = "咖啡厅",
    min_rating: float = 4.6,
    current_time: str = "周二 16:20:00",
    max_walking_seconds: int = 600,
    reference_address: str = "西北民航大厦",
    reference_city: str = "",
    max_distance_meters: int = 1600,
    subway_search_radius: str = "500",
    subway_keywords: str = "地铁站"
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID，默认值为 "B0FFFON0T7"
        user_location: 用户位置坐标，格式为"经度,纬度"，默认值为 "108.910954,34.244338"
        search_radius: 搜索半径（米），默认值为 "2000"（2公里）
        search_keywords: 搜索关键词，默认值为 "咖啡厅"
        min_rating: 最小评分，默认值为 4.6
        current_time: 当前时间，格式为"周X HH:MM:SS"，默认值为 "周二 16:20:00"
        max_walking_seconds: 最大步行时间（秒），默认值为 600（10分钟）
        reference_address: 参考地址，默认值为 "西北民航大厦"
        reference_city: 参考地址所在城市，默认值为空字符串
        max_distance_meters: 最大直线距离（米），默认值为 1600（1.6公里）
        subway_search_radius: 地铁站搜索半径（米），默认值为 "500"
        subway_keywords: 地铁站搜索关键词，默认值为 "地铁站"
    
    Returns:
        bool: 所有验证条件都满足返回True，否则返回False
    """
    all_passed = True
    
    # 步骤1：周边可达性
    print("步骤1：验证周边可达性（2公里内）")
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
    
    # 步骤2：评分约束
    print("步骤2：验证评分>=4.6")
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"  验证失败：获取POI详情出错 - {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"  验证失败：无法获取POI坐标")
        return False
    
    poi_location = poi_detail.location
    print(f"  目标POI坐标: {poi_location}")
    
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
                else:
                    print(f"  验证失败：评分 {rating_value} < {min_rating}")
                    all_passed = False
            except (ValueError, TypeError):
                print(f"  验证失败：评分格式错误 - {rating}")
                all_passed = False
    
    # 步骤3：营业状态（基于当前时间）
    print("步骤3：验证营业状态（当前时间：{}）".format(current_time))
    
    if not poi_detail.biz_ext:
        print(f"  验证失败：无法获取POI扩展信息（biz_ext）")
        all_passed = False
    else:
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
                    else:
                        print(f"  验证失败：当前时间 {current_time} 不在营业时间内")
                        all_passed = False
    
    # 步骤4：步行时间
    print("步骤4：验证步行时间不超过10分钟")
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=poi_location
    )
    
    if walking_result.error:
        print(f"  验证失败：步行路线规划出错 - {walking_result.error}")
        all_passed = False
    elif walking_result.total_duration_seconds is None:
        print(f"  验证失败：无法获取步行时长")
        all_passed = False
    else:
        walking_seconds = walking_result.total_duration_seconds
        
        if walking_seconds <= max_walking_seconds:
            print(f"  验证通过：步行时间 {walking_seconds//60}分{walking_seconds%60}秒 <= {max_walking_seconds//60}分钟")
        else:
            print(f"  验证失败：步行时间 {walking_seconds//60}分{walking_seconds%60}秒 > {max_walking_seconds//60}分钟")
            all_passed = False
    
    # 步骤5：参考地直线距离
    print("步骤5：验证参考地直线距离<=1.6公里")
    
    # 调用获取参考地址坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
    reference_text_result = maps_text_search(keywords=reference_address, city=reference_city or "")
    if reference_text_result.error:
        print(f"  验证失败：获取参考地址坐标出错 - {reference_text_result.error}")
        all_passed = False
    elif not reference_text_result.pois or len(reference_text_result.pois) == 0:
        print(f"  验证失败：未找到参考地址")
        all_passed = False
    else:
        first_poi_id = reference_text_result.pois[0].id
        reference_detail_result = maps_search_detail(id=first_poi_id)
        if reference_detail_result.error:
            print(f"❌ 获取坐标失败: {reference_detail_result.error}")
            all_passed = False
        elif not reference_detail_result.location:
            print("❌ 未获取到坐标")
            all_passed = False
        else:
            reference_location = reference_detail_result.location
            print(f"  参考地址坐标: {reference_location}")
            
            # 调用 maps_distance 计算直线距离
            distance_result = maps_distance(
                origins=reference_location,
                destination=poi_location
            )
            
            if distance_result.error:
                print(f"  验证失败：距离计算出错 - {distance_result.error}")
                all_passed = False
            elif not distance_result.results or len(distance_result.results) == 0:
                print(f"  验证失败：无法获取距离信息")
                all_passed = False
            else:
                distance_meters = distance_result.results[0].distance_meters
                
                if distance_meters <= max_distance_meters:
                    print(f"  验证通过：直线距离 {distance_meters}米 <= {max_distance_meters}米")
                else:
                    print(f"  验证失败：直线距离 {distance_meters}米 > {max_distance_meters}米")
                    all_passed = False
    
    # 步骤6：地铁站邻近
    print("步骤6：验证附近500米内有地铁站")
    subway_search_result = maps_around_search(
        location=poi_location,
        radius=subway_search_radius,
        keywords=subway_keywords
    )
    
    if subway_search_result.error:
        print(f"  验证失败：地铁站搜索出错 - {subway_search_result.error}")
        all_passed = False
    elif not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"  验证失败：附近{int(subway_search_radius)}米内未找到地铁站")
        all_passed = False
    else:
        subway_count = len(subway_search_result.pois)
        if subway_count >= 1:
            print(f"  验证通过：附近{int(subway_search_radius)}米内找到 {subway_count} 个地铁站")
            # 打印找到的地铁站名称（用于参考）
            for poi in subway_search_result.pois[:3]:  # 只打印前3个
                print(f"    - {poi.name}")
        else:
            print(f"  验证失败：附近{int(subway_search_radius)}米内未找到地铁站")
            all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '不通过'}")
    return result  


if __name__ == "__main__":
    main()
