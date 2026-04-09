"""
修改任务指令：你要找一个附近2.5公里以内的商场，步行过去别超过25分钟。因为你准备转乘公共交通去见客户，所以商场附近600米内必须能找到一个公交站。你还要确认这个商场在地图上的评分不低于4.8。你虽然心情不好，但仍然保持礼貌和独立的姿态。
输入：B0FFG6LDP3
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_search_detail(id='B0FFG6LDP3') 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 评分rating与坐标location，验证 rating>=4.8。
2) 调用 maps_around_search(location='109.120748,21.457503', radius='2500', keywords='商场')，验证返回pois中包含 id='B0FFG6LDP3'（从而验证“离你不超过2.5公里且为商场”）。
3) 调用 maps_walking_by_coordinates(origin='109.120748,21.457503', destination=目标POI.location) 获取步行时长t_walk，验证 t_walk<=25分钟。
4) 调用 maps_around_search(location=目标POI.location, radius='600', keywords='公交站')，验证返回pois非空（或至少存在1个公交站POI）。
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
    target_poi_id: str = 'B0FFG6LDP3',
    user_location: str = '109.120748,21.457503',
    min_rating: float = 4.8,
    max_distance_meters: str = '2500',
    keywords: str = '商场',
    max_walking_minutes: int = 25,
    bus_stop_radius: str = '600',
    bus_stop_keywords: str = '公交站'
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标，格式为"经度,纬度"
        min_rating: 最低评分要求
        max_distance_meters: 最大距离（米），字符串格式
        keywords: 搜索关键词
        max_walking_minutes: 最大步行时长（分钟）
        bus_stop_radius: 公交站搜索半径（米），字符串格式
        bus_stop_keywords: 公交站搜索关键词
    
    Returns:
        bool: True表示所有验证通过，False表示部分或全部验证失败
    """
    all_passed = True
    
    # 验证步骤1: 获取POI详情，验证评分 >= 4.8
    print(f"验证步骤1: 获取POI详情并验证评分 >= {min_rating}")
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"验证步骤1失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print("验证步骤1失败: 未获取到POI坐标")
        return False
    
    # 获取评分
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
    
    target_poi_location = poi_detail.location
    
    # 验证步骤2: 验证POI在用户位置2.5公里内且为商场
    print(f"验证步骤2: 验证POI在用户位置{max_distance_meters}米内且为{keywords}")
    around_search_result = maps_around_search(
        location=user_location,
        radius=max_distance_meters,
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
            print(f"验证步骤2通过: 在{max_distance_meters}米内找到目标{keywords}POI")
        else:
            print(f"验证步骤2失败: 在{max_distance_meters}米内未找到目标{keywords}POI")
            all_passed = False
    
    # 验证步骤3: 验证步行时长 <= 25分钟
    print(f"验证步骤3: 验证步行时长 <= {max_walking_minutes}分钟")
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
        walking_minutes = walking_result.total_duration_seconds / 60.0
        if walking_minutes <= max_walking_minutes:
            print(f"验证步骤3通过: 步行时长 {walking_minutes:.1f}分钟 <= {max_walking_minutes}分钟")
        else:
            print(f"验证步骤3失败: 步行时长 {walking_minutes:.1f}分钟 > {max_walking_minutes}分钟")
            all_passed = False
    
    # 验证步骤4: 验证POI附近600米内有公交站
    print(f"验证步骤4: 验证POI附近{bus_stop_radius}米内有{bus_stop_keywords}")
    bus_stop_result = maps_around_search(
        location=target_poi_location,
        radius=bus_stop_radius,
        keywords=bus_stop_keywords
    )
    
    if bus_stop_result.error:
        print(f"验证步骤4失败: {bus_stop_result.error}")
        all_passed = False
    elif not bus_stop_result.pois or len(bus_stop_result.pois) == 0:
        print(f"验证步骤4失败: POI附近{bus_stop_radius}米内未找到{bus_stop_keywords}")
        all_passed = False
    else:
        print(f"验证步骤4通过: POI附近{bus_stop_radius}米内找到{len(bus_stop_result.pois)}个{bus_stop_keywords}")
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")
    return result  


if __name__ == "__main__":
    main()
