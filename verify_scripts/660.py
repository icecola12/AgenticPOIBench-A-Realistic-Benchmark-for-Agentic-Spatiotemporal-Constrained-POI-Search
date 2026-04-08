"""
输入：B02F002JNM
输出：True

验证方法：
1) 周边召回数量与“附近8公里内”验证：
- 调用 maps_around_search，参数：location=114.446606,23.121736，radius=8000，keywords=博物馆。
- 验证返回的pois数量>=8（用于保证任务有足够候选、可评测）。
- 验证 target_poi_id=B02F002JNM 出现在该pois列表中（从而证明其满足“附近8公里内”的硬约束）。

2) 评分验证：
- 对 target_poi_id 调用 maps_search_detail(id=B02F002JNM)。
- 从返回的 biz_ext.rating 读取评分，验证 rating >= 4.7。

3) 骑行时间验证（从出发地到目标博物馆）：
- 使用 maps_search_detail 返回的目标 location 作为 destination。
- 调用 maps_bicycling_by_coordinates(origin=114.446606,23.121736, destination=目标location)。
- 验证 total_duration_seconds <= 20*60。

4) 到惠州站的驾车时间验证（从目标博物馆到火车站）：
- 调用 maps_text_search(keywords="惠州站", city="惠州") 取 poi_id，再 maps_search_detail(id=poi_id) 获取惠州站坐标 station_loc。
- 调用 maps_driving_by_coordinates(origin=目标location, destination=station_loc)。
- 验证 total_duration_seconds <= 12*60。
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
    target_poi_id: str = "B02F002JNM",
    user_location: str = "114.446606,23.121736",
    search_radius: str = "8000",
    search_keywords: str = "博物馆",
    min_poi_count: int = 8,
    min_rating: float = 4.7,
    max_bicycling_seconds: int = 1200,
    station_address: str = "惠州站",
    station_city: str = "惠州",
    max_driving_seconds: int = 720
) -> bool:
    """
    验证POI是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID
        user_location: 用户位置坐标，格式为"经度,纬度"
        search_radius: 搜索半径（米）
        search_keywords: 搜索关键词
        min_poi_count: 最小POI数量要求
        min_rating: 最低评分要求
        max_bicycling_seconds: 最大骑行时间（秒）
        station_address: 火车站地址
        station_city: 火车站所在城市
        max_driving_seconds: 最大驾车时间（秒）
    
    Returns:
        bool: 所有验证条件都满足返回True，否则返回False
    """
    all_passed = True
    
    print("=" * 80)
    print(f"开始验证POI: {target_poi_id}")
    print("=" * 80)
    
    # 步骤1: 周边召回数量与"附近8公里内"验证
    print("\n【步骤1】周边召回数量与\"附近8公里内\"验证")
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
        poi_count = len(around_result.pois) if around_result.pois else 0
        poi_found = False
        
        # 验证POI数量>=8
        if poi_count >= min_poi_count:
            print(f"[PASS] 步骤1-数量验证通过: 找到 {poi_count} 个POI >= {min_poi_count}")
        else:
            print(f"[FAIL] 步骤1-数量验证失败: 找到 {poi_count} 个POI < {min_poi_count}")
            all_passed = False
        
        # 验证目标POI是否在列表中
        if around_result.pois:
            for poi in around_result.pois:
                if poi.id == target_poi_id:
                    poi_found = True
                    break
        
        if poi_found:
            print(f"[PASS] 步骤1-距离验证通过: POI {target_poi_id} 在附近{search_radius}米内找到")
        else:
            print(f"[FAIL] 步骤1-距离验证失败: POI {target_poi_id} 未在附近{search_radius}米内找到")
            all_passed = False
    
    # 步骤2: 评分验证
    print("\n【步骤2】评分验证(>=4.7)")
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
                        else:
                            print(f"[FAIL] 步骤2-评分验证失败: 评分 {rating_value} < {min_rating}")
                            all_passed = False
                    except (ValueError, TypeError):
                        print(f"[FAIL] 步骤2-评分验证失败: 评分格式错误 - {rating}")
                        all_passed = False
    
    # 步骤3: 骑行时间验证(<=20分钟)
    print("\n【步骤3】骑行时间验证(<=20分钟)")
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
    
    # 步骤4: 到惠州站的驾车时间验证(<=12分钟)
    print("\n【步骤4】到惠州站的驾车时间验证(<=12分钟)")
    print("-" * 80)
    if not poi_location:
        print(f"[FAIL] 步骤4失败: 无法获取POI坐标，跳过驾车时间验证")
        all_passed = False
    else:
        # 获取惠州站坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
        station_text_result = maps_text_search(keywords=station_address, city=station_city)
        if station_text_result.error:
            print(f"[FAIL] 步骤4失败: 无法获取{station_address}坐标 - {station_text_result.error}")
            all_passed = False
        elif not station_text_result.pois or len(station_text_result.pois) == 0:
            print(f"[FAIL] 步骤4失败: 未找到{station_address}的坐标")
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
                print(f"[OK] 获取到{station_address}坐标: {station_location}")
                
                # 计算驾车时间
                driving_result = maps_driving_by_coordinates(
                    origin=poi_location,
                    destination=station_location
                )
                
                if driving_result.error:
                    print(f"[FAIL] 步骤4失败: {driving_result.error}")
                    all_passed = False
                else:
                    if driving_result.total_duration_seconds is None:
                        print(f"[FAIL] 步骤4失败: 无法获取驾车时间")
                        all_passed = False
                    else:
                        duration = driving_result.total_duration_seconds
                        if duration <= max_driving_seconds:
                            print(f"[PASS] 步骤4通过: 驾车时间 {duration}秒 ({duration//60}分{duration%60}秒) <= {max_driving_seconds}秒 ({max_driving_seconds//60}分钟)")
                        else:
                            print(f"[FAIL] 步骤4失败: 驾车时间 {duration}秒 ({duration//60}分{duration%60}秒) > {max_driving_seconds}秒 ({max_driving_seconds//60}分钟)")
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
