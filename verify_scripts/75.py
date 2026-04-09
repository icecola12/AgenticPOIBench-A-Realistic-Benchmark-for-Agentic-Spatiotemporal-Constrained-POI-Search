"""
输入：B0FFG7ILFL
输出：True

验证方法：
1) 距离约束（附近2公里内）：调用 maps_around_search(location='100.471648,38.942852', radius='2000', keywords='便利店')，验证返回pois中包含目标poi_id=B0FFG7ILFL。
2) 步行路程不超过900米：调用 maps_search_detail('B0FFG7ILFL') 获取目标location='100.463800,38.946232'；再调用 maps_walking_by_coordinates(origin='100.471648,38.942852', destination='100.463800,38.946232')，验证 total_distance_meters<=900（实测811米）。
3) 到张掖西站驾车时间不超过8分钟：调用 maps_search_detail('B0FFFAGTHK') 获取张掖西站location='100.428341,38.923036'；再调用 maps_driving_by_coordinates(origin='100.463800,38.946232', destination='100.428341,38.923036')，验证 total_duration_seconds<=480（实测431秒）。
4) 评分不低于3.5分：调用 maps_search_detail('B0FFG7ILFL')，在 biz_ext.rating 中验证 rating>=3.5（实测3.6）。
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
    target_poi_id: str = "B0FFG7ILFL",
    location: str = "100.471648,38.942852",
    radius: str = "2000",
    keywords: str = "便利店",
    max_walking_distance_meters: int = 900,
    station_poi_id: str = "B0FFFAGTHK",
    max_driving_duration_seconds: int = 480,
    min_rating: float = 3.5
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        location: 用户位置坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        max_walking_distance_meters: 最大步行距离（米）
        station_poi_id: 车站POI ID（张掖西站）
        max_driving_duration_seconds: 最大驾车时长（秒）
        min_rating: 最低评分
    
    Returns:
        bool: True表示所有验证都通过，False表示有验证未通过
    """
    all_passed = True
    
    # 验证1: 距离约束（附近2公里内）
    print("=" * 50)
    print("验证1: 距离约束（附近2公里内）")
    print(f"搜索位置: {location}, 半径: {radius}米, 关键词: {keywords}")
    around_result = maps_around_search(location=location, radius=radius, keywords=keywords)
    
    if around_result.error:
        print(f"❌ 周边搜索失败: {around_result.error}")
        all_passed = False
    elif not around_result.pois:
        print("❌ 周边搜索未找到POI")
        all_passed = False
    else:
        poi_ids = [poi.id for poi in around_result.pois]
        if target_poi_id in poi_ids:
            print(f"✅ 通过: target_poi_id {target_poi_id} 在周边POI列表中（共{len(poi_ids)}个POI）")
        else:
            print(f"❌ 未通过: target_poi_id {target_poi_id} 不在周边POI列表中")
            all_passed = False
    
    # 验证2: 步行路程不超过900米
    print("=" * 50)
    print("验证2: 步行路程不超过900米")
    detail_result = maps_search_detail(id=target_poi_id)
    
    if detail_result.error:
        print(f"❌ POI详情查询失败: {detail_result.error}")
        all_passed = False
        # 如果无法获取详情，后续验证也无法进行
        return False
    
    if not detail_result.location:
        print("❌ 无法获取POI坐标，后续验证无法进行")
        return False
    
    poi_location = detail_result.location
    print(f"起点: {location}, 终点: {poi_location}")
    walking_result = maps_walking_by_coordinates(origin=location, destination=poi_location)
    
    if walking_result.error:
        print(f"❌ 步行路线规划失败: {walking_result.error}")
        all_passed = False
    else:
        distance = walking_result.total_distance_meters
        if distance is not None and distance <= max_walking_distance_meters:
            print(f"✅ 通过: 步行距离 {distance}米 <= {max_walking_distance_meters}米")
        else:
            print(f"❌ 未通过: 步行距离 {distance}米 > {max_walking_distance_meters}米")
            all_passed = False
    
    # 验证3: 到张掖西站驾车时间不超过8分钟
    print("=" * 50)
    print("验证3: 到张掖西站驾车时间不超过8分钟")
    station_detail_result = maps_search_detail(id=station_poi_id)
    
    if station_detail_result.error:
        print(f"❌ 车站POI详情查询失败: {station_detail_result.error}")
        all_passed = False
    elif not station_detail_result.location:
        print("❌ 无法获取车站POI坐标，验证无法进行")
        all_passed = False
    else:
        station_location = station_detail_result.location
        print(f"起点: {poi_location}, 终点: {station_location}")
        driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
        
        if driving_result.error:
            print(f"❌ 驾车路线规划失败: {driving_result.error}")
            all_passed = False
        else:
            duration = driving_result.total_duration_seconds
            if duration is not None and duration <= max_driving_duration_seconds:
                print(f"✅ 通过: 驾车时长 {duration}秒 ({duration/60:.1f}分钟) <= {max_driving_duration_seconds}秒 ({max_driving_duration_seconds/60:.1f}分钟)")
            else:
                print(f"❌ 未通过: 驾车时长 {duration}秒 ({duration/60:.1f}分钟) > {max_driving_duration_seconds}秒 ({max_driving_duration_seconds/60:.1f}分钟)")
                all_passed = False
    
    # 验证4: 评分不低于3.5分
    print("=" * 50)
    print("验证4: 评分不低于3.5分")
    if not detail_result.biz_ext:
        print("❌ 未通过: 无法获取评分信息（biz_ext为空）")
        all_passed = False
    else:
        biz_ext = detail_result.biz_ext
        rating = biz_ext.get("rating")
        
        if rating is None:
            print("❌ 未通过: 无法获取评分信息（rating为空）")
            all_passed = False
        else:
            try:
                rating_float = float(rating)
                if rating_float >= min_rating:
                    print(f"✅ 通过: 评分 {rating_float} >= {min_rating}")
                else:
                    print(f"❌ 未通过: 评分 {rating_float} < {min_rating}")
                    all_passed = False
            except (ValueError, TypeError):
                print(f"❌ 未通过: 评分格式错误 ({rating})")
                all_passed = False
    
    # 最终结果
    print("=" * 50)
    if all_passed:
        print("✅ 所有验证通过！")
    else:
        print("❌ 部分验证未通过")
    print("=" * 50)
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {result}")  


if __name__ == "__main__":
    main()
