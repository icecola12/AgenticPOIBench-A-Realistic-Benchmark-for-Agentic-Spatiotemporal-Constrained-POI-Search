"""
输入：B0FFK6L2MX
输出：True

验证方法：
1) 验证“附近2公里内的餐厅”
- 调用 maps_around_search({location:"118.498675,31.682374", radius:"2000", keywords:"餐厅"})
- 验证返回pois列表中包含 target_poi_id=B0FFK6L2MX

2) 验证“步行不超过20分钟”
- 调用 maps_search_detail({id:"B0FFK6L2MX"}) 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 目标POI坐标 destination
- 调用 maps_walking_by_coordinates({origin:"118.498675,31.682374", destination: destination}) 得到 poi_id，再 maps_search_detail(id=poi_id) 得到 步行总时长 t_walk
- 验证 t_walk <= 20*60 秒

3) 验证“你步行与同事驾车到达时间差不超过15分钟”
- 以“雨山湖饭店·欢乐时光西餐厅(湖南路店)”的坐标 118.506076,31.684048 作为“雨山湖饭店附近”的出发点 origin_colleague
- 调用 maps_driving_by_coordinates({origin: origin_colleague, destination: destination}) 得到驾车总时长 t_drive
- 计算 |t_walk - t_drive|，验证 <= 15*60 秒

4) 验证“23:30后仍营业”与“300米内有停车场”
- 调用 maps_search_detail({id:"B0FFK6L2MX"}) 读取 biz_ext.open_time/opentime2
- 验证营业时间覆盖 23:30（即当天23:30仍在营业）
- 调用 maps_around_search({location: destination, radius:"300", keywords:"停车场"})
- 验证返回pois数量>0
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
    target_poi_id: str = 'B0FFK6L2MX',
    user_location: str = '118.498675,31.682374',
    radius: str = '2000',
    keywords: str = '餐厅',
    max_walking_seconds: int = 1200,
    colleague_location: str = '118.506076,31.684048',
    max_time_diff_seconds: int = 900,
    check_time: str = '23:30',
    parking_radius: str = '300',
    parking_keywords: str = '停车场'
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标，格式为"经度,纬度"
        radius: 搜索半径（米），字符串格式
        keywords: 搜索关键词
        max_walking_seconds: 最大步行时长（秒）
        colleague_location: 同事出发位置坐标，格式为"经度,纬度"
        max_time_diff_seconds: 最大时间差（秒）
        check_time: 需要检查的营业时间，格式为"HH:MM"
        parking_radius: 停车场搜索半径（米），字符串格式
        parking_keywords: 停车场搜索关键词
    
    Returns:
        bool: True表示所有验证通过，False表示部分或全部验证失败
    """
    all_passed = True
    
    # 验证步骤1: 验证"附近2公里内的餐厅"
    print("验证步骤1: 验证附近2公里内的餐厅")
    around_search_result = maps_around_search(
        location=user_location,
        radius=radius,
        keywords=keywords
    )
    
    if around_search_result.error:
        print(f"验证步骤1失败: {around_search_result.error}")
        all_passed = False
    elif not around_search_result.pois:
        print("验证步骤1失败: 未找到符合条件的POI")
        all_passed = False
    else:
        # 检查返回的POI列表中是否包含目标POI ID
        found = False
        for poi in around_search_result.pois:
            if poi.id == target_poi_id:
                found = True
                break
        
        if found:
            print(f"验证步骤1通过: 在{radius}米内找到目标{keywords}POI")
        else:
            print(f"验证步骤1失败: 在{radius}米内未找到目标{keywords}POI")
            all_passed = False
    
    # 验证步骤2: 验证"步行不超过20分钟"
    print(f"验证步骤2: 验证步行不超过20分钟（{max_walking_seconds}秒）")
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"验证步骤2失败: {poi_detail.error}")
        all_passed = False
    elif not poi_detail.location:
        print("验证步骤2失败: 未获取到POI坐标")
        all_passed = False
    else:
        target_poi_location = poi_detail.location
        print(f"验证步骤2: 获取到POI坐标 {target_poi_location}")
        
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
    
    # 验证步骤3: 验证"你步行与同事驾车到达时间差不超过15分钟"
    print(f"验证步骤3: 验证步行与同事驾车到达时间差不超过15分钟（{max_time_diff_seconds}秒）")
    
    if not poi_detail.location:
        print("验证步骤3失败: 未获取到POI坐标")
        all_passed = False
    else:
        target_poi_location = poi_detail.location
        
        # 获取步行时长（如果步骤2已经获取，可以重用，但为了代码清晰，这里重新获取）
        walking_result = maps_walking_by_coordinates(
            origin=user_location,
            destination=target_poi_location
        )
        
        if walking_result.error or walking_result.total_duration_seconds is None:
            print("验证步骤3失败: 无法获取步行时长")
            all_passed = False
        else:
            walking_seconds = walking_result.total_duration_seconds
            
            # 获取同事驾车时长
            driving_result = maps_driving_by_coordinates(
                origin=colleague_location,
                destination=target_poi_location
            )
            
            if driving_result.error:
                print(f"验证步骤3失败: {driving_result.error}")
                all_passed = False
            elif driving_result.total_duration_seconds is None:
                print("验证步骤3失败: 未获取到驾车时长")
                all_passed = False
            else:
                driving_seconds = driving_result.total_duration_seconds
                time_diff = abs(walking_seconds - driving_seconds)
                
                if time_diff <= max_time_diff_seconds:
                    print(f"验证步骤3通过: 时间差 {time_diff}秒 <= {max_time_diff_seconds}秒（步行{walking_seconds}秒，驾车{driving_seconds}秒）")
                else:
                    print(f"验证步骤3失败: 时间差 {time_diff}秒 > {max_time_diff_seconds}秒（步行{walking_seconds}秒，驾车{driving_seconds}秒）")
                    all_passed = False
    
    # 验证步骤4: 验证"23:30后仍营业"与"300米内有停车场"
    print("验证步骤4: 验证23:30后仍营业与300米内有停车场")
    
    # 4.1 验证营业时间覆盖23:30
    print(f"验证步骤4.1: 验证营业时间覆盖{check_time}")
    
    if not poi_detail.biz_ext:
        print("验证步骤4.1失败: 无法获取POI扩展信息（biz_ext）")
        all_passed = False
    else:
        open_time = poi_detail.biz_ext.get("open_time")
        opentime2 = poi_detail.biz_ext.get("opentime2")
        
        # 优先使用opentime2，如果没有则使用open_time
        business_hours_str = opentime2 if opentime2 else open_time
        
        if not business_hours_str:
            print("验证步骤4.1失败: biz_ext中未找到open_time或opentime2字段")
            all_passed = False
        else:
            print(f"验证步骤4.1: 营业时间信息: {business_hours_str}")
            print(f"验证步骤4.1: 检查时间: {check_time}")
            
            # 解析检查时间
            check_time_match = re.match(r"(\d{2}):(\d{2})", check_time)
            if not check_time_match:
                print(f"验证步骤4.1失败: 无法解析检查时间格式: {check_time}")
                all_passed = False
            else:
                check_hour = int(check_time_match.group(1))
                check_minute = int(check_time_match.group(2))
                check_time_minutes = check_hour * 60 + check_minute
                
                # 解析营业时间字符串，检查是否覆盖23:30
                is_open_at_check_time = False
                
                # 尝试匹配带星期的时间段格式
                # 例如: "周一至周四,周日 07:00-22:00；周五至周六 07:00-22:30"
                pattern_with_weekday = r"([^；]+?)\s+(\d{2}):(\d{2})-(\d{2}):(\d{2})"
                matches = re.findall(pattern_with_weekday, business_hours_str)
                
                if matches:
                    # 有星期信息的时间段，检查所有时间段
                    for match in matches:
                        start_hour = int(match[1])
                        start_minute = int(match[2])
                        end_hour = int(match[3])
                        end_minute = int(match[4])
                        
                        start_time_minutes = start_hour * 60 + start_minute
                        end_time_minutes = end_hour * 60 + end_minute
                        
                        if end_time_minutes < start_time_minutes:
                            # 跨天的情况，如22:00-02:00
                            if check_time_minutes >= start_time_minutes or check_time_minutes <= end_time_minutes:
                                is_open_at_check_time = True
                                break
                        else:
                            # 正常情况
                            if start_time_minutes <= check_time_minutes <= end_time_minutes:
                                is_open_at_check_time = True
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
                        
                        start_time_minutes = start_hour * 60 + start_minute
                        end_time_minutes = end_hour * 60 + end_minute
                        
                        if end_time_minutes < start_time_minutes:
                            # 跨天的情况
                            if check_time_minutes >= start_time_minutes or check_time_minutes <= end_time_minutes:
                                is_open_at_check_time = True
                        else:
                            if start_time_minutes <= check_time_minutes <= end_time_minutes:
                                is_open_at_check_time = True
                
                if is_open_at_check_time:
                    print(f"验证步骤4.1通过: 营业时间覆盖{check_time}")
                else:
                    print(f"验证步骤4.1失败: 营业时间不覆盖{check_time}")
                    all_passed = False
    
    # 4.2 验证300米内有停车场
    print(f"验证步骤4.2: 验证{parking_radius}米内有{parking_keywords}")
    
    if not poi_detail.location:
        print("验证步骤4.2失败: 未获取到POI坐标")
        all_passed = False
    else:
        target_poi_location = poi_detail.location
        
        parking_result = maps_around_search(
            location=target_poi_location,
            radius=parking_radius,
            keywords=parking_keywords
        )
        
        if parking_result.error:
            print(f"验证步骤4.2失败: {parking_result.error}")
            all_passed = False
        elif not parking_result.pois or len(parking_result.pois) == 0:
            print(f"验证步骤4.2失败: POI附近{parking_radius}米内未找到{parking_keywords}")
            all_passed = False
        else:
            parking_count = len(parking_result.pois)
            print(f"验证步骤4.2通过: POI附近{parking_radius}米内找到{parking_count}个{parking_keywords}")
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")
    return result  


if __name__ == "__main__":
    main()
