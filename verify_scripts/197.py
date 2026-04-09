"""
修改任务指令：你想在附近2000米内找一家酒吧，评分要高于3.5。这家酒吧离大塘街道办事处的距离要超过500米。从你家开车去酒吧的路上，至少需要存在一个途径点，满足国龙财富中心直线距离在600米内。而且这条路上的任意一个途经点附近200米内都得有ATM。酒吧到公交站的步行时间要在15分钟以内。然后你要去灏景尚都的朋友家，从你家经过酒吧再到朋友家的总开车时间不能超过15分钟，而且这样绕路比直接去朋友家增加的时间不能超过5分钟。最后，酒吧到梧州站的开车时间不能超过15分钟。你说话简短急促，希望快速完成所有事。
输入：B0FFK244Y0
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('111.272214,23.4772', '酒吧', 2000)验证目标酒吧在2000米范围内。
2. 调用maps_search_detail('B0FFK244Y0')获取酒吧评分，验证>3.5。
3. 调用maps_distance('111.281110,23.478488', '111.279551,23.484944')验证酒吧到大塘街道办事处距离>500米。
4. 调用maps_driving_by_coordinates('111.272214,23.4772', '111.281110,23.478488')获取驾车步骤，对每个步骤坐标调用maps_distance(步骤坐标, '111.277526,23.473687')验证是否存在一点到国龙财富中心距离<600米。
5. 对上述每个步骤坐标调用maps_around_search(步骤坐标, 'ATM', 200)验证是否存在ATM在200米内。
6. 调用maps_walking_by_coordinates('111.281110,23.478488', '111.280601,23.479329')验证酒吧到公交站步行时间≤900秒（15分钟）。
7. 调用maps_driving_by_coordinates('111.272214,23.4772', '111.275551,23.473118')获取直接驾车时间T_direct。
8. 调用maps_driving_by_coordinates('111.272214,23.4772', '111.281110,23.478488')获取第一段驾车时间T1，调用maps_driving_by_coordinates('111.281110,23.478488', '111.275551,23.473118')获取第二段驾车时间T2，验证T1+T2≤900秒（15分钟）且(T1+T2)-T_direct≤300秒（5分钟）。
9. 调用maps_driving_by_coordinates('111.281110,23.478488', '111.240760,23.486899')验证酒吧到梧州站驾车时间≤900秒（15分钟）。
"""
import sys
import os
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
    maps_geo,
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
    target_poi_id: str = 'B0FFK244Y0',
    user_location: str = '111.272214,23.4772'
) -> bool:
    """
    验证POI是否符合要求
    
    Args:
        target_poi_id: 目标POI ID，默认值为 'B0FFK244Y0'
        user_location: 用户位置坐标，默认值为 '111.272214,23.4772'
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 调用maps_around_search验证目标酒吧在2000米范围内
    print("验证步骤1: 验证目标酒吧在2000米范围内")
    around_result = maps_around_search(user_location, '2000', '酒吧')
    if around_result.error:
        print(f"  验证失败: {around_result.error}")
        return False
    
    target_found = False
    if around_result.pois:
        for poi in around_result.pois:
            if poi.id == target_poi_id:
                target_found = True
                break
    
    if target_found:
        print("  验证通过: 目标酒吧在2000米范围内")
    else:
        print("  验证失败: 目标酒吧不在2000米范围内")
        all_passed = False
    
    # 验证步骤2: 调用maps_search_detail获取酒吧评分，验证>3.5
    print("验证步骤2: 验证酒吧评分>3.5")
    detail_result = maps_search_detail(target_poi_id)
    if detail_result.error:
        print(f"  验证失败: {detail_result.error}")
        return False
    
    if not detail_result.location:
        print("  验证失败: 无法获取酒吧坐标")
        return False
    
    bar_location = detail_result.location
    rating = None
    if detail_result.biz_ext and isinstance(detail_result.biz_ext, dict):
        rating_str = detail_result.biz_ext.get('rating', '')
        if rating_str:
            try:
                rating = float(rating_str)
            except (ValueError, TypeError):
                pass
    
    if rating is not None and rating > 3.5:
        print(f"  验证通过: 酒吧评分 {rating} > 3.5")
    else:
        print(f"  验证失败: 酒吧评分 {rating} <= 3.5")
        all_passed = False
    
    # 验证步骤3: 验证酒吧到大塘街道办事处距离>500米
    print("验证步骤3: 验证酒吧到大塘街道办事处距离>500米")
    # 需要先搜索大塘街道办事处坐标
    dtd_search = maps_text_search('大塘街道办事处', '梧州')
    if dtd_search.error or not dtd_search.pois:
        print("  验证失败: 无法找到大塘街道办事处")
        return False
    
    dtd_poi_id = dtd_search.pois[0].id
    dtd_detail = maps_search_detail(dtd_poi_id)
    if dtd_detail.error or not dtd_detail.location:
        print("  验证失败: 无法获取大塘街道办事处坐标")
        return False
    
    dtd_location = dtd_detail.location
    distance_result = maps_distance(bar_location, dtd_location)
    if distance_result.error or not distance_result.results:
        print(f"  验证失败: {distance_result.error or '无法计算距离'}")
        return False
    
    distance_to_dtd = distance_result.results[0].distance_meters
    if distance_to_dtd > 500:
        print(f"  验证通过: 酒吧到大塘街道办事处距离 {distance_to_dtd} 米 > 500 米")
    else:
        print(f"  验证失败: 酒吧到大塘街道办事处距离 {distance_to_dtd} 米 <= 500 米")
        all_passed = False
    
    # 验证步骤4: 获取驾车步骤，验证是否存在一点到国龙财富中心距离<600米
    print("验证步骤4: 验证驾车路线中存在一点到国龙财富中心距离<600米")
    # 需要先搜索国龙财富中心坐标
    glcf_search = maps_text_search('国龙财富中心', '梧州')
    if glcf_search.error or not glcf_search.pois:
        print("  验证失败: 无法找到国龙财富中心")
        return False
    
    glcf_poi_id = glcf_search.pois[0].id
    glcf_detail = maps_search_detail(glcf_poi_id)
    if glcf_detail.error or not glcf_detail.location:
        print("  验证失败: 无法获取国龙财富中心坐标")
        return False
    
    glcf_location = glcf_detail.location
    
    # 获取驾车路线
    driving_result = maps_driving_by_coordinates(user_location, bar_location)
    if driving_result.error or not driving_result.steps:
        print(f"  验证失败: {driving_result.error or '无法获取驾车路线'}")
        return False
    
    # 收集所有步骤坐标
    step_coords = set()
    for step in driving_result.steps:
        step_coords.add(step.from_coordinates)
        step_coords.add(step.to_coordinates)
    
    step4_passed = False
    for coord in step_coords:
        # 验证到国龙财富中心的距离
        dist_to_glcf = maps_distance(coord, glcf_location)
        if dist_to_glcf.error or not dist_to_glcf.results:
            continue
        
        distance_glcf = dist_to_glcf.results[0].distance_meters
        if distance_glcf < 600:
            step4_passed = True
            print(f"  验证通过: 找到途经点 {coord} 到国龙财富中心距离 {distance_glcf} 米 < 600 米")
            break
    
    if not step4_passed:
        print("  验证失败: 未找到满足条件的途经点")
        all_passed = False
    
    # 验证步骤5: 对上述每个步骤坐标调用maps_around_search验证是否存在ATM在200米内
    print("验证步骤5: 验证所有步骤坐标附近200米内存在ATM")
    step5_passed = True
    for coord in step_coords:
        atm_search = maps_around_search(coord, '200', 'ATM')
        if atm_search.error or not atm_search.pois:
            print(f"  验证失败: 途经点 {coord} 附近200米内没有ATM")
            step5_passed = False
        else:
            print(f"  验证通过: 途经点 {coord} 附近200米内有ATM")
    
    if not step5_passed:
        all_passed = False
    
    # 验证步骤6: 验证酒吧到公交站步行时间≤900秒（15分钟）
    print("验证步骤6: 验证酒吧到公交站步行时间≤600秒（15分钟）")
    # 需要搜索公交站坐标（根据用户原始指令，应该是"公交站"，但需要找到具体的）
    # 根据验证步骤，可能是"市图书馆公交站"或类似的，但这里我们搜索"公交站"
    bus_stop_search = maps_around_search(bar_location, '500', '公交站')
    if bus_stop_search.error or not bus_stop_search.pois:
        print("  验证失败: 无法找到公交站")
        return False
    
    bus_stop_location = bus_stop_search.pois[0].location
    if not bus_stop_location:
        print("  验证失败: 无法获取公交站坐标")
        return False
    
    walking_result = maps_walking_by_coordinates(bar_location, bus_stop_location)
    if walking_result.error:
        print(f"  验证失败: {walking_result.error}")
        return False
    
    walking_time = walking_result.total_duration_seconds if walking_result.total_duration_seconds else 0
    if walking_time <= 900:
        print(f"  验证通过: 酒吧到公交站步行时间 {walking_time} 秒 ≤ 900 秒")
    else:
        print(f"  验证失败: 酒吧到公交站步行时间 {walking_time} 秒 > 900 秒")
        all_passed = False
    
    # 验证步骤7: 获取直接驾车时间T_direct
    print("验证步骤7: 获取直接驾车时间T_direct")
    # 需要搜索灏景尚都坐标
    hjsd_search = maps_text_search('灏景尚都', '梧州')
    if hjsd_search.error or not hjsd_search.pois:
        print("  验证失败: 无法找到灏景尚都")
        return False
    
    hjsd_poi_id = hjsd_search.pois[0].id
    hjsd_detail = maps_search_detail(hjsd_poi_id)
    if hjsd_detail.error or not hjsd_detail.location:
        print("  验证失败: 无法获取灏景尚都坐标")
        return False
    
    hjsd_location = hjsd_detail.location
    
    direct_driving = maps_driving_by_coordinates(user_location, hjsd_location)
    if direct_driving.error:
        print(f"  验证失败: {direct_driving.error}")
        return False
    
    T_direct = direct_driving.total_duration_seconds if direct_driving.total_duration_seconds else 0
    print(f"  直接驾车时间 T_direct = {T_direct} 秒")
    
    # 验证步骤8: 验证T1+T2≤900秒（15分钟）且(T1+T2)-T_direct≤300秒（5分钟）
    print("验证步骤8: 验证T1+T2≤900秒（15分钟）且(T1+T2)-T_direct≤300秒（5分钟）")
    T1_result = maps_driving_by_coordinates(user_location, bar_location)
    if T1_result.error:
        print(f"  验证失败: {T1_result.error}")
        return False
    
    T1 = T1_result.total_duration_seconds if T1_result.total_duration_seconds else 0
    
    T2_result = maps_driving_by_coordinates(bar_location, hjsd_location)
    if T2_result.error:
        print(f"  验证失败: {T2_result.error}")
        return False
    
    T2 = T2_result.total_duration_seconds if T2_result.total_duration_seconds else 0
    
    T_total = T1 + T2
    time_diff = T_total - T_direct
    
    step8_passed = True
    if T_total <= 900:
        print(f"  验证通过: T1+T2 = {T_total} 秒 ≤ 900 秒")
    else:
        print(f"  验证失败: T1+T2 = {T_total} 秒 > 900 秒")
        step8_passed = False
    
    if time_diff <= 300:
        print(f"  验证通过: (T1+T2)-T_direct = {time_diff} 秒 ≤ 300 秒")
    else:
        print(f"  验证失败: (T1+T2)-T_direct = {time_diff} 秒 > 300 秒")
        step8_passed = False
    
    if not step8_passed:
        all_passed = False
    
    # 验证步骤9: 验证酒吧到梧州站驾车时间≤900秒（15分钟）
    print("验证步骤9: 验证酒吧到梧州站驾车时间≤900秒（15分钟）")
    # 需要搜索梧州站坐标
    wz_station_search = maps_text_search('梧州站', '梧州')
    if wz_station_search.error or not wz_station_search.pois:
        print("  验证失败: 无法找到梧州站")
        return False
    
    wz_station_poi_id = wz_station_search.pois[0].id
    wz_station_detail = maps_search_detail(wz_station_poi_id)
    if wz_station_detail.error or not wz_station_detail.location:
        print("  验证失败: 无法获取梧州站坐标")
        return False
    
    wz_station_location = wz_station_detail.location
    
    station_driving = maps_driving_by_coordinates(bar_location, wz_station_location)
    if station_driving.error:
        print(f"  验证失败: {station_driving.error}")
        return False
    
    station_time = station_driving.total_duration_seconds if station_driving.total_duration_seconds else 0
    if station_time <= 900:
        print(f"  验证通过: 酒吧到梧州站驾车时间 {station_time} 秒 ≤ 900 秒")
    else:
        print(f"  验证失败: 酒吧到梧州站驾车时间 {station_time} 秒 > 900 秒")
        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
