"""
输入：B018900FIF
输出：True

验证方法：
1) 距离约束：调用 maps_around_search(location="115.065343,35.703976", radius="5000", keywords="加油站")，验证返回pois中包含目标poi_id=B018900FIF。
2) 评分约束：调用 maps_search_detail(id="B018900FIF")，读取biz_ext.rating，验证 rating >= 4.4。
3) 骑行时间约束：从 maps_search_detail 获取目标POI坐标destination=location；调用 maps_bicycling_by_coordinates(origin="115.065343,35.703976", destination=destination)，验证 total_duration_seconds <= 12*60。
4) 去高铁站驾车时间约束：调用 maps_text_search(keywords="濮阳东站", city="濮阳", citylimit="true") 获取濮阳东站poi_id=B0FFKGZUXJ；调用 maps_search_detail(id="B0FFKGZUXJ") 获取其location=station_loc；再调用 maps_driving_by_coordinates(origin=destination, destination=station_loc)，验证 total_duration_seconds <= 18*60。
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
    target_poi_id: str = 'B018900FIF',
    user_location: str = '115.065343,35.703976',
    radius: str = '5000',
    keywords: str = '加油站',
    min_rating: float = 4.4,
    max_bicycling_seconds: int = 720,
    station_keywords: str = '濮阳东站',
    station_city: str = '濮阳',
    station_citylimit: str = 'true',
    max_driving_seconds: int = 1080
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标，格式为"经度,纬度"
        radius: 搜索半径（米），字符串格式
        keywords: 搜索关键词
        min_rating: 最低评分要求
        max_bicycling_seconds: 最大骑行时长（秒）
        station_keywords: 车站搜索关键词
        station_city: 车站所在城市
        station_citylimit: 是否限制在城市范围内
        max_driving_seconds: 最大驾车时长（秒）
    
    Returns:
        bool: True表示所有验证通过，False表示部分或全部验证失败
    """
    all_passed = True
    
    # 验证步骤1: 距离约束
    print("验证步骤1: 距离约束 - 验证POI在用户位置周边搜索范围内")
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
    
    # 验证步骤2: 评分约束
    print(f"验证步骤2: 评分约束 - 验证评分 >= {min_rating}")
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"验证步骤2失败: {poi_detail.error}")
        all_passed = False
    elif not poi_detail.location:
        print("验证步骤2失败: 未获取到POI坐标")
        all_passed = False
    else:
        target_poi_location = poi_detail.location
        print(f"验证步骤2: 成功获取POI坐标 {target_poi_location}")
        
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
            print("验证步骤2失败: 未获取到POI评分")
            all_passed = False
        elif rating >= min_rating:
            print(f"验证步骤2通过: 评分 {rating} >= {min_rating}")
        else:
            print(f"验证步骤2失败: 评分 {rating} < {min_rating}")
            all_passed = False
    
    # 验证步骤3: 骑行时间约束
    print(f"验证步骤3: 骑行时间约束 - 验证骑行时长 <= {max_bicycling_seconds}秒（{max_bicycling_seconds // 60}分钟）")
    
    if not poi_detail.location:
        print("验证步骤3失败: 未获取到POI坐标")
        all_passed = False
    else:
        target_poi_location = poi_detail.location
        
        bicycling_result = maps_bicycling_by_coordinates(
            origin=user_location,
            destination=target_poi_location
        )
        
        if bicycling_result.error:
            print(f"验证步骤3失败: {bicycling_result.error}")
            all_passed = False
        elif bicycling_result.total_duration_seconds is None:
            print("验证步骤3失败: 未获取到骑行时长")
            all_passed = False
        else:
            bicycling_seconds = bicycling_result.total_duration_seconds
            if bicycling_seconds <= max_bicycling_seconds:
                print(f"验证步骤3通过: 骑行时长 {bicycling_seconds}秒 <= {max_bicycling_seconds}秒（{max_bicycling_seconds // 60}分钟）")
            else:
                print(f"验证步骤3失败: 骑行时长 {bicycling_seconds}秒 > {max_bicycling_seconds}秒（{max_bicycling_seconds // 60}分钟）")
                all_passed = False
    
    # 验证步骤4: 去高铁站驾车时间约束
    print(f"验证步骤4: 去高铁站驾车时间约束 - 验证驾车时长 <= {max_driving_seconds}秒（{max_driving_seconds // 60}分钟）")
    
    if not poi_detail.location:
        print("验证步骤4失败: 未获取到POI坐标")
        all_passed = False
    else:
        target_poi_location = poi_detail.location
        
        # 搜索高铁站
        station_search_result = maps_text_search(
            keywords=station_keywords,
            city=station_city,
            citylimit=station_citylimit
        )
        
        if station_search_result.error:
            print(f"验证步骤4失败: 搜索车站出错 - {station_search_result.error}")
            all_passed = False
        elif not station_search_result.pois or len(station_search_result.pois) == 0:
            print(f"验证步骤4失败: 未找到{station_keywords}")
            all_passed = False
        else:
            # 使用搜索结果中的第一个POI
            station_poi_id = station_search_result.pois[0].id
            print(f"验证步骤4: 找到车站POI ID: {station_poi_id}")
            
            # 获取车站坐标
            station_detail = maps_search_detail(id=station_poi_id)
            
            if station_detail.error:
                print(f"验证步骤4失败: 获取车站详情出错 - {station_detail.error}")
                all_passed = False
            elif not station_detail.location:
                print("验证步骤4失败: 无法获取车站坐标")
                all_passed = False
            else:
                station_location = station_detail.location
                print(f"验证步骤4: 获取到车站坐标: {station_location}")
                
                # 计算驾车时长
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
