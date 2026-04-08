"""
输入：B0L1HSXHRD
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边候选集验证：用 maps_around_search(location=105.302617,27.315021, radius=5000, keywords=便利店) 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 周边POI列表，验证 target_poi_id 在返回的pois中（满足“附近5公里内”且POI数量>=8便于筛选）。
2) POI类型与基础信息验证：对 target_poi_id 调用 maps_search_detail(id) 获取名称/地址/坐标与 biz_ext 信息，验证其为便利店类型（名称或类别语义为便利店）。
3) 驾车时长验证：用 maps_driving_by_coordinates(origin=105.302617,27.315021, destination=POI.location) 获取驾车用时，验证 total_duration_seconds <= 300（不超过5分钟）。
4) 骑行时长验证：用 maps_bicycling_by_coordinates(origin=105.302617,27.315021, destination=POI.location) 获取骑行用时，验证 total_duration_seconds <= 480（不超过8分钟）。
5) 营业时间验证：用 maps_search_detail(id) 中 biz_ext.opentime2 / biz_ext.open_time 判断是否为24小时营业；在给定 time 对应的当天时刻应处于营业区间内（若显示“24h/00:00-24:00/00:00-次日00:00”等则判定通过）。
6) 评分验证：用 maps_search_detail(id) 的 biz_ext.rating，验证 rating >= 3.0。
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
    target_poi_id: str = "B0L1HSXHRD",
    location: str = "105.302617,27.315021",
    radius: str = "5000",
    keywords: str = "便利店",
    max_driving_duration_seconds: int = 300,
    max_bicycling_duration_seconds: int = 480,
    min_rating: float = 3.0
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        location: 用户位置坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        max_driving_duration_seconds: 最大驾车时长（秒）
        max_bicycling_duration_seconds: 最大骑行时长（秒）
        min_rating: 最低评分
    
    Returns:
        bool: True表示所有验证都通过，False表示有验证未通过
    """
    all_passed = True
    
    # 验证1: 周边候选集验证
    print("=" * 50)
    print("验证1: 周边候选集验证")
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
    
    # 验证2: POI类型与基础信息验证
    print("=" * 50)
    print("验证2: POI类型与基础信息验证")
    detail_result = maps_search_detail(id=target_poi_id)
    
    if detail_result.error:
        print(f"❌ POI详情查询失败: {detail_result.error}")
        all_passed = False
        # 如果无法获取详情，后续验证也无法进行
        return False
    
    if not detail_result.name:
        print("❌ 未通过: 无法获取POI名称")
        all_passed = False
    else:
        # 检查名称或类别是否包含"便利店"
        name = detail_result.name
        is_convenience_store = "便利店" in name or "超市" in name or "商店" in name
        
        # 检查biz_ext中的类型信息
        if detail_result.biz_ext:
            biz_type = detail_result.biz_ext.get("type", "")
            if isinstance(biz_type, str):
                is_convenience_store = is_convenience_store or "便利店" in biz_type
        
        if is_convenience_store:
            print(f"✅ 通过: POI名称 '{name}' 符合便利店类型")
        else:
            print(f"❌ 未通过: POI名称 '{name}' 不符合便利店类型")
            all_passed = False
    
    # 获取POI坐标，用于后续验证
    if not detail_result.location:
        print("❌ 无法获取POI坐标，后续验证无法进行")
        return False
    
    poi_location = detail_result.location
    
    # 验证3: 驾车时长验证
    print("=" * 50)
    print("验证3: 驾车时长验证")
    print(f"起点: {location}, 终点: {poi_location}")
    driving_result = maps_driving_by_coordinates(origin=location, destination=poi_location)
    
    if driving_result.error:
        print(f"❌ 驾车路线规划失败: {driving_result.error}")
        all_passed = False
    else:
        duration = driving_result.total_duration_seconds
        if duration <= max_driving_duration_seconds:
            print(f"✅ 通过: 驾车时长 {duration}秒 ({duration/60:.1f}分钟) <= {max_driving_duration_seconds}秒 ({max_driving_duration_seconds/60:.1f}分钟)")
        else:
            print(f"❌ 未通过: 驾车时长 {duration}秒 ({duration/60:.1f}分钟) > {max_driving_duration_seconds}秒 ({max_driving_duration_seconds/60:.1f}分钟)")
            all_passed = False
    
    # 验证4: 骑行时长验证
    print("=" * 50)
    print("验证4: 骑行时长验证")
    print(f"起点: {location}, 终点: {poi_location}")
    bicycling_result = maps_bicycling_by_coordinates(origin=location, destination=poi_location)
    
    if bicycling_result.error:
        print(f"❌ 骑行路线规划失败: {bicycling_result.error}")
        all_passed = False
    else:
        duration = bicycling_result.total_duration_seconds
        if duration <= max_bicycling_duration_seconds:
            print(f"✅ 通过: 骑行时长 {duration}秒 ({duration/60:.1f}分钟) <= {max_bicycling_duration_seconds}秒 ({max_bicycling_duration_seconds/60:.1f}分钟)")
        else:
            print(f"❌ 未通过: 骑行时长 {duration}秒 ({duration/60:.1f}分钟) > {max_bicycling_duration_seconds}秒 ({max_bicycling_duration_seconds/60:.1f}分钟)")
            all_passed = False
    
    # 验证5: 营业时间验证
    print("=" * 50)
    print("验证5: 营业时间验证")
    if not detail_result.biz_ext:
        print("❌ 未通过: 无法获取营业时间信息（biz_ext为空）")
        all_passed = False
    else:
        biz_ext = detail_result.biz_ext
        opentime2 = biz_ext.get("opentime2", "")
        open_time = biz_ext.get("open_time", "")
        
        # 检查是否为24小时营业
        is_24h = False
        time_str = ""
        
        if opentime2:
            time_str = str(opentime2)
            # 检查各种24小时营业的表示方式
            is_24h = ("24h" in time_str.lower() or 
                     "00:00-24:00" in time_str or 
                     "00:00-次日00:00" in time_str or
                     "24小时" in time_str)
        elif open_time:
            time_str = str(open_time)
            is_24h = ("24h" in time_str.lower() or 
                     "00:00-24:00" in time_str or 
                     "00:00-次日00:00" in time_str or
                     "24小时" in time_str)
        
        if is_24h:
            print(f"✅ 通过: 营业时间为24小时营业 ({time_str})")
        else:
            print(f"❌ 未通过: 不是24小时营业 (营业时间: {time_str if time_str else '未提供'})")
            all_passed = False
    
    # 验证6: 评分验证
    print("=" * 50)
    print("验证6: 评分验证")
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
