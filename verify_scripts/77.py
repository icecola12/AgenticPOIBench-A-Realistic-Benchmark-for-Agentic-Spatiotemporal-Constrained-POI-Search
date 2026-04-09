"""
输入：B0FFIIMDT3
输出：True

验证方法：
1) 距离约束(附近2公里内)：调用 maps_around_search(location="113.422973,23.124475", radius="2000", keywords="咖啡厅")，验证返回pois列表中包含目标poi_id=B0FFIIMDT3。
2) 评分约束(>=4.6) 与营业时间约束(当前时间仍营业且可待到22:00左右)：调用 maps_search_detail(id="B0FFIIMDT3")，从 biz_ext 读取 rating>=4.6；并读取 open_time/opentime2，结合time字段(周二 21:10:00)验证该时间点仍在营业且闭店时间>=22:00。
3) 骑行时间约束(<=12分钟)：调用 maps_bicycling_by_coordinates(origin="113.422973,23.124475", destination=POI.location)，验证 total_duration_seconds<=720。
4) 地铁站直线距离约束(最近地铁站<=1000米)：调用 maps_around_search(location=POI.location, radius="1200", keywords="地铁站") 获取附近地铁站列表；对每个地铁站调用 maps_distance(origins=POI.location, destination=station.location)，取最小 distance_meters，验证 min_distance<=1000。
5) 停车场约束(600米内有停车场)：调用 maps_around_search(location=POI.location, radius="600", keywords="停车场")，验证返回pois数量>=1。
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
    target_poi_id: str = "B0FFIIMDT3",
    user_location: str = "113.422973,23.124475",
    search_radius: str = "2000",
    search_keywords: str = "咖啡厅",
    min_rating: float = 4.6,
    current_time: str = "周二 21:10:00",
    max_bicycling_seconds: int = 720,
    subway_search_radius: str = "1200",
    subway_keywords: str = "地铁站",
    max_subway_distance_meters: int = 1000,
    parking_search_radius: str = "600",
    parking_keywords: str = "停车场"
) -> bool:
    """
    验证POI是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID
        user_location: 用户位置坐标，格式为"经度,纬度"
        search_radius: 搜索半径（米）
        search_keywords: 搜索关键词
        min_rating: 最低评分要求
        current_time: 当前时间，格式为"周二 21:10:00"
        max_bicycling_seconds: 最大骑行时间（秒）
        subway_search_radius: 地铁站搜索半径（米）
        subway_keywords: 地铁站搜索关键词
        max_subway_distance_meters: 最大地铁站距离（米）
        parking_search_radius: 停车场搜索半径（米）
        parking_keywords: 停车场搜索关键词
    
    Returns:
        bool: 所有验证条件都满足返回True，否则返回False
    """
    all_passed = True
    
    print("=" * 80)
    print(f"开始验证POI: {target_poi_id}")
    print("=" * 80)
    
    # 步骤1: 距离约束(附近2公里内)
    print("\n【步骤1】距离约束验证：验证POI是否在用户位置附近2公里内")
    print("-" * 80)
    around_result = maps_around_search(
        location=user_location,
        radius=search_radius,
        keywords=search_keywords
    )
    
    if around_result.error:
        print(f"[FAIL] 步骤1失败: {around_result.error}")
        all_passed = False
    else:
        poi_found = False
        if around_result.pois:
            for poi in around_result.pois:
                if poi.id == target_poi_id:
                    poi_found = True
                    break
        
        if poi_found:
            print(f"[PASS] 步骤1通过: POI {target_poi_id} 在附近{search_radius}米内找到")
        else:
            print(f"[FAIL] 步骤1失败: POI {target_poi_id} 未在附近{search_radius}米内找到")
            all_passed = False
    
    # 步骤2: 评分约束与营业时间约束
    print("\n【步骤2】评分约束(>=4.6)与营业时间约束验证")
    print("-" * 80)
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"[FAIL] 步骤2失败: {poi_detail.error}")
        all_passed = False
        poi_location = None
    else:
        poi_location = poi_detail.location
        print(f"[OK] 获取到POI详情")
        print(f"   POI名称: {poi_detail.name or '未知'}")
        print(f"   POI坐标: {poi_location or '未知'}")
        
        if not poi_location:
            print(f"[FAIL] 步骤2失败: 无法获取POI坐标")
            all_passed = False
        else:
            # 验证评分
            rating_passed = False
            if not poi_detail.biz_ext:
                print(f"[FAIL] 步骤2-评分验证失败: 无法获取POI扩展信息（biz_ext）")
                all_passed = False
            else:
                rating = poi_detail.biz_ext.get("rating")
                if rating is None:
                    print(f"[FAIL] 步骤2-评分验证失败: 无法获取评分信息")
                    all_passed = False
                else:
                    try:
                        rating_value = float(rating)
                        if rating_value >= min_rating:
                            print(f"[PASS] 步骤2-评分验证通过: 评分 {rating_value} >= {min_rating}")
                            rating_passed = True
                        else:
                            print(f"[FAIL] 步骤2-评分验证失败: 评分 {rating_value} < {min_rating}")
                            all_passed = False
                    except (ValueError, TypeError):
                        print(f"[FAIL] 步骤2-评分验证失败: 评分格式错误 - {rating}")
                        all_passed = False
            
            # 验证营业时间
            open_time_passed = False
            if poi_detail.biz_ext:
                open_time = poi_detail.biz_ext.get("open_time")
                opentime2 = poi_detail.biz_ext.get("opentime2")
                
                # 优先使用opentime2，如果没有则使用open_time
                business_hours_str = opentime2 if opentime2 else open_time
                
                if not business_hours_str:
                    print(f"[FAIL] 步骤2-营业时间验证失败: biz_ext中未找到open_time或opentime2字段")
                    all_passed = False
                else:
                    print(f"   营业时间信息: {business_hours_str}")
                    print(f"   当前时间: {current_time}")
                    
                    # 解析当前时间
                    weekday_map = {
                        "周一": 0, "周二": 1, "周三": 2, "周四": 3,
                        "周五": 4, "周六": 5, "周日": 6
                    }
                    
                    time_match = re.match(r"周([一二三四五六日])\s+(\d{2}):(\d{2}):(\d{2})", current_time)
                    if not time_match:
                        print(f"[FAIL] 步骤2-营业时间验证失败: 无法解析当前时间格式: {current_time}")
                        all_passed = False
                    else:
                        weekday_str = time_match.group(1)
                        current_hour = int(time_match.group(2))
                        current_minute = int(time_match.group(3))
                        
                        weekday_num = weekday_map.get("周" + weekday_str)
                        if weekday_num is None:
                            print(f"[FAIL] 步骤2-营业时间验证失败: 无法识别星期: {weekday_str}")
                            all_passed = False
                        else:
                            # 解析营业时间字符串
                            is_open = False
                            closing_hour = None
                            
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
                                    weekday_parts = [part.strip() for part in weekday_range_str.split(",")]
                                    
                                    for part in weekday_parts:
                                        if "至" in part:
                                            # 处理"周一至周四"这种情况
                                            start_day, end_day = part.split("至")
                                            start_day_num = weekday_map.get(start_day.strip())
                                            end_day_num = weekday_map.get(end_day.strip())
                                            if start_day_num is not None and end_day_num is not None:
                                                if start_day_num <= weekday_num <= end_day_num:
                                                    weekday_in_range = True
                                                    break
                                        else:
                                            # 单个星期
                                            day_num = weekday_map.get(part.strip())
                                            if day_num == weekday_num:
                                                weekday_in_range = True
                                                break
                                    
                                    if weekday_in_range:
                                        # 检查当前时间是否在营业时间内（含跨天：关门在次日则 在段内 = current>=open 或 current<=close）
                                        current_time_minutes = current_hour * 60 + current_minute
                                        start_time_minutes = start_hour * 60 + start_minute
                                        end_time_minutes = end_hour * 60 + end_minute
                                        
                                        if end_time_minutes < start_time_minutes:
                                            # 跨天时段
                                            if current_time_minutes >= start_time_minutes or current_time_minutes <= end_time_minutes:
                                                is_open = True
                                                closing_hour = end_hour + 24  # 关门在次日，视为满足>=22:00
                                                break
                                        else:
                                            if start_time_minutes <= current_time_minutes <= end_time_minutes:
                                                is_open = True
                                                closing_hour = end_hour
                                                break
                            else:
                                # 简单格式，如"09:00-22:00"
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
                                        # 跨天时段
                                        if current_time_minutes >= start_time_minutes or current_time_minutes <= end_time_minutes:
                                            is_open = True
                                            closing_hour = end_hour + 24  # 关门在次日，视为满足>=22:00
                                    else:
                                        if start_time_minutes <= current_time_minutes <= end_time_minutes:
                                            is_open = True
                                            closing_hour = end_hour
                            
                            if is_open and closing_hour is not None:
                                # 验证闭店时间>=22:00（跨天时 closing_hour 可能为 end_hour+24）
                                display_hour = (closing_hour - 24) if closing_hour >= 24 else closing_hour
                                display_suffix = "（次日）" if closing_hour >= 24 else ""
                                if closing_hour >= 22:
                                    print(f"[PASS] 步骤2-营业时间验证通过: 当前时间在营业时间内，闭店时间 {display_hour:02d}:00{display_suffix} >= 22:00")
                                    open_time_passed = True
                                else:
                                    print(f"[FAIL] 步骤2-营业时间验证失败: 闭店时间 {display_hour:02d}:00{display_suffix} < 22:00")
                                    all_passed = False
                            else:
                                print(f"[FAIL] 步骤2-营业时间验证失败: 当前时间不在营业时间内")
                                all_passed = False
    
    # 步骤3: 骑行时间约束(<=12分钟)
    print("\n【步骤3】骑行时间约束验证(<=12分钟)")
    print("-" * 80)
    if not poi_location:
        print(f"[FAIL] 步骤3失败: 无法获取POI坐标，跳过骑行时间验证")
        all_passed = False
    else:
        bicycling_result = maps_bicycling_by_coordinates(
            origin=user_location,
            destination=poi_location
        )
        
        if bicycling_result.error:
            print(f"[FAIL] 步骤3失败: {bicycling_result.error}")
            all_passed = False
        else:
            if bicycling_result.total_duration_seconds is None:
                print(f"[FAIL] 步骤3失败: 无法获取骑行时间")
                all_passed = False
            else:
                duration = bicycling_result.total_duration_seconds
                if duration <= max_bicycling_seconds:
                    print(f"[PASS] 步骤3通过: 骑行时间 {duration}秒 ({duration//60}分{duration%60}秒) <= {max_bicycling_seconds}秒 ({max_bicycling_seconds//60}分钟)")
                else:
                    print(f"[FAIL] 步骤3失败: 骑行时间 {duration}秒 ({duration//60}分{duration%60}秒) > {max_bicycling_seconds}秒 ({max_bicycling_seconds//60}分钟)")
                    all_passed = False
    
    # 步骤4: 地铁站直线距离约束(最近地铁站<=1000米)
    print("\n【步骤4】地铁站直线距离约束验证(最近地铁站<=1000米)")
    print("-" * 80)
    if not poi_location:
        print(f"[FAIL] 步骤4失败: 无法获取POI坐标，跳过地铁站距离验证")
        all_passed = False
    else:
        subway_search_result = maps_around_search(
            location=poi_location,
            radius=subway_search_radius,
            keywords=subway_keywords
        )
        
        if subway_search_result.error:
            print(f"[FAIL] 步骤4失败: {subway_search_result.error}")
            all_passed = False
        else:
            if not subway_search_result.pois or len(subway_search_result.pois) == 0:
                print(f"[FAIL] 步骤4失败: 未找到附近地铁站")
                all_passed = False
            else:
                print(f"   找到 {len(subway_search_result.pois)} 个附近地铁站")
                min_distance = float('inf')
                
                for station in subway_search_result.pois:
                    if not station.location:
                        continue
                    
                    distance_result = maps_distance(
                        origins=poi_location,
                        destination=station.location
                    )
                    
                    if distance_result.error or not distance_result.results:
                        continue
                    
                    distance = distance_result.results[0].distance_meters
                    if distance < min_distance:
                        min_distance = distance
                
                if min_distance == float('inf'):
                    print(f"[FAIL] 步骤4失败: 无法计算到任何地铁站的距离")
                    all_passed = False
                else:
                    if min_distance <= max_subway_distance_meters:
                        print(f"[PASS] 步骤4通过: 最近地铁站距离 {min_distance}米 <= {max_subway_distance_meters}米")
                    else:
                        print(f"[FAIL] 步骤4失败: 最近地铁站距离 {min_distance}米 > {max_subway_distance_meters}米")
                        all_passed = False
    
    # 步骤5: 停车场约束(600米内有停车场)
    print("\n【步骤5】停车场约束验证(600米内有停车场)")
    print("-" * 80)
    if not poi_location:
        print(f"[FAIL] 步骤5失败: 无法获取POI坐标，跳过停车场验证")
        all_passed = False
    else:
        parking_search_result = maps_around_search(
            location=poi_location,
            radius=parking_search_radius,
            keywords=parking_keywords
        )
        
        if parking_search_result.error:
            print(f"[FAIL] 步骤5失败: {parking_search_result.error}")
            all_passed = False
        else:
            if parking_search_result.pois and len(parking_search_result.pois) >= 1:
                print(f"[PASS] 步骤5通过: 找到 {len(parking_search_result.pois)} 个停车场")
            else:
                print(f"[FAIL] 步骤5失败: 未找到停车场（找到 {len(parking_search_result.pois) if parking_search_result.pois else 0} 个）")
                all_passed = False
    
    # 输出最终结果
    print("\n" + "=" * 80)
    if all_passed:
        print("最终验证结果: [PASS] 满足（所有验证条件都通过）")
        print("=" * 80)
        return True
    else:
        print("最终验证结果: [FAIL] 不满足（部分或全部验证条件未通过）")
        print("=" * 80)
        return False


def main():
    result = verify_poi()
    print(f"\n验证函数返回值: {result}")


if __name__ == "__main__":
    main()
